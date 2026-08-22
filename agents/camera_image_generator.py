import os
import logging
from typing import List, Tuple, Union, Optional
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector

from interfaces import ShotDescription, ShotBriefDescription, Camera, ImageOutput, VideoOutput

from moviepy import VideoFileClip
from PIL import Image
from utils.retry import after_func

system_prompt_template_select_reference_camera = \
"""
[Role]
You are a professional video editing expert specializing in multi-camera shot analysis.

[Task]
Analyze the input camera position data to construct a "camera position tree". Identify the parent camera for each camera position and determine the dependent shot indices.

[Input]
A sequence of cameras enclosed within <camera_seq> and </camera_seq>.
Each camera contains shots enclosed within <camera_N> and </camera_N>.

[Output]
{format_instructions}

[Guidelines]
- Content Inclusion Check: Parent camera should contain child camera's content.
- Transition Smoothness Priority: Prefer similar shot sizes for parent/child.
- Temporal Proximity: Parent camera shot index should be close to child camera's first shot.
- Logical Consistency: The camera tree should be acyclic.
- Only one camera can exist without a parent.
- The first camera must be the root.
"""

human_prompt_template_select_reference_camera = \
"""
<camera_seq>
{camera_seq_str}
</camera_seq>
"""

class CameraParentItem(BaseModel):
    parent_cam_idx: Optional[int] = Field(default=None, description="Parent camera index or None for root.")
    parent_shot_idx: Optional[int] = Field(default=None, description="Dependent shot index or None.")
    reason: str = Field(description="Reason for parent selection.")
    is_parent_fully_covers_child: Optional[bool] = Field(default=None, description="Whether parent fully covers child.")
    missing_info: Optional[str] = Field(default=None, description="Missing elements from parent shot.")

class CameraTreeResponse(BaseModel):
    camera_parent_items: List[Optional[CameraParentItem]] = Field(
        description="Parent camera items for each camera. Length = number of cameras."
    )

class CameraImageGenerator:
    def __init__(
        self,
        chat_model,
        image_generator,
        video_generator,
    ):
        self.chat_model = chat_model
        self.image_generator = image_generator
        self.video_generator = video_generator

    async def construct_camera_tree(
        self,
        cameras: List[Camera],
        shot_descs: List[Union[ShotDescription, ShotBriefDescription]],
    ) -> List[Camera]:
        parser = PydanticOutputParser(pydantic_object=CameraTreeResponse)

        camera_seq_str = ""
        for cam in cameras:
            camera_seq_str += f"<camera_{cam.cam_idx}>\n"
            for shot_idx in cam.active_shot_idxs:
                camera_seq_str += f"Shot {shot_idx}: {shot_descs[shot_idx].visual_desc}\n"
            camera_seq_str += f"</camera_{cam.cam_idx}>\n"

        messages = [
            SystemMessage(content=system_prompt_template_select_reference_camera.format(format_instructions=parser.get_format_instructions())),
            HumanMessage(content=human_prompt_template_select_reference_camera.format(camera_seq_str=camera_seq_str)),
        ]

        chain = self.chat_model | parser
        response: CameraTreeResponse = await chain.ainvoke(messages)
        for cam, parent_cam_item in zip(cameras, response.camera_parent_items):
            if parent_cam_item is not None:
                cam.parent_cam_idx = parent_cam_item.parent_cam_idx
                cam.parent_shot_idx = parent_cam_item.parent_shot_idx
                cam.reason = parent_cam_item.reason
                cam.is_parent_fully_covers_child = parent_cam_item.is_parent_fully_covers_child
                cam.missing_info = parent_cam_item.missing_info
        return cameras

    async def generate_transition_video(
        self,
        first_shot_visual_desc: str,
        second_shot_visual_desc: str,
        first_shot_ff_path: str,
    ) -> VideoOutput:
        prompt = f"Two shots. The transition between the shots is a cut to. The style should be consistent."
        prompt += f"\nThe first shot description: {first_shot_visual_desc}."
        prompt += f"\nThe second shot description: {second_shot_visual_desc}."
        video_output = await self.video_generator.generate_single_video(
            prompt=prompt,
            reference_image_paths=[first_shot_ff_path],
        )
        return video_output

    def get_new_camera_image(
        self,
        transition_video_path: str,
    ) -> ImageOutput:
        video = open_video(transition_video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())
        scene_manager.detect_scenes(video, show_progress=False)
        scene_list = scene_manager.get_scene_list()
        output_dir = os.path.join(os.path.dirname(transition_video_path), "cache")
        os.makedirs(output_dir, exist_ok=True)
        split_video_ffmpeg(transition_video_path, scene_list, output_dir, show_progress=True)

        video_name = os.path.basename(transition_video_path).split('.')[0]
        second_video_path = os.path.join(output_dir, f"{video_name}-Scene-002.mp4")
        if os.path.exists(second_video_path):
            clip = VideoFileClip(second_video_path)
            ff = clip.get_frame(0)
            ff = Image.fromarray(ff.astype('uint8'), 'RGB')
            return ImageOutput(fmt="pil", ext="png", data=ff)
        else:
            clip = VideoFileClip(transition_video_path)
            lf_time = clip.duration - (1 / clip.fps)
            lf_time = max(0, lf_time)
            lf = clip.get_frame(lf_time)
            lf = Image.fromarray(lf.astype('uint8'), 'RGB')
            return ImageOutput(fmt="pil", ext="png", data=lf)

    async def generate_first_frame(
        self,
        shot_desc: ShotDescription,
        character_portrait_path_and_text_pairs: List[Tuple[str, str]],
    ) -> ImageOutput:
        prompt = ""
        reference_image_paths = []
        for i, (path, text) in enumerate(character_portrait_path_and_text_pairs):
            prompt += f"Image {i}: {text}\n"
            reference_image_paths.append(path)
        prompt += f"Generate an image based on the following description: {shot_desc.ff_desc}."
        image_output = await self.image_generator.generate_single_image(
            prompt=prompt,
            reference_image_paths=reference_image_paths,
        )
        return image_output
