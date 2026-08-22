import os
import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from moviepy import VideoFileClip, concatenate_videoclips

from interfaces import (
    CharacterInScene, ShotBriefDescription, ShotDescription, Camera,
    ImageOutput, VideoOutput, Frame,
)
from agents import (
    StoryboardArtist,
    CharacterPortraitsGenerator,
    ReferenceImageSelector,
    BestImageSelector,
    CameraImageGenerator,
)

logger = logging.getLogger(__name__)


class Script2VideoPipeline:
    """Converts a single scene script into a video clip.

    Steps:
    1. Extract characters from the script
    2. Design storyboard (shot brief descriptions)
    3. Decompose each shot into first/last frame + motion
    4. Build camera tree
    5. Generate reference images (character portraits + scene frames)
    6. Generate videos per shot
    7. Concatenate into final scene video
    """

    def __init__(
        self,
        chat_model,
        image_generator,
        video_generator,
        working_dir: str,
        num_candidate_images: int = 4,
        num_best_selection_rounds: int = 2,
    ):
        self.chat_model = chat_model
        self.image_generator = image_generator
        self.video_generator = video_generator
        self.working_dir = working_dir
        self.num_candidate_images = num_candidate_images
        self.num_best_selection_rounds = num_best_selection_rounds

        os.makedirs(self.working_dir, exist_ok=True)

        self.storyboard_artist = StoryboardArtist(chat_model=self.chat_model)
        self.reference_image_selector = ReferenceImageSelector(chat_model=self.chat_model)
        self.best_image_selector = BestImageSelector(chat_model=self.chat_model)
        self.camera_image_generator = CameraImageGenerator(
            chat_model=self.chat_model,
            image_generator=self.image_generator,
            video_generator=self.video_generator,
        )

    # ------------------------------------------------------------------
    # Helper: collect portrait path+text for visible characters
    # ------------------------------------------------------------------
    def _get_portrait_pairs(
        self,
        characters: List[CharacterInScene],
        vis_char_idxs: List[int],
        character_portraits_registry: Dict[str, Dict[str, Dict[str, str]]],
    ) -> List[Tuple[str, str]]:
        pairs = []
        for idx in vis_char_idxs:
            if idx >= len(characters):
                continue
            char = characters[idx]
            registry = character_portraits_registry.get(char.identifier_in_scene, {})
            # Prefer front view, then side, then back
            for view in ["front", "side", "back"]:
                entry = registry.get(view)
                if entry and os.path.exists(entry["path"]):
                    pairs.append((entry["path"], entry["description"]))
                    break
        return pairs

    # ------------------------------------------------------------------
    # Step 1: Design storyboard
    # ------------------------------------------------------------------
    async def design_storyboard(
        self,
        script: str,
        characters: List[CharacterInScene],
        user_requirement: Optional[str],
    ) -> List[ShotBriefDescription]:
        save_path = os.path.join(self.working_dir, "storyboard.json")
        if os.path.exists(save_path):
            import json
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            storyboard = [ShotBriefDescription.model_validate(s) for s in data]
            print(f"  🚀 Loaded storyboard ({len(storyboard)} shots) from cache.")
            return storyboard

        print("  🧠 Designing storyboard...")
        storyboard = await self.storyboard_artist.design_storyboard(
            script=script,
            characters=characters,
            user_requirement=user_requirement,
        )

        import json
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump([s.model_dump() for s in storyboard], f, ensure_ascii=False, indent=2)
        print(f"  ✅ Storyboard designed: {len(storyboard)} shots.")
        return storyboard

    # ------------------------------------------------------------------
    # Step 2: Decompose shots
    # ------------------------------------------------------------------
    async def decompose_shots(
        self,
        shot_briefs: List[ShotBriefDescription],
        characters: List[CharacterInScene],
    ) -> List[ShotDescription]:
        save_path = os.path.join(self.working_dir, "shot_descriptions.json")
        if os.path.exists(save_path):
            import json
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            shots = [ShotDescription.model_validate(s) for s in data]
            print(f"  🚀 Loaded shot descriptions ({len(shots)}) from cache.")
            return shots

        print("  🧠 Decomposing shot descriptions...")
        shots = []
        for brief in shot_briefs:
            desc = await self.storyboard_artist.decompose_visual_description(
                shot_brief_desc=brief,
                characters=characters,
            )
            shots.append(desc)

        import json
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump([s.model_dump() for s in shots], f, ensure_ascii=False, indent=2)
        print(f"  ✅ Decomposed {len(shots)} shots.")
        return shots

    # ------------------------------------------------------------------
    # Step 3: Build camera tree
    # ------------------------------------------------------------------
    async def build_camera_tree(
        self,
        shots: List[ShotDescription],
    ) -> List[Camera]:
        # Group shots by camera
        cam_shot_map: Dict[int, List[int]] = {}
        for shot in shots:
            cam_shot_map.setdefault(shot.cam_idx, []).append(shot.idx)

        cameras = []
        for cam_idx, active_shot_idxs in sorted(cam_shot_map.items()):
            cameras.append(Camera(cam_idx=cam_idx, active_shot_idxs=active_shot_idxs))

        save_path = os.path.join(self.working_dir, "camera_tree.json")
        if os.path.exists(save_path):
            import json
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cameras = [Camera.model_validate(c) for c in data]
            print(f"  🚀 Loaded camera tree ({len(cameras)} cameras) from cache.")
            return cameras

        print("  🧠 Building camera tree...")
        cameras = await self.camera_image_generator.construct_camera_tree(
            cameras=cameras,
            shot_descs=shots,
        )

        import json
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in cameras], f, ensure_ascii=False, indent=2)
        print(f"  ✅ Camera tree built: {len(cameras)} cameras.")
        return cameras

    # ------------------------------------------------------------------
    # Step 4: Generate first frame for a shot
    # ------------------------------------------------------------------
    async def generate_first_frame_for_shot(
        self,
        shot: ShotDescription,
        characters: List[CharacterInScene],
        character_portraits_registry: Dict[str, Dict[str, Dict[str, str]]],
        available_ref_images: List[Tuple[str, str]],
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """Generate first frame image and return (path, updated_ref_images)."""
        ff_dir = os.path.join(self.working_dir, "first_frames")
        os.makedirs(ff_dir, exist_ok=True)
        ff_path = os.path.join(ff_dir, f"shot_{shot.idx}_ff.png")

        if os.path.exists(ff_path):
            print(f"  🚀 First frame for shot {shot.idx} exists, skipping.")
            return ff_path, available_ref_images

        # Select reference images and generate prompt
        ref_result = await self.reference_image_selector.select_reference_images_and_generate_prompt(
            available_image_path_and_text_pairs=available_ref_images,
            frame_description=shot.ff_desc,
        )
        ref_pairs = ref_result["reference_image_path_and_text_pairs"]
        text_prompt = ref_result["text_prompt"]

        ref_paths = [p for p, _ in ref_pairs]
        ref_texts = [t for _, t in ref_pairs]

        # Generate multiple candidates and select best
        candidates_dir = os.path.join(ff_dir, f"shot_{shot.idx}_candidates")
        os.makedirs(candidates_dir, exist_ok=True)

        candidate_paths = []
        for i in range(self.num_candidate_images):
            candidate_path = os.path.join(candidates_dir, f"candidate_{i}.png")
            if os.path.exists(candidate_path):
                candidate_paths.append(candidate_path)
                continue

            image_output = await self.image_generator.generate_single_image(
                prompt=text_prompt,
                reference_image_paths=ref_paths,
            )
            image_output.save(candidate_path)
            candidate_paths.append(candidate_path)

        # Select best image
        best_path = await self.best_image_selector(
            reference_image_path_and_text_pairs=ref_pairs,
            target_description=shot.ff_desc,
            candidate_image_paths=candidate_paths,
        )

        # Copy best to ff_path
        import shutil
        shutil.copy2(best_path, ff_path)

        # Update available references with this frame
        new_ref = available_ref_images + [(ff_path, shot.ff_desc)]
        print(f"  ✅ First frame for shot {shot.idx} generated.")
        return ff_path, new_ref

    # ------------------------------------------------------------------
    # Step 5: Generate video for a shot
    # ------------------------------------------------------------------
    async def generate_video_for_shot(
        self,
        shot: ShotDescription,
        ff_path: str,
        prev_lf_path: Optional[str],
    ) -> str:
        video_dir = os.path.join(self.working_dir, "videos")
        os.makedirs(video_dir, exist_ok=True)
        video_path = os.path.join(video_dir, f"shot_{shot.idx}.mp4")

        if os.path.exists(video_path):
            print(f"  🚀 Video for shot {shot.idx} exists, skipping.")
            return video_path

        # Build video prompt from motion description
        prompt = shot.motion_desc
        ref_images = [ff_path]
        if prev_lf_path:
            ref_images = [prev_lf_path]

        print(f"  🎬 Generating video for shot {shot.idx}...")
        video_output = await self.video_generator.generate_single_video(
            prompt=prompt,
            reference_image_paths=ref_images,
        )
        video_output.save(video_path)
        print(f"  ✅ Video for shot {shot.idx} saved.")
        return video_path

    # ------------------------------------------------------------------
    # Extract last frame from a video
    # ------------------------------------------------------------------
    def extract_last_frame(self, video_path: str) -> str:
        lf_dir = os.path.join(self.working_dir, "last_frames")
        os.makedirs(lf_dir, exist_ok=True)
        shot_idx = os.path.basename(video_path).replace("shot_", "").replace(".mp4", "")
        lf_path = os.path.join(lf_dir, f"shot_{shot_idx}_lf.png")

        if os.path.exists(lf_path):
            return lf_path

        clip = VideoFileClip(video_path)
        lf_time = clip.duration - (1 / clip.fps)
        lf_time = max(0, lf_time)
        lf_frame = clip.get_frame(lf_time)
        from PIL import Image as PILImage
        img = PILImage.fromarray(lf_frame.astype('uint8'), 'RGB')
        img.save(lf_path)
        clip.close()
        return lf_path

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def __call__(
        self,
        script: str,
        user_requirement: Optional[str],
        style: str,
        characters: List[CharacterInScene],
        character_portraits_registry: Dict[str, Dict[str, Dict[str, str]]],
    ) -> str:
        print(f"\n{'='*60}")
        print(f"  Script2VideoPipeline")
        print(f"{'='*60}")

        # 1. Design storyboard
        shot_briefs = await self.design_storyboard(script, characters, user_requirement)
        if not shot_briefs:
            raise ValueError("No shots designed for this scene.")

        # 2. Decompose shots
        shots = await self.decompose_shots(shot_briefs, characters)

        # 3. Build camera tree
        cameras = await self.build_camera_tree(shots)

        # 4. Generate first frames and videos per shot
        available_ref_images: List[Tuple[str, str]] = []
        # Seed with character portraits
        for char in characters:
            registry = character_portraits_registry.get(char.identifier_in_scene, {})
            for view in ["front", "side", "back"]:
                entry = registry.get(view)
                if entry and os.path.exists(entry["path"]):
                    available_ref_images.append((entry["path"], entry["description"]))

        video_paths = []
        prev_lf_path = None

        for shot in shots:
            # Generate first frame
            ff_path, available_ref_images = await self.generate_first_frame_for_shot(
                shot=shot,
                characters=characters,
                character_portraits_registry=character_portraits_registry,
                available_ref_images=available_ref_images,
            )

            # Generate video
            video_path = await self.generate_video_for_shot(
                shot=shot,
                ff_path=ff_path,
                prev_lf_path=prev_lf_path,
            )
            video_paths.append(video_path)

            # Extract last frame for chaining
            prev_lf_path = self.extract_last_frame(video_path)

        # 5. Concatenate all shot videos
        final_video_path = os.path.join(self.working_dir, "scene_video.mp4")
        if os.path.exists(final_video_path):
            print(f"  🚀 Scene video already exists, skipping concatenation.")
            return final_video_path

        print(f"  🎬 Concatenating {len(video_paths)} shot videos...")
        clips = [VideoFileClip(vp) for vp in video_paths]
        final = concatenate_videoclips(clips)
        final.write_videofile(final_video_path, logger=None)
        for c in clips:
            c.close()
        final.close()
        print(f"  ✅ Scene video saved to {final_video_path}")

        return final_video_path
