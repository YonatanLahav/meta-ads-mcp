from pydantic import BaseModel


class MetaAdsConfig(BaseModel):
    access_token: str
    api_version: str = "v21.0"
    app_id: str | None = None
    app_secret: str | None = None
