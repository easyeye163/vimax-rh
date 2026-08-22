from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class CharacterInScene(BaseModel):
    idx: int = Field(
        description="The index of the character in the scene, starting from 0.",
        examples=[0, 1, 2],
    )
    identifier_in_scene: str = Field(
        description="The unique identifier/name for the character within the scene. Enclosed in angle brackets (e.g., '<Alice>').",
        examples=["<Alice>", "<Bob the Builder>"],
    )
    static_features: str = Field(
        description="The character's unchanging physical traits such as facial features, body shape, hair, skin tone, etc.",
    )
    dynamic_features: str = Field(
        description="The character's changeable traits such as clothing, accessories, key items they carry, etc.",
    )

    def __str__(self):
        return (
            f"{self.identifier_in_scene} [visible]\n"
            f"static features: {self.static_features}\n"
            f"dynamic features: {self.dynamic_features}"
        )


class CharacterInEvent(BaseModel):
    identifier_in_event: str = Field(
        description="The unique identifier for the character across the event.",
    )
    static_features: str = Field(
        description="The aggregated static features of the character across all scenes in the event.",
    )
    active_scenes: Dict[int, str] = Field(
        description="A mapping from scene index to the character's identifier used in that scene.",
    )

    def __str__(self):
        scenes_str = ", ".join([f"scene {idx}: {name}" for idx, name in self.active_scenes.items()])
        return f"{self.identifier_in_event} (active in {scenes_str}), static features: {self.static_features}"


class CharacterInNovel(BaseModel):
    index: int = Field(
        description="The unique index of the character in the novel.",
        examples=[0, 1, 2],
    )
    identifier_in_novel: str = Field(
        description="The canonical identifier for the character across the entire novel.",
    )
    static_features: str = Field(
        description="The comprehensive static features of the character.",
    )
    active_events: Dict[int, str] = Field(
        default_factory=dict,
        description="A mapping from event index to the character's identifier used in that event.",
    )

    def __str__(self):
        events_str = ", ".join([f"event {idx}: {name}" for idx, name in self.active_events.items()])
        return f"{self.identifier_in_novel} (index {self.index}, active in {events_str}), static features: {self.static_features}"
