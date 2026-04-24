import os
from pathlib import Path
from dotenv import load_dotenv
from src.types.config import MetaAdsConfig, ServerConfig


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "pyproject.toml").exists() or (current / ".env").exists():
            return current
        current = current.parent
    return Path.cwd()


ENV_PATH = _find_project_root() / ".env"
load_dotenv(ENV_PATH, override=False)


def load_meta_config() -> MetaAdsConfig | None:
    token = os.getenv("META_ACCESS_TOKEN")
    if not token:
        return None
    return MetaAdsConfig(
        access_token=token,
        api_version=os.getenv("META_API_VERSION", "v21.0"),
        app_id=os.getenv("META_APP_ID"),
        app_secret=os.getenv("META_APP_SECRET"),
    )


def load_server_config() -> ServerConfig:
    return ServerConfig(
        debug=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info"),
    )
