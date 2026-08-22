import os
import copy
from typing import Dict, Any


def resolve_chat_model_config(init_args: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve chat model config, filling in defaults from env vars."""
    config = copy.deepcopy(init_args)

    # Fill in api_key from env if empty
    if not config.get("api_key"):
        config["api_key"] = os.getenv("OPENROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")

    # Fill in base_url from env if empty
    if not config.get("base_url"):
        config["base_url"] = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    # Ensure model_provider is set
    if not config.get("model_provider"):
        config["model_provider"] = "openai"

    return config
