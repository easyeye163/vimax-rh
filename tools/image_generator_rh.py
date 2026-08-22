import logging
import os
import asyncio
import aiohttp
from typing import List, Optional
from interfaces.image_output import ImageOutput
from utils.rate_limiter import RateLimiter
from utils.retry import after_func
from tenacity import retry, stop_after_attempt


RUNNINGHUB_BASE_URL = "https://www.runninghub.cn/openapi/v2"


class ImageGeneratorRunningHub:
    """RunningHub ComfyUI workflow image generator.

    Supports:
    - Text-to-Image (t2i): pure prompt → image
    - Image-to-Image (i2i): prompt + reference image → image

    RunningHub API:
    - Upload: POST /media/upload/binary  (form field: file)
    - Submit: POST /run/ai-app/{app_id}
    - Query:  POST /query  {"taskId": "..."}
    """

    def __init__(
        self,
        api_key: str = "",
        t2i_app_id: str = "2088920592350277634",
        i2i_app_id: str = "2088926295186034689",
        t2i_prompt_node_id: str = "17",
        t2i_prompt_field_name: str = "prompt",
        i2i_prompt_node_id: str = "160",
        i2i_prompt_field_name: str = "text",
        i2i_image_node_id: str = "104",
        i2i_image_field_name: str = "image",
        poll_interval: int = 10,
        poll_timeout: int = 300,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.api_key = api_key or os.getenv("RUNNINGHUB_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "RunningHub API key is required. "
                "Set it via init_args.api_key or RUNNINGHUB_API_KEY env var."
            )

        self.t2i_app_id = t2i_app_id
        self.i2i_app_id = i2i_app_id

        self.t2i_prompt_node_id = t2i_prompt_node_id
        self.t2i_prompt_field_name = t2i_prompt_field_name
        self.i2i_prompt_node_id = i2i_prompt_node_id
        self.i2i_prompt_field_name = i2i_prompt_field_name
        self.i2i_image_node_id = i2i_image_node_id
        self.i2i_image_field_name = i2i_image_field_name

        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout
        self.rate_limiter = rate_limiter

    # ------------------------------------------------------------------
    # RunningHub API helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
        }

    async def _upload_image(self, image_path: str) -> str:
        """Upload a local image to RunningHub and return the fileName."""
        url = f"{RUNNINGHUB_BASE_URL}/media/upload/binary"
        with open(image_path, "rb") as f:
            data = aiohttp.FormData()
            data.add_field("file", f, filename=os.path.basename(image_path))

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers(), data=data, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    file_name = result["data"]["fileName"]
                    logging.info(f"Uploaded image to RunningHub: {file_name}")
                    return file_name

    async def _submit_task(self, app_id: str, node_info_list: list) -> str:
        """Submit a ComfyUI workflow task and return the taskId."""
        url = f"{RUNNINGHUB_BASE_URL}/run/ai-app/{app_id}"
        payload = {
            "nodeInfoList": node_info_list,
            "instanceType": "default",
            "usePersonalQueue": "false",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                resp.raise_for_status()
                result = await resp.json()
                task_id = result["data"]["taskId"]
                logging.info(f"RunningHub task submitted: {task_id} (app={app_id})")
                return task_id

    async def _poll_task(self, task_id: str) -> dict:
        """Poll until the task finishes. Returns the full result dict."""
        url = f"{RUNNINGHUB_BASE_URL}/query"
        payload = {"taskId": task_id}
        elapsed = 0.0

        async with aiohttp.ClientSession() as session:
            while elapsed < self.poll_timeout:
                async with session.post(
                    url,
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    resp.raise_for_status()
                    result = await resp.json()

                status = result["data"]["status"]
                if status == "SUCCESS":
                    logging.info(f"Task {task_id} completed successfully.")
                    return result
                elif status == "FAILED":
                    reason = result["data"].get("failedReason", "unknown")
                    raise RuntimeError(f"RunningHub task {task_id} failed: {reason}")
                else:
                    logging.debug(f"Task {task_id} status: {status} (elapsed {elapsed:.0f}s)")

                await asyncio.sleep(self.poll_interval)
                elapsed += self.poll_interval

        raise TimeoutError(f"RunningHub task {task_id} did not complete within {self.poll_timeout}s")

    # ------------------------------------------------------------------
    # Public API (matches ImageGenerator protocol)
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        **kwargs,
    ) -> ImageOutput:
        """Generate an image via RunningHub.

        - If no reference_image_paths → use text-to-image workflow
        - If reference_image_paths provided → use image-to-image workflow
        """
        if self.rate_limiter:
            await self.rate_limiter.acquire()

        if not reference_image_paths:
            return await self._generate_t2i(prompt)
        else:
            return await self._generate_i2i(prompt, reference_image_paths)

    async def _generate_t2i(self, prompt: str) -> ImageOutput:
        """Text-to-image generation."""
        logging.info(f"[RH T2I] Generating image with prompt: {prompt[:100]}...")

        node_info_list = [
            {
                "nodeId": self.t2i_prompt_node_id,
                "fieldName": self.t2i_prompt_field_name,
                "fieldValue": prompt,
            },
        ]

        task_id = await self._submit_task(self.t2i_app_id, node_info_list)
        result = await self._poll_task(task_id)

        # Extract output URL from results
        output_url = result["data"]["results"][0]["url"]
        logging.info(f"[RH T2I] Image generated: {output_url}")

        return ImageOutput(fmt="url", ext="png", data=output_url)

    async def _generate_i2i(self, prompt: str, reference_image_paths: List[str]) -> ImageOutput:
        """Image-to-image generation (use first reference image)."""
        logging.info(f"[RH I2I] Generating image with prompt: {prompt[:100]}...")

        # Upload the reference image
        ref_file_name = await self._upload_image(reference_image_paths[0])

        node_info_list = [
            {
                "nodeId": self.i2i_image_node_id,
                "fieldName": self.i2i_image_field_name,
                "fieldValue": ref_file_name,
            },
            {
                "nodeId": self.i2i_prompt_node_id,
                "fieldName": self.i2i_prompt_field_name,
                "fieldValue": prompt,
            },
        ]

        task_id = await self._submit_task(self.i2i_app_id, node_info_list)
        result = await self._poll_task(task_id)

        output_url = result["data"]["results"][0]["url"]
        logging.info(f"[RH I2I] Image generated: {output_url}")

        return ImageOutput(fmt="url", ext="png", data=output_url)
