import logging
from typing import List, Tuple
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chat_models.base import BaseChatModel
from utils.image import image_path_to_b64
from utils.retry import after_func

system_prompt_template_select_most_consistent_image = \
"""
[Role]
You are a professional visual assessment expert.

[Task]
Based on the reference images, the text description of the target image, and candidate images, evaluate which candidate image performs best in:
- Character Consistency: Whether character features align with the reference.
- Spatial Consistency: Whether relative positions are consistent.
- Description Accuracy: Whether the candidate reflects the text description.

[Input]
- Reference images with descriptions.
- Candidate images to evaluate.
- Text description for target image enclosed in <target_description> and </target_description>.

[Output]
{format_instructions}

[Guidelines]
- Prioritize Character Consistency.
- Focus on Spatial Consistency.
- Strictly Compare with Text Description.
- If none are ideal, choose the relatively best option.
- Ensure key elements from the text are present.
- Prioritize images without artifacts or framing issues.
"""

human_prompt_template_select_most_consistent_image = \
"""
<target_description>
{target_description}
</target_description>
"""

class BestImageResponse(BaseModel):
    best_image_index: int = Field(
        ...,
        description="The index of the best image."
    )
    reason: str = Field(
        ...,
        description="The reason why the image is the best."
    )

class BestImageSelector:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def __call__(
        self,
        reference_image_path_and_text_pairs: List[Tuple[str, str]],
        target_description: str,
        candidate_image_paths: List[str],
    ) -> str:
        if not candidate_image_paths:
            raise ValueError("No candidate images to select from")

        logging.info(f"Selecting the best image from {len(candidate_image_paths)} candidates")

        human_content = []
        for idx, (ref_image_path, text) in enumerate(reference_image_path_and_text_pairs):
            human_content.append({"type": "text", "text": f"Reference Image {idx}: {text}"})
            human_content.append({"type": "image_url", "image_url": {"url": image_path_to_b64(ref_image_path, mime=True)}})

        for idx, candidate_image_path in enumerate(candidate_image_paths):
            human_content.append({"type": "text", "text": f"Candidate Image {idx}"})
            human_content.append({"type": "image_url", "image_url": {"url": image_path_to_b64(candidate_image_path, mime=True)}})
        human_content.append({"type": "text", "text": human_prompt_template_select_most_consistent_image.format(target_description=target_description)})

        parser = PydanticOutputParser(pydantic_object=BestImageResponse)

        messages = [
            SystemMessage(content=system_prompt_template_select_most_consistent_image.format(format_instructions=parser.get_format_instructions())),
            HumanMessage(content=human_content)
        ]

        chain = self.chat_model | parser
        response = await chain.ainvoke(messages)
        idx = response.best_image_index
        if not isinstance(idx, int) or idx < 0 or idx >= len(candidate_image_paths):
            logging.warning(f"Received invalid best_image_index={idx}; defaulting to 0")
            idx = 0
        best_image_path = candidate_image_paths[idx]
        logging.info(f"Best image selected: {best_image_path} (reason: {response.reason})")
        return best_image_path
