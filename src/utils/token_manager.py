import http.server
import json
import os
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

from src.config.settings import ENV_PATH
from src.utils.logger import logger

REDIRECT_URI = "http://localhost:8888/callback"
REDIRECT_PORT = 8888
SCOPES = "ads_management,ads_read,business_management"
OAUTH_TIMEOUT = 120


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

    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text("\n".join(lines) + "\n")


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    auth_code: str | None = None
    error: str | None = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            _CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Authentication successful!</h2>"
                b"<p>You can close this tab and return to the terminal.</p>"
                b"</body></html>"
            )
        elif "error" in params:
            _CallbackHandler.error = params.get("error_description", params["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h2>Error: {_CallbackHandler.error}</h2></body></html>".encode())
        else:
            self.send_response(404)
            self.end_headers()

        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format, *args):
        pass


def _exchange_code_for_token(app_id: str, app_secret: str, code: str, api_version: str) -> str:
    params = urllib.parse.urlencode({
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    })
    url = f"https://graph.facebook.com/{api_version}/oauth/access_token?{params}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["access_token"]


def _exchange_for_long_lived_token(app_id: str, app_secret: str, short_token: str, api_version: str) -> str:
    params = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })
    url = f"https://graph.facebook.com/{api_version}/oauth/access_token?{params}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["access_token"]


def run_oauth_flow(app_id: str, app_secret: str, api_version: str) -> str | None:
    _CallbackHandler.auth_code = None
    _CallbackHandler.error = None

    auth_url = (
        f"https://www.facebook.com/{api_version}/dialog/oauth?"
        f"client_id={app_id}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={SCOPES}"
        f"&response_type=code"
    )

    try:
        server = http.server.HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
        server.timeout = OAUTH_TIMEOUT
    except OSError as e:
        logger.error(f"Could not start OAuth callback server on port {REDIRECT_PORT}: {e}")
        return None

    logger.info("Opening browser for Meta OAuth authentication...")
    print(f"Opening browser for authentication...", file=sys.stderr)
    print(f"If browser doesn't open, visit: {auth_url}", file=sys.stderr)

    webbrowser.open(auth_url)
    server.handle_request()
    server.server_close()

    if _CallbackHandler.error:
        logger.error(f"OAuth failed: {_CallbackHandler.error}")
        return None

    if not _CallbackHandler.auth_code:
        logger.error("No authorization code received (timeout or user closed browser)")
        return None

    try:
        short_token = _exchange_code_for_token(app_id, app_secret, _CallbackHandler.auth_code, api_version)
        long_token = _exchange_for_long_lived_token(app_id, app_secret, short_token, api_version)
        return long_token
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return None


def ensure_valid_token(access_token: str, app_id: str | None, app_secret: str | None, api_version: str) -> str | None:
    # Step 1: Check if current token works
    user = validate_token(access_token, api_version)

    if user:
        logger.info(f"Token valid for user: {user.get('name', 'Unknown')}")

        # Step 2: Silently refresh for another 60 days if possible
        if app_id and app_secret:
            new_token = refresh_token(access_token, app_id, app_secret, api_version)
            if new_token and new_token != access_token:
                save_token_to_env(new_token)
                os.environ["META_ACCESS_TOKEN"] = new_token
                logger.info("Token refreshed for another 60 days")
                return new_token

        return access_token

    logger.warning("Token is invalid or expired")

    # Step 3: Try silent refresh with expired token
    if app_id and app_secret:
        new_token = refresh_token(access_token, app_id, app_secret, api_version)
        if new_token:
            verify = validate_token(new_token, api_version)
            if verify:
                save_token_to_env(new_token)
                os.environ["META_ACCESS_TOKEN"] = new_token
                logger.info(f"Token recovered for user: {verify.get('name', 'Unknown')}")
                return new_token

    # Step 4: Full OAuth browser flow as last resort
    if app_id and app_secret:
        logger.info("Attempting OAuth browser flow...")
        new_token = run_oauth_flow(app_id, app_secret, api_version)
        if new_token:
            verify = validate_token(new_token, api_version)
            if verify:
                save_token_to_env(new_token)
                os.environ["META_ACCESS_TOKEN"] = new_token
                logger.info(f"Authenticated via OAuth as: {verify.get('name', 'Unknown')}")
                return new_token

    logger.error("Authentication failed. Ensure META_APP_ID and META_APP_SECRET are set in .env")
    return None
