from typing import List, Optional, Literal, Tuple
import asyncio
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt

from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from interfaces import CharacterInScene, ShotDescription, ShotBriefDescription, ImageOutput

from utils.retry import after_func

system_prompt_template_design_storyboard = \
"""
[Role]
You are a professional storyboard artist with the following core skills:
- Script Analysis: Ability to quickly interpret a script's text.
- Visualization: Expertise in translating written descriptions into visual frames.
- Storyboarding: Proficiency in cinematic language (shot types, camera angles, movements, transitions).
- Narrative Continuity: Ability to ensure the storyboard sequence is logically smooth.
- Technical Knowledge: Understanding of storyboard formats and industry standards.

[Task]
Your task is to design a complete storyboard based on a user-provided script (which contains only one scene).

[Input]
- Script: A complete scene script enclosed within <script> and </script>.
- Characters List: A list describing basic information for each character, enclosed within <characters> and </characters>.
- User requirement: Optional, enclosed within <user_requirement> and </user_requirement>.

[Output]
{format_instructions}

[Guidelines]
- Ensure all output values (except keys) match the language used in the script.
- Each shot must have a clear narrative purpose.
- Use cinematic language deliberately.
- When designing a new shot, first consider whether it can be filmed using an existing camera position.
- Keep character names in visual descriptions and speaker fields consistent with the character list.
- When describing visual elements, indicate the position of elements within the frame.
- Avoid unsafe content in visual descriptions.
- Assign at most one dialogue line per character per shot.
- Each shot requires an independent description without reference to each other.
- When the shot focuses on a character, describe which specific body part the focus is on.
- When describing a character, indicate the direction they are facing.
"""

human_prompt_template_design_storyboard = \
"""
<script>
{script_str}
</script>

<characters>
{characters_str}
</characters>

<user_requirement>
{user_requirement_str}
</user_requirement>
"""

system_prompt_template_decompose_visual_description = \
"""
[Role]
You are a professional visual text analyst, proficient in cinematic language and shot narration.

[Task]
Your task is to dissect a visual text description of a shot into three core components:
- First Frame Description: Describe the static image at the beginning of the shot.
- Last Frame Description: Describe the static image at the end of the shot.
- Motion Description: Describe all movements between the first and last frame.

[Input]
- The description is enclosed within <visual_desc> and </visual_desc>.
- The character list is enclosed within <characters> and </characters>.

[Output]
{format_instructions}

[Guidelines]
- Ensure all output values (except keys) match the language used in the script.
- Ensure the first and last frame descriptions are pure "snapshots," containing no ongoing actions.
- In the motion description, clearly distinguish between camera movement and on-screen movement.
- The last frame description must be logically consistent with the first frame description and the motion description.
- Use accurate, concise, and professional descriptive language.
- Similar to the input visual description, the first and last frame descriptions should include details such as shot type, angle, composition.
- 'large' cases involve exaggerated transition shots with significant change.
- 'medium' cases involve introduction of new characters or character turns.
- 'small' cases involve minor changes like expression changes, pose changes.
- When describing a character, indicate the direction they are facing.
- The first shot must establish the overall scene environment.
- Use as few camera positions as possible.
"""

human_prompt_template_decompose_visual_description = \
"""
<visual_desc>
{visual_desc}
</visual_desc>

<characters>
{characters_str}
</characters>
"""

class VisDescDecompositionResponse(BaseModel):
    ff_desc: str = Field(
        description="A detailed description of the first frame of the shot."
    )
    ff_vis_char_idxs: List[int] = Field(
        description="Indices of visible characters in the first frame.",
        examples=[[0], [1], [0, 1], []]
    )
    lf_desc: str = Field(
        description="A detailed description of the last frame of the shot."
    )
    lf_vis_char_idxs: List[int] = Field(
        description="Indices of visible characters in the last frame.",
        examples=[[0], [1], [0, 1], []]
    )
    motion_desc: str = Field(
        description="The motion description of the shot."
    )
    variation_type: Literal["large", "medium", "small"] = Field(
        description="Degree of change between first and last frame."
    )
    variation_reason: str = Field(
        description="The reason for the variation type."
    )

class StoryboardArtist:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def design_storyboard(
        self,
        script: str,
        characters: List[CharacterInScene],
        user_requirement: Optional[str] = None,
        retry_timeout: int = 150,
    ) -> List[ShotBriefDescription]:
        class StoryboardResponse(BaseModel):
            storyboard: List[ShotBriefDescription] = Field(
                description="A complete storyboard of the scene."
            )

        script_str = script.strip()
        characters_str = "\n".join([f"Character {index}: {char}" for index, char in enumerate(characters)])
        user_requirement_str = user_requirement.strip() if user_requirement else ""

        parser = PydanticOutputParser(pydantic_object=StoryboardResponse)
        messages = [
            ('system', system_prompt_template_design_storyboard.format(format_instructions=parser.get_format_instructions())),
            ('human', human_prompt_template_design_storyboard.format(script_str=script_str, characters_str=characters_str, user_requirement_str=user_requirement_str)),
        ]
        chain = self.chat_model | parser
        response: StoryboardResponse = await asyncio.wait_for(
            chain.ainvoke(messages),
            timeout=retry_timeout,
        )
        return response.storyboard

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def decompose_visual_description(
        self,
        shot_brief_desc: ShotBriefDescription,
        characters: List[CharacterInScene],
        retry_timeout: int = 150,
    ) -> ShotDescription:
        parser = PydanticOutputParser(pydantic_object=VisDescDecompositionResponse)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ('system', system_prompt_template_decompose_visual_description),
                ('human', human_prompt_template_decompose_visual_description),
            ]
        )
        chain = prompt_template | self.chat_model | parser

        visual_desc = shot_brief_desc.visual_desc.strip()
        characters_str = "\n".join([
            f"{char.identifier_in_scene}: (static) {char.static_features}; (dynamic) {char.dynamic_features}"
            for char in characters
        ])

        decomposition: VisDescDecompositionResponse = await asyncio.wait_for(
            chain.ainvoke(
                input={
                    "format_instructions": parser.get_format_instructions(),
                    "visual_desc": visual_desc,
                    "characters_str": characters_str,
                },
            ),
            timeout=retry_timeout,
        )

        return ShotDescription(
            idx=shot_brief_desc.idx,
            is_last=shot_brief_desc.is_last,
            cam_idx=shot_brief_desc.cam_idx,
            visual_desc=shot_brief_desc.visual_desc,
            variation_type=decomposition.variation_type,
            variation_reason=decomposition.variation_reason,
            ff_desc=decomposition.ff_desc,
            ff_vis_char_idxs=decomposition.ff_vis_char_idxs,
            lf_desc=decomposition.lf_desc,
            lf_vis_char_idxs=decomposition.lf_vis_char_idxs,
            motion_desc=decomposition.motion_desc,
            audio_desc=shot_brief_desc.audio_desc,
        )


class CharacterPortraitsGenerator:
    """Generates character portrait images (front, side, back views)."""

    def __init__(self, image_generator):
        self.image_generator = image_generator

    async def generate_front_portrait(self, character: CharacterInScene, style: str) -> ImageOutput:
        """Generate a front-view portrait of the character."""
        prompt = (
            f"A front-view portrait of {character.identifier_in_scene}. "
            f"{character.static_features}. {character.dynamic_features}. "
            f"Style: {style}. Clean background, studio lighting."
        )
        return await self.image_generator.generate_single_image(
            prompt=prompt,
            reference_image_paths=[],
        )

    async def generate_side_portrait(self, character: CharacterInScene, front_portrait_path: str) -> ImageOutput:
        """Generate a side-view portrait using the front portrait as reference."""
        prompt = (
            f"A side-view portrait of {character.identifier_in_scene}. "
            f"{character.static_features}. {character.dynamic_features}. "
            f"Same character as the reference image but viewed from the side. Clean background."
        )
        return await self.image_generator.generate_single_image(
            prompt=prompt,
            reference_image_paths=[front_portrait_path],
        )

    async def generate_back_portrait(self, character: CharacterInScene, front_portrait_path: str) -> ImageOutput:
        """Generate a back-view portrait using the front portrait as reference."""
        prompt = (
            f"A back-view portrait of {character.identifier_in_scene}. "
            f"{character.static_features}. {character.dynamic_features}. "
            f"Same character as the reference image but viewed from behind. Clean background."
        )
        return await self.image_generator.generate_single_image(
            prompt=prompt,
            reference_image_paths=[front_portrait_path],
        )