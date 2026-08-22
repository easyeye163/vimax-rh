"""Factory for creating rendering backends from YAML config.

The config file specifies a ``class_path`` (dotted module + class name)
and ``init_args`` for each backend.  This module dynamically imports
and instantiates them.

Example config:
    image_generator:
      class_path: tools.ImageGeneratorRunningHub
      init_args:
        api_key: ...
    video_generator:
      class_path: tools.VideoGeneratorRunningHub
      init_args:
        api_key: ...
"""

import importlib
import logging
from typing import Any, Dict, Optional

from utils.rate_limiter import RateLimiter


def _import_class(dotted_path: str):
    """Import a class from a dotted path like 'tools.ImageGeneratorRunningHub'."""
    module_path, _, class_name = dotted_path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _build_rate_limiter(config_section: dict) -> Optional[RateLimiter]:
    """Create a RateLimiter if the config section has rate limit settings."""
    rpm = config_section.get("max_requests_per_minute")
    rpd = config_section.get("max_requests_per_day")
    if rpm is None and rpd is None:
        return None
    return RateLimiter(max_requests_per_minute=rpm, max_requests_per_day=rpd)


def _create_backend(config_section: dict):
    """Instantiate a backend from a config section."""
    class_path = config_section["class_path"]
    init_args: Dict[str, Any] = dict(config_section.get("init_args", {}))

    # Inject rate limiter if configured
    rate_limiter = _build_rate_limiter(config_section)
    if rate_limiter is not None:
        init_args["rate_limiter"] = rate_limiter

    cls = _import_class(class_path)
    logging.info(f"Creating backend: {class_path}")
    return cls(**init_args)


class RenderBackend:
    """Holds the instantiated image and video generators."""

    def __init__(self, image_generator, video_generator):
        self.image_generator = image_generator
        self.video_generator = video_generator

    @classmethod
    def from_config(cls, config: dict) -> "RenderBackend":
        image_gen = _create_backend(config["image_generator"])
        video_gen = _create_backend(config["video_generator"])
        return cls(image_generator=image_gen, video_generator=video_gen)
