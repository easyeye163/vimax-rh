import logging
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from interfaces import Event, Scene
from interfaces import CharacterInScene, CharacterInEvent, CharacterInNovel
from tenacity import retry, stop_after_attempt
from utils.retry import after_func

system_prompt_template_merge_characters_across_scenes_in_event = \
"""
You are an expert script analysis and character fusion specialist. Your role is to analyze multiple script scenes, identify characters that represent the same entity across different scenes, and merge them into a unified character list.

**TASK**
Process the input scenes, each containing a script and characters. Identify and merge characters that are the same across scenes. Output a consolidated list of characters for the entire event.

**INPUT**
A sequence of scenes. Each scene is enclosed within <scene_N> and </scene_N> tags.

**OUTPUT**
{format_instructions}

**GUIDELINES**
1. Character Fusion: Analyze contextual clues to determine if characters from different scenes are the same person.
2. Unique Identifier: Assign a consistent, unique ID to each merged character.
3. Scene Mapping: For each character, list all scenes they appear in and the name used.
4. Completeness: Ensure all characters from all scenes are included.
5. If a character undergoes significant changes across scenes, split them into separate roles.
6. The language of outputs in values should be same as the input text.
"""

human_prompt_template_merge_characters_across_scenes_in_event = \
"""
{scenes_sequence}
"""

class MergeCharactersAcrossScenesInEventResponse(BaseModel):
    characters: List[CharacterInEvent] = Field(
        description="List of merged characters with their identifiers",
    )

system_prompt_template_merge_characters_to_existing_characters_in_novel = \
"""
You are an information integration expert skilled in accurately identifying, matching, and merging character information.

**TASK**
Merge the character list extracted from the current event into the global character list.

**INPUT**
1. Existing Characters in the Novel, enclosed within <existing_characters> and </existing_characters>.
2. Characters in the Current Event, enclosed within <event_characters> and </event_characters>.

**OUTPUT**
{format_instructions}

**GUIDELINES**
1. Feature Consistency: Strictly compare features. Distinguish youth/old age versions as separate characters.
2. Efficient Merging: Avoid duplicate characters.
3. Feature Update: Update descriptions if new information is available.
"""

human_prompt_template_merge_characters_to_existing_characters_in_novel = \
"""
<existing_characters>
{existing_characters_in_novel}
</existing_characters>

<event_characters>
{characters_in_event}
</event_characters>
"""

class CharacterForMergingToNovel(BaseModel):
    index_in_event: int = Field(
        description="The index of the character in the event list.",
    )
    index_in_novel: int = Field(
        description="The index in the novel list. -1 if new.",
    )
    identifier_in_novel: str = Field(
        description="The unique identifier for the character in the novel.",
    )
    modified_features: str = Field(
        description="The modified static features after merging.",
    )

class MergeCharactersToExistingCharactersInNovelResponse(BaseModel):
    characters: List[CharacterForMergingToNovel] = Field(
        description="List of characters with mapping info."
    )

class GlobalInformationPlanner:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def merge_characters_across_scenes_in_event(
        self,
        event_idx: int,
        scenes: List[Scene],
    ) -> List[CharacterInEvent]:
        scenes_sequence_str = ""
        for scene in scenes:
            scene_str = f"<scene_{scene.idx}>\n"
            scene_str += "<script>\n" + scene.script + "\n</script>\n\n"
            scene_str += "<characters>\n"
            for character in scene.characters:
                scene_str += f"<character_{character.idx}>\n"
                scene_str += str(character)
                scene_str += f"\n</character_{character.idx}>\n"
            scene_str += "</characters>\n"
            scene_str += f"</scene_{scene.idx}>\n"
            scenes_sequence_str += scene_str

        parser = PydanticOutputParser(pydantic_object=MergeCharactersAcrossScenesInEventResponse)

        messages = [
            SystemMessage(
                content=system_prompt_template_merge_characters_across_scenes_in_event.format(
                    format_instructions=parser.get_format_instructions(),
                ),
            ),
            HumanMessage(
                content=human_prompt_template_merge_characters_across_scenes_in_event.format(
                    scenes_sequence=scenes_sequence_str,
                )
            )
        ]

        chain = self.chat_model | parser
        response: MergeCharactersAcrossScenesInEventResponse = await chain.ainvoke(messages)
        characters_in_event = response.characters

        # Validate output
        flags = [{c.identifier_in_scene: False for c in s.characters} for s in scenes]
        for character in characters_in_event:
            for scene_idx, identifier_in_scene in character.active_scenes.items():
                if identifier_in_scene not in [c.identifier_in_scene for c in scenes[scene_idx].characters]:
                    raise ValueError(f"Character {identifier_in_scene} not found in scene {scene_idx}")
                else:
                    flags[scene_idx][identifier_in_scene] = True
        for scene_idx, flag in enumerate(flags):
            for identifier_in_scene, included in flag.items():
                if not included:
                    raise ValueError(f"Character {identifier_in_scene} in scene {scene_idx} not included")

        return characters_in_event

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def merge_characters_to_existing_characters_in_novel(
        self,
        event_idx: int,
        existing_characters_in_novel: List[CharacterInNovel],
        characters_in_event: List[CharacterInEvent],
    ) -> List[CharacterInNovel]:
        existing_characters_str = ""
        for character in existing_characters_in_novel:
            existing_characters_str += f"<character_{character.index}>\n"
            existing_characters_str += str(character)
            existing_characters_str += f"\n</character_{character.index}>\n"

        characters_in_event_str = ""
        for character in characters_in_event:
            characters_in_event_str += f"<character_{characters_in_event.index(character)}>\n"
            characters_in_event_str += character.identifier_in_event + "\n"
            characters_in_event_str += "Static features: " + character.static_features + "\n"
            characters_in_event_str += f"</character_{characters_in_event.index(character)}>\n"

        parser = PydanticOutputParser(pydantic_object=MergeCharactersToExistingCharactersInNovelResponse)

        messages = [
            SystemMessage(
                content=system_prompt_template_merge_characters_to_existing_characters_in_novel.format(
                    format_instructions=parser.get_format_instructions(),
                ),
            ),
            HumanMessage(
                content=human_prompt_template_merge_characters_to_existing_characters_in_novel.format(
                    existing_characters_in_novel=existing_characters_str,
                    characters_in_event=characters_in_event_str,
                )
            )
        ]

        chain = self.chat_model | parser
        response: MergeCharactersToExistingCharactersInNovelResponse = await chain.ainvoke(messages)

        for character in response.characters:
            if character.index_in_novel == -1:
                new_character = CharacterInNovel(
                    index=len(existing_characters_in_novel),
                    identifier_in_novel=character.identifier_in_novel,
                    static_features=character.modified_features,
                    active_events={event_idx: characters_in_event[character.index_in_event].identifier_in_event},
                )
                existing_characters_in_novel.append(new_character)
            else:
                existing_characters_in_novel[character.index_in_novel].static_features = character.modified_features
                existing_characters_in_novel[character.index_in_novel].active_events.update({event_idx: characters_in_event[character.index_in_event].identifier_in_event})

        return existing_characters_in_novel
