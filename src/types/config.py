from pydantic import BaseModel, Field


class MetaAdsConfig(BaseModel):
    access_token: str
    api_version: str = "v21.0"
    app_id: str | None = None
    app_secret: str | None = None


class ServerConfig(BaseModel):
    debug: bool = False
    log_level: str = Field(default="info", pattern="^(error|warn|info|debug)$")
