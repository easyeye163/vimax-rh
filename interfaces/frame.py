from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Frame(BaseModel):
    shot_idx: int = Field(
        description="The index of the shot in the sequence, starting from 0."
    )
    frame_type: Literal["first", "last"] = Field(
        description="The type of the frame, 'first' for the first frame of the shot, 'last' for the last frame of the shot."
    )
    cam_idx: int = Field(
        description="The index of the camera used for this frame, starting from 0."
    )
    vis_char_idxs: List[int] = Field(
        description="A list of indices of characters that are visible in this frame, corresponding to the character list provided in the input."
    )


class Camera(BaseModel):
    cam_idx: int = Field(
        description="The index of the camera, starting from 0."
    )
    active_shot_idxs: List[int] = Field(
        description="The indices of shots filmed by this camera."
    )
    parent_cam_idx: Optional[int] = Field(
        default=None,
        description="The index of the parent camera, if any."
    )
    parent_shot_idx: Optional[int] = Field(
        default=None,
        description="The index of the shot within the parent camera that covers this camera's content."
    )
    reason: Optional[str] = Field(
        default=None,
        description="The reason for the parent camera selection."
    )
    is_parent_fully_covers_child: Optional[bool] = Field(
        default=None,
        description="Whether the parent camera fully covers the child camera's content."
    )
    missing_info: Optional[str] = Field(
        default=None,
        description="The missing elements in the child shot that are not covered by the parent shot."
    )
