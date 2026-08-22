import logging
from typing import List, Tuple
from tenacity import retry, stop_after_attempt
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chat_models.base import BaseChatModel
from utils.image import image_path_to_b64
from utils.retry import after_func

system_prompt_template_select_reference_images_only_text = \
"""
[Role]
You are a professional visual creation assistant skilled in multimodal image analysis.

[Task]
Select the most suitable reference images from a provided set of reference image descriptions based on the user's text description of the target frame.

[Input]
- Text description enclosed in <frame_description> and </frame_description>.
- Reference image descriptions sequence, each prefixed with its index.

[Output]
{format_instructions}

[Guidelines]
- Language of all output values should match the frame description language.
- Prioritize images with similar compositions.
- Give higher priority to more recent images.
- Avoid duplicate information.
- For character portraits, select at most one image from multiple views.
- Select at most **8** optimal reference images.
"""

system_prompt_template_select_reference_images_multimodal = \
"""
[Role]
You are a professional visual creation assistant skilled in multimodal image analysis.

[Task]
Select the most suitable reference images from a provided reference image library based on the user's text description.

[Input]
- Text description enclosed in <frame_description> and </frame_description>.
- Reference images with descriptions, indexed from 0.

[Output]
{format_instructions}

[Guidelines]
- Language of all output values should match the frame description language.
- Prioritize images with similar compositions.
- Give higher priority to more recent images.
- Avoid duplicate information.
- For character portraits, select at most one image from multiple views.
- Select at most **8** optimal reference images.
- The text guiding image editing should be as concise as possible.
"""

human_prompt_template_select_reference_images = \
"""
<frame_description>
{frame_description}
</frame_description>
"""

class RefImageIndicesAndTextPrompt(BaseModel):
    ref_image_indices: List[int] = Field(
        description="Indices of selected reference images (0-based).",
        examples=[[0, 2, 5]]
    )
    text_prompt: str = Field(
        description="Text description to guide image generation. Refer to reference images as 'Image N'.",
        examples=["Create an image based on the description. The man should reference Image 0. The landscape should reference Image 1."]
    )

class ReferenceImageSelector:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def select_reference_images_and_generate_prompt(
        self,
        available_image_path_and_text_pairs: List[Tuple[str, str]],
        frame_description: str,
    ):
        filtered_pairs = available_image_path_and_text_pairs

        # 1. Filter images using text-only model if >= 8
        if len(available_image_path_and_text_pairs) >= 8:
            human_content = []
            for idx, (_, text) in enumerate(available_image_path_and_text_pairs):
                human_content.append({"type": "text", "text": f"Image {idx}: {text}"})
            human_content.append({"type": "text", "text": human_prompt_template_select_reference_images.format(frame_description=frame_description)})

            parser = PydanticOutputParser(pydantic_object=RefImageIndicesAndTextPrompt)
            messages = [
                SystemMessage(content=system_prompt_template_select_reference_images_only_text.format(format_instructions=parser.get_format_instructions())),
                HumanMessage(content=human_content)
            ]

            chain = self.chat_model | parser
            try:
                ref = await chain.ainvoke(messages)
                filtered_pairs = [available_image_path_and_text_pairs[i] for i in ref.ref_image_indices]
                logging.info(f"Filtered image idx: {ref.ref_image_indices}")
            except Exception as e:
                logging.error(f"Error in text-only filtering: {e}")
                raise e

        # 2. Filter with multimodal model
        human_content = []
        for idx, (image_path, text) in enumerate(filtered_pairs):
            human_content.append({"type": "text", "text": f"Image {idx}: {text}"})
            human_content.append({"type": "image_url", "image_url": {"url": image_path_to_b64(image_path)}})
        human_content.append({"type": "text", "text": human_prompt_template_select_reference_images.format(frame_description=frame_description)})

        parser = PydanticOutputParser(pydantic_object=RefImageIndicesAndTextPrompt)
        messages = [
            SystemMessage(content=system_prompt_template_select_reference_images_multimodal.format(format_instructions=parser.get_format_instructions())),
            HumanMessage(content=human_content)
        ]

        chain = self.chat_model | parser
        try:
            response = await chain.ainvoke(messages)
            selected_pairs = [filtered_pairs[i] for i in response.ref_image_indices]
            return {
                "reference_image_path_and_text_pairs": selected_pairs,
                "text_prompt": response.text_prompt,
            }
        except Exception as e:
            logging.error(f"Error in multimodal filtering: {e}")
            raise e
