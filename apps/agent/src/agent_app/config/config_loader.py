import json
import os
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from agent_app.config.config_model import ConfigModel
from agent_app.config.environment import load_icarus_environment, repository_root

load_icarus_environment()


def _settings_resource() -> Traversable | Path:
    root = repository_root()
    if root is not None:
        return root / "apps" / "agent" / "settings.json"
    return files("agent_app.resources").joinpath("default_settings.json")


def get_config(settings_path: str | Path | None = None) -> ConfigModel:
    explicit = settings_path or os.getenv("ICARUS_SETTINGS_PATH")
    resource = Path(explicit).expanduser() if explicit is not None else _settings_resource()
    with resource.open("r", encoding="utf-8") as file:
        data = json.load(file)
    data["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    data["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
    data["icarus_data_dir"] = os.getenv("ICARUS_DATA_DIR") or None
    return ConfigModel(**data)
