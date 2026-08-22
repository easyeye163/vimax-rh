from interfaces import Event, Scene
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt
import logging
from utils.retry import after_func

system_prompt_template_get_next_scene = \
"""
You are an expert scriptwriter specializing in adapting literary works into structured screenplay scenes.

**TASK**
Generate the next scene for a screenplay adaptation based on the provided input. Each scene must include:
- Environment: slugline and detailed description
- Characters: List of characters appearing in the scene
- Script: Character actions and dialogues

**INPUT**
- Event Description enclosed within <event_description> and </event_description>.
- Context Fragments enclosed within <context_fragments> and </context_fragments>.
- Previous Scenes (if any) enclosed within <previous_scenes> and </previous_scenes>.

**OUTPUT**
{format_instructions}

**GUIDELINES**
1. Extract scenes based on the provided context fragments.
2. Focus on Relevance: Use only context fragments that directly align with the event.
3. Dialogues and Actions: Convert descriptive prose into actionable lines.
4. Conciseness: Keep descriptions brief and visual.
5. Format Consistency: Ensure industry-standard screenplay structure.
6. The character must be an individual, not a group.
7. When location or time changes, create a new scene. Total scenes should not exceed 5.
8. The language of outputs should be same as the input.
"""

human_prompt_template_get_next_scene = \
"""
<event_description>
{event_description}
</event_description>

<context_fragments>
{context_fragments}
</context_fragments>

<previous_scenes>
{previous_scenes}
</previous_scenes>
"""

class SceneExtractor:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(5),
        after=after_func,
    )
    async def get_next_scene(
        self,
        relevant_chunks: List[str],
        event: Event,
        previous_scenes: List[Scene],
    ) -> Scene:
        context_fragments_str = "\n".join([f"<chunk_{i}>\n{chunk}\n</chunk_{i}>" for i, chunk in enumerate(relevant_chunks)])
        previous_scenes_str = "\n".join([f"<scene_{i}>\n{scene}\n</scene_{i}>" for i, scene in enumerate(previous_scenes)])

        parser = PydanticOutputParser(pydantic_object=Scene)

        messages = [
            SystemMessage(
                content=system_prompt_template_get_next_scene.format(
                    format_instructions=parser.get_format_instructions(),
                ),
            ),
            HumanMessage(
                content=human_prompt_template_get_next_scene.format(
                    event_description=str(event),
                    context_fragments=context_fragments_str,
                    previous_scenes=previous_scenes_str,
                )
            )
        ]

        chain = self.chat_model | parser
        scene = await chain.ainvoke(messages)
        return scene
