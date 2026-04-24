from pydantic import BaseModel, ConfigDict


class MetaAdsConfig(BaseModel):
    model_config = ConfigDict(frozen=False)

    access_token: str
    api_version: str = "v21.0"
    app_id: str | None = None
    app_secret: str | None = None
