import logging
import os
import asyncio
import aiohttp
from typing import List, Optional
from interfaces.video_output import VideoOutput
from utils.rate_limiter import RateLimiter
from utils.retry import after_func
from tenacity import retry, stop_after_attempt


RUNNINGHUB_BASE_URL = "https://www.runninghub.cn/openapi/v2"


class VideoGeneratorRunningHub:
    """RunningHub ComfyUI workflow video generator.

    Uses the AnimateDiff + MiniMax H3 image-to-video workflow.

    RunningHub API:
    - Upload: POST /media/upload/binary  (form field: file)
    - Submit: POST /run/ai-app/{app_id}
    - Query:  POST /query  {"taskId": "..."}
    """

    def __init__(
        self,
        api_key: str = "",
        i2v_app_id: str = "2088844222551121921",
        prompt_node_id: str = "138",
        prompt_field_name: str = "value",
        image_node_id: str = "137",
        image_field_name: str = "image",
        poll_interval: int = 15,
        poll_timeout: int = 600,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.api_key = api_key or os.getenv("RUNNINGHUB_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "RunningHub API key is required. "
                "Set it via init_args.api_key or RUNNINGHUB_API_KEY env var."
            )

        self.i2v_app_id = i2v_app_id
        self.prompt_node_id = prompt_node_id
        self.prompt_field_name = prompt_field_name
        self.image_node_id = image_node_id
        self.image_field_name = image_field_name

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
                logging.info(f"RunningHub video task submitted: {task_id} (app={app_id})")
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
                    logging.info(f"Video task {task_id} completed successfully.")
                    return result
                elif status == "FAILED":
                    reason = result["data"].get("failedReason", "unknown")
                    traceback_info = ""
                    if isinstance(reason, dict) and "traceback" in reason:
                        traceback_info = reason["traceback"]
                    raise RuntimeError(
                        f"RunningHub video task {task_id} failed: {reason} {traceback_info}"
                    )
                else:
                    logging.debug(f"Video task {task_id} status: {status} (elapsed {elapsed:.0f}s)")

                await asyncio.sleep(self.poll_interval)
                elapsed += self.poll_interval

        raise TimeoutError(f"RunningHub video task {task_id} did not complete within {self.poll_timeout}s")

    # ------------------------------------------------------------------
    # Prompt construction for MiniMax H3 engine
    # ------------------------------------------------------------------

    def _build_prompt(self, prompt: str) -> str:
        """Build a 6-segment Full-Reference prompt for the MiniMax H3 engine.

        When the caller provides a raw visual/motion description, we wrap
        it into the structured format that the AnimateDiff + MiniMax H3
        workflow expects.
        """
        # If the caller already uses subject_definitions format, pass through
        if "subject_definitions:" in prompt or "<Subject" in prompt:
            return prompt

        # Otherwise wrap in simplified 6-segment format
        structured = f"""subject_definitions:
<Subject 1> is the main subject described in the scene.

summary:
[reference generation] {prompt}

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - appearance and motion from reference.

summarized_description:
The target video faithfully follows the visual description. {prompt}

overall_soundscape:
Ambient sounds matching the scene atmosphere.

non_diegetic_music:
Background music appropriate to the scene mood.
"""
        return structured

    # ------------------------------------------------------------------
    # Public API (matches VideoGenerator protocol)
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: List[str],
        **kwargs,
    ) -> VideoOutput:
        """Generate a video via RunningHub image-to-video workflow.

        Requires at least one reference image (first frame).
        """
        if self.rate_limiter:
            await self.rate_limiter.acquire()

        if not reference_image_paths:
            raise ValueError(
                "RunningHub video generator requires at least one reference image "
                "(first frame). Provide reference_image_paths."
            )

        logging.info(f"[RH I2V] Generating video with prompt: {prompt[:100]}...")

        # Upload the first frame reference image
        ref_file_name = await self._upload_image(reference_image_paths[0])

        # Build structured prompt for MiniMax H3
        rh_prompt = self._build_prompt(prompt)

        node_info_list = [
            {
                "nodeId": self.image_node_id,
                "fieldName": self.image_field_name,
                "fieldValue": ref_file_name,
            },
            {
                "nodeId": self.prompt_node_id,
                "fieldName": self.prompt_field_name,
                "fieldValue": rh_prompt,
            },
        ]

        task_id = await self._submit_task(self.i2v_app_id, node_info_list)
        result = await self._poll_task(task_id)

        # Extract output URL from results
        output_url = result["data"]["results"][0]["url"]
        logging.info(f"[RH I2V] Video generated: {output_url}")

        return VideoOutput(fmt="url", ext="mp4", data=output_url)
