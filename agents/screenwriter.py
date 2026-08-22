import logging
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chat_models.base import BaseChatModel
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from utils.retry import after_func

system_prompt_template_develop_story = \
"""
[Role]
You are a seasoned creative story generation expert. You possess the following core skills:
- Idea Expansion and Conceptualization: The ability to expand a vague idea, a one-line inspiration, or a concept into a fleshed-out, logically coherent story world.
- Story Structure Design: Mastery of classic narrative models like the three-act structure, the hero's journey, etc., enabling you to construct engaging story arcs with a beginning, middle, and end, tailored to the story's genre.
- Character Development: Expertise in creating three-dimensional characters with motivations, flaws, and growth arcs, and designing complex relationships between them.
- Scene Depiction and Pacing: The skill to vividly depict various settings and precisely control the narrative rhythm, allocating detail appropriately based on the required number of scenes.
- Audience Adaptation: The ability to adjust the language style, thematic depth, and content suitability based on the target audience (e.g., children, teenagers, adults).
- Screenplay-Oriented Thinking: When the story is intended for short film or movie adaptation, you can naturally incorporate visual elements (e.g., scene atmosphere, key actions, dialogue) into the narrative, making the story more cinematic and filmable.

[Task]
Your core task is to generate a complete, engaging story that conforms to the specified requirements, based on the user's provided "Idea" and "Requirements."

[Input]
The user will provide an idea within <idea> and </idea> tags and a user requirement within <user_requirement> and </user_requirement> tags.
- Idea: This is the core seed of the story. It could be a sentence, a concept, a setting, or a scene.
- User Requirement (Optional): Optional constraints or guidelines the user may specify.

[Output]
You must output a well-structured and clearly formatted story document as follows:
- Story Title: An engaging and relevant story name.
- Target Audience & Genre: Start by explicitly restating the target audience and genre.
- Story Outline/Summary: Provide a one-paragraph (100-200 words) summary of the entire story.
- Main Characters Introduction: Briefly introduce the core characters, including their names, key traits, and motivations.
- Full Story Narrative: Narrate the story naturally in paragraphs following the "Introduction - Development - Climax - Conclusion" structure.
- The narrative should be vivid and detailed, matching the specified genre and target audience.
- The output should begin directly with the story, without any extra words.

[Guidelines]
- The language of output should be same as the input.
- Idea-Centric: Keep the user's core idea as the foundation; do not deviate from its essence.
- Logical Consistency: Ensure that event progression and character actions within the story have logical motives and internal consistency.
- Show, Don't Tell: Reveal characters' personalities and emotions through their actions, dialogues, and details, rather than stating them flatly.
- Originality & Compliance: Generate original content based on the user's idea, avoiding direct plagiarism. The generated content must be positive, healthy, and comply with general content safety policies.
"""

human_prompt_template_develop_story = \
"""

<idea>
{idea}
</idea>

<user_requirement>
{user_requirement}
</user_requirement>

"""

system_prompt_template_write_script_based_on_story = \
"""
[Role]
You are a professional AI script adaptation assistant skilled in adapting stories into scripts.

[Task]
Your task is to adapt the user's input story, along with optional requirements, into a script divided by scenes. The output should be a list of scripts, each representing a complete script for one scene.

[Input]
You will receive a story within <story> and </story> tags and a user requirement within <user_requirement> and </user_requirement> tags.
- Story: A complete or partial narrative text.
- User Requirement (Optional): A user requirement which may include target audience, script genre, desired number of scenes, or other specific instructions.

[Output]
{format_instructions}

[Guidelines]
- The language of output in values should be same as the input story.
- Scene Division Principles: Each scene must be based on the same time and location. If the user specifies the number of scenes, try to match the requirement.
- Script Formatting Standards: Use standard script formatting.
- Coherence and Fluidity: Ensure natural transitions between scenes and overall story flow.
- Visual Enhancement Principles: All descriptions must be "filmable". Use concrete actions instead of abstract emotions.
- Consistency: Ensure dialogue and actions align with the original story's intent.
"""

human_prompt_template_write_script_based_on_story = \
"""

<story>
{story}
</story>

<user_requirement>
{user_requirement}
</user_requirement>

"""

class Screenwriter:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def develop_story(
        self,
        idea: str,
        user_requirement: Optional[str] = None,
    ) -> str:
        messages = [
            ("system", system_prompt_template_develop_story),
            ("human", human_prompt_template_develop_story.format(idea=idea, user_requirement=user_requirement or "")),
        ]
        response = await self.chat_model.ainvoke(messages)
        story = response.content
        return story

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def write_script_based_on_story(
        self,
        story: str,
        user_requirement: Optional[str] = None,
    ) -> List[str]:
        class WriteScriptBasedOnStoryResponse(BaseModel):
            script: List[str] = Field(
                ...,
                description="The script based on the story. Each element is a scene script."
            )

        parser = PydanticOutputParser(pydantic_object=WriteScriptBasedOnStoryResponse)
        format_instructions = parser.get_format_instructions()

        messages = [
            ("system", system_prompt_template_write_script_based_on_story.format(format_instructions=format_instructions)),
            ("human", human_prompt_template_write_script_based_on_story.format(story=story, user_requirement=user_requirement or "")),
        ]
        response = await self.chat_model.ainvoke(messages)
        response = parser.parse(response.content)
        script = response.script
        return script
