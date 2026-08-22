import os
import logging
from agents import Screenwriter, CharacterExtractor, CharacterPortraitsGenerator
from pipelines.script2video_pipeline import Script2VideoPipeline
from interfaces import CharacterInScene
from typing import List, Dict, Optional
import asyncio
import json
from moviepy import VideoFileClip, concatenate_videoclips
import yaml
from langchain.chat_models import init_chat_model
from tools.render_backend import RenderBackend
from utils.provider_presets import resolve_chat_model_config


class Idea2VideoPipeline:
    """Full idea-to-video pipeline.

    Steps:
    1. Develop a story from the idea
    2. Extract characters from the story
    3. Generate character portraits
    4. Write a script from the story
    5. For each scene script, run Script2VideoPipeline
    6. Concatenate all scene videos into the final video
    """

    def __init__(
        self,
        chat_model,
        image_generator,
        video_generator,
        working_dir: str,
    ):
        self.chat_model = chat_model
        self.image_generator = image_generator
        self.video_generator = video_generator
        self.working_dir = working_dir
        os.makedirs(self.working_dir, exist_ok=True)

        self.screenwriter = Screenwriter(chat_model=self.chat_model)
        self.character_extractor = CharacterExtractor(chat_model=self.chat_model)
        self.character_portraits_generator = CharacterPortraitsGenerator(
            image_generator=self.image_generator)

    @classmethod
    def init_from_config(cls, config_path: str) -> "Idea2VideoPipeline":
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        chat_model_args = resolve_chat_model_config(config["chat_model"]["init_args"])
        chat_model = init_chat_model(**chat_model_args)
        backend = RenderBackend.from_config(config)

        return cls(
            chat_model=chat_model,
            image_generator=backend.image_generator,
            video_generator=backend.video_generator,
            working_dir=config["working_dir"],
        )

    async def develop_story(
        self,
        idea: str,
        user_requirement: str,
    ) -> str:
        save_path = os.path.join(self.working_dir, "story.txt")
        if os.path.exists(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                story = f.read()
            print("🚀 Loaded story from existing file.")
            return story

        print("🧠 Developing story...")
        story = await self.screenwriter.develop_story(idea=idea, user_requirement=user_requirement)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(story)
        print(f"✅ Story developed and saved to {save_path}.")
        return story

    async def extract_characters(self, story: str) -> List[CharacterInScene]:
        save_path = os.path.join(self.working_dir, "characters.json")
        if os.path.exists(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                characters = json.load(f)
            characters = [CharacterInScene.model_validate(c) for c in characters]
            print(f"🚀 Loaded {len(characters)} characters from cache.")
            return characters

        print("🧠 Extracting characters...")
        characters = await self.character_extractor.extract_characters(story)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in characters], f, ensure_ascii=False, indent=4)
        print(f"✅ Extracted {len(characters)} characters.")
        return characters

    async def generate_character_portraits(
        self,
        characters: List[CharacterInScene],
        character_portraits_registry: Optional[Dict[str, Dict[str, Dict[str, str]]]],
        style: str,
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        registry_path = os.path.join(self.working_dir, "character_portraits_registry.json")

        if character_portraits_registry is None:
            if os.path.exists(registry_path):
                with open(registry_path, 'r', encoding='utf-8') as f:
                    character_portraits_registry = json.load(f)
            else:
                character_portraits_registry = {}

        tasks = [
            self._generate_portraits_for_single_character(character, style)
            for character in characters
            if character.identifier_in_scene not in character_portraits_registry
        ]

        if tasks:
            for future in asyncio.as_completed(tasks):
                result = await future
                character_portraits_registry.update(result)
                with open(registry_path, 'w', encoding='utf-8') as f:
                    json.dump(character_portraits_registry, f, ensure_ascii=False, indent=4)
            print(f"✅ Completed portrait generation for {len(characters)} characters.")
        else:
            print("🚀 All characters already have portraits.")

        return character_portraits_registry

    async def _generate_portraits_for_single_character(
        self,
        character: CharacterInScene,
        style: str,
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        character_dir = os.path.join(
            self.working_dir, "character_portraits",
            f"{character.idx}_{character.identifier_in_scene.strip('<>')}")
        os.makedirs(character_dir, exist_ok=True)

        front_path = os.path.join(character_dir, "front.png")
        if not os.path.exists(front_path):
            output = await self.character_portraits_generator.generate_front_portrait(character, style)
            output.save(front_path)

        side_path = os.path.join(character_dir, "side.png")
        if not os.path.exists(side_path):
            output = await self.character_portraits_generator.generate_side_portrait(character, front_path)
            output.save(side_path)

        back_path = os.path.join(character_dir, "back.png")
        if not os.path.exists(back_path):
            output = await self.character_portraits_generator.generate_back_portrait(character, front_path)
            output.save(back_path)

        print(f"  ☑️ Portraits generated for {character.identifier_in_scene}.")

        return {
            character.identifier_in_scene: {
                "front": {"path": front_path, "description": f"A front view portrait of {character.identifier_in_scene}."},
                "side": {"path": side_path, "description": f"A side view portrait of {character.identifier_in_scene}."},
                "back": {"path": back_path, "description": f"A back view portrait of {character.identifier_in_scene}."},
            }
        }

    async def write_script_based_on_story(
        self,
        story: str,
        user_requirement: str,
    ) -> List[str]:
        save_path = os.path.join(self.working_dir, "script.json")
        if os.path.exists(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                script = json.load(f)
            print("🚀 Loaded script from cache.")
            return script

        print("🧠 Writing script...")
        script = await self.screenwriter.write_script_based_on_story(
            story=story, user_requirement=user_requirement)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=4)
        print(f"✅ Script written ({len(script)} scenes).")
        return script

    async def __call__(
        self,
        idea: str,
        user_requirement: str,
        style: str,
    ) -> str:
        print(f"\n{'#'*60}")
        print(f"  ViMax-RH: Idea-to-Video Pipeline")
        print(f"  Powered by RunningHub ComfyUI Workflows")
        print(f"{'#'*60}\n")

        # 1. Develop story
        story = await self.develop_story(idea=idea, user_requirement=user_requirement)

        # 2. Extract characters
        characters = await self.extract_characters(story=story)

        # 3. Generate character portraits
        character_portraits_registry = await self.generate_character_portraits(
            characters=characters,
            character_portraits_registry=None,
            style=style,
        )

        # 4. Write script
        scene_scripts = await self.write_script_based_on_story(story=story, user_requirement=user_requirement)

        # 5. Generate video for each scene
        all_video_paths = []
        for idx, scene_script in enumerate(scene_scripts):
            print(f"\n--- Scene {idx + 1}/{len(scene_scripts)} ---")
            scene_working_dir = os.path.join(self.working_dir, f"scene_{idx}")
            os.makedirs(scene_working_dir, exist_ok=True)

            script2video = Script2VideoPipeline(
                chat_model=self.chat_model,
                image_generator=self.image_generator,
                video_generator=self.video_generator,
                working_dir=scene_working_dir,
            )
            final_video_path = await script2video(
                script=scene_script,
                user_requirement=user_requirement,
                style=style,
                characters=characters,
                character_portraits_registry=character_portraits_registry,
            )
            all_video_paths.append(final_video_path)

        # 6. Concatenate all scene videos
        final_video_path = os.path.join(self.working_dir, "final_video.mp4")
        if os.path.exists(final_video_path):
            print(f"\n🚀 Final video already exists: {final_video_path}")
            return final_video_path

        print(f"\n🎬 Concatenating {len(all_video_paths)} scene videos...")
        video_clips = [VideoFileClip(vp) for vp in all_video_paths]
        final_video = concatenate_videoclips(video_clips)
        final_video.write_videofile(final_video_path, logger=None)
        for c in video_clips:
            c.close()
        final_video.close()
        print(f"✅ Final video saved to {final_video_path}")

        return final_video_path
