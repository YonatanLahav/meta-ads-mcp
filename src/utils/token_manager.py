import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from src.utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def validate_token(access_token: str, api_version: str) -> dict | None:
    url = f"https://graph.facebook.com/{api_version}/me?access_token={urllib.parse.quote(access_token)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None


def refresh_token(access_token: str, app_id: str, app_secret: str, api_version: str) -> str | None:
    params = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": access_token,
    })
    url = f"https://graph.facebook.com/{api_version}/oauth/access_token?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("access_token")
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        return None


def save_token_to_env(token: str):
    lines = []
    replaced = False

    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.strip().startswith("META_ACCESS_TOKEN="):
                lines.append(f"META_ACCESS_TOKEN={token}")
                replaced = True
            else:
                lines.append(line)

    if not replaced:
        lines.append(f"META_ACCESS_TOKEN={token}")

    ENV_PATH.write_text("\n".join(lines) + "\n")


def ensure_valid_token(access_token: str, app_id: str | None, app_secret: str | None, api_version: str) -> str | None:
    user = validate_token(access_token, api_version)

    if user:
        logger.info(f"Token valid for user: {user.get('name', 'Unknown')}")

        if app_id and app_secret:
            new_token = refresh_token(access_token, app_id, app_secret, api_version)
            if new_token and new_token != access_token:
                save_token_to_env(new_token)
                os.environ["META_ACCESS_TOKEN"] = new_token
                logger.info("Token refreshed for another 60 days")
                return new_token

        return access_token

    logger.warning("Token is invalid or expired")

    if app_id and app_secret:
        new_token = refresh_token(access_token, app_id, app_secret, api_version)
        if new_token:
            verify = validate_token(new_token, api_version)
            if verify:
                save_token_to_env(new_token)
                os.environ["META_ACCESS_TOKEN"] = new_token
                logger.info(f"Token recovered for user: {verify.get('name', 'Unknown')}")
                return new_token

    logger.error("Could not refresh token. Run: python scripts/auth.py")
    return None
