"""ViMax-RH: Idea-to-Video Pipeline Entry Point.

A fork of the ViMax (HKUDS/ViMax) idea-to-video pipeline, replacing
Google/Doubao API backends with RunningHub ComfyUI workflow APIs.

Usage:
    # Set environment variables
    export RUNNINGHUB_API_KEY="your_runninghub_api_key"
    export OPENROUTER_API_KEY="your_openrouter_api_key"  # or OPENAI_API_KEY

    # Run with default idea
    python main_idea2video.py

    # Edit the idea, user_requirement, and style below to customize.
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipelines.idea2video_pipeline import Idea2VideoPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# ============================================================
# SET YOUR OWN IDEA, USER REQUIREMENT, AND STYLE HERE
# ============================================================
idea = \
    """
A lone astronaut stands on the edge of a massive crater on the Moon,
looking down at the vast, silent expanse. In the distance, Earth rises
above the lunar horizon, glowing blue and white. The astronaut slowly
raises a hand in a peaceful gesture, then begins to walk along the
crater's rim, their boots kicking up fine lunar dust with each step.
"""

user_requirement = \
    """
For adults, do not exceed 3 scenes. Each scene should be no more than 5 shots.
"""

style = "Cinematic, realistic, dramatic lighting"
# ============================================================


async def main():
    logging.info("Starting ViMax-RH Idea-to-Video Pipeline")
    logging.info(f"Idea: {idea.strip()[:80]}...")
    logging.info(f"Style: {style}")

    pipeline = Idea2VideoPipeline.init_from_config(
        config_path="configs/idea2video.yaml")

    final_video_path = await pipeline(
        idea=idea,
        user_requirement=user_requirement,
        style=style,
    )

    print(f"\n{'='*60}")
    print(f"  Pipeline Complete!")
    print(f"  Final video: {final_video_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
