from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ShotBriefDescription(BaseModel):
    idx: int = Field(
        description="The index of the shot in the sequence, starting from 0.",
        examples=[0, 1, 2],
    )
    is_last: bool = Field(
        description="Whether this is the last shot. If True, the story of the script has ended and no more shots will be planned after this one.",
        examples=[False, True],
    )
    cam_idx: int = Field(
        description="The index of the camera in the scene.",
        examples=[0, 1, 2],
    )
    visual_desc: str = Field(
        description='''A vivid and detailed visual description of the shot that convey rich visual information through text. The character identifiers in the description must match those in the character list and be enclosed in angle brackets (e.g., <Alice>, <Bob>). All visible characters should be described.
        If there is a conversation, please write down the content of the conversation, when you meet some dialogue, you should write into the visual content description with :" " symbols and the character's features.
        ''',
    )
    audio_desc: str = Field(
        description="A detailed description of the audio in the shot.",
    )

    def __str__(self):
        s = f"Shot {self.idx}:\n"
        s += f"Camera Index: {self.cam_idx}\n"
        s += f"Visual: {self.visual_desc}\n"
        s += f"Audio: {self.audio_desc}"
        return s


class ShotDescription(BaseModel):
    idx: int = Field(
        description="The index of the shot in the sequence, starting from 0."
    )
    is_last: bool = Field(
        description="Whether this is the last shot in the sequence."
    )
    cam_idx: int = Field(
        description="The index of the camera in the scene.",
        examples=[0, 1, 2],
    )
    visual_desc: str = Field(
        description='''A vivid and detailed visual description of the shot that convey rich visual information through text. The character identifiers in the description must match those in the character list and be enclosed in angle brackets (e.g., <Alice>, <Bob>).
        If there is a conversation, please write down the content of the conversation, when you meet some dialogue, you should write into the visual content description with :" " symbols and the character's features.
        ''',
    )
    variation_type: Literal["large", "medium", "small"] = Field(
        description="Indicates the degree of change in the shot's content.",
        examples=["large", "medium", "small"],
    )
    variation_reason: str = Field(
        description="The reason for the variation type of the shot.",
    )
    ff_desc: str = Field(
        description="The first frame of the shot.",
    )
    ff_vis_char_idxs: List[int] = Field(
        default=[],
        description="The indices of the characters in the first frame.",
    )
    lf_desc: str = Field(
        description="The last frame of the shot.",
    )
    lf_vis_char_idxs: List[int] = Field(
        default=[],
        description="The indices of the characters in the last frame.",
    )
    motion_desc: str = Field(
        description='''The motion description of the shot.
        If there is a conversation, please write down the content of the conversation with :" " symbols and the character's features.
        ''',
    )
    audio_desc: str = Field(
        description="A detailed description of the audio in the shot.",
    )
