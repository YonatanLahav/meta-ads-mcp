import os
from pathlib import Path
from dotenv import load_dotenv
from src.types.config import MetaAdsConfig, ServerConfig

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_PATH)


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
