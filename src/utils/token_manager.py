import html
import http.server
import json
import os
import stat
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


def _graph_get(url: str, access_token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _graph_post(url: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def validate_token(access_token: str, api_version: str) -> dict | None:
    try:
        return _graph_get(f"https://graph.facebook.com/{api_version}/me", access_token)
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None


def refresh_token(access_token: str, app_id: str, app_secret: str, api_version: str) -> str | None:
    try:
        data = _graph_post(
            f"https://graph.facebook.com/{api_version}/oauth/access_token",
            {
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": access_token,
            },
        )
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
    os.chmod(ENV_PATH, stat.S_IRUSR | stat.S_IWUSR)


def _persist_token(token: str):
    save_token_to_env(token)
    os.environ["META_ACCESS_TOKEN"] = token


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
            safe_error = html.escape(_CallbackHandler.error)
            self.wfile.write(f"<html><body><h2>Authentication failed: {safe_error}</h2></body></html>".encode())
        else:
            self.send_response(404)
            self.end_headers()

        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format, *args):
        pass


def _exchange_code_for_token(app_id: str, app_secret: str, code: str, api_version: str) -> str:
    data = _graph_post(
        f"https://graph.facebook.com/{api_version}/oauth/access_token",
        {
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
    )
    return data["access_token"]


def _exchange_for_long_lived_token(app_id: str, app_secret: str, short_token: str, api_version: str) -> str:
    data = _graph_post(
        f"https://graph.facebook.com/{api_version}/oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
    )
    return data["access_token"]


def run_oauth_flow(app_id: str, app_secret: str, api_version: str) -> str | None:
    _CallbackHandler.auth_code = None
    _CallbackHandler.error = None

    auth_url = (
        f"https://www.facebook.com/{api_version}/dialog/oauth?"
        f"client_id={urllib.parse.quote(app_id)}"
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
    print("Opening browser for authentication...", file=sys.stderr)
    print(f"If browser doesn't open, visit: {auth_url}", file=sys.stderr)

    webbrowser.open(auth_url)
    server.handle_request()
    server.server_close()

    if _CallbackHandler.error:
        logger.error("OAuth authentication failed")
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
    user = validate_token(access_token, api_version)

    if user:
        logger.info("Token validated successfully")

        if app_id and app_secret:
            new_token = refresh_token(access_token, app_id, app_secret, api_version)
            if new_token and new_token != access_token:
                _persist_token(new_token)
                logger.info("Token refreshed for another 60 days")
                return new_token

        return access_token

    logger.warning("Token is invalid or expired")

    if app_id and app_secret:
        new_token = refresh_token(access_token, app_id, app_secret, api_version)
        if new_token:
            if validate_token(new_token, api_version):
                _persist_token(new_token)
                logger.info("Token recovered via silent refresh")
                return new_token

    if app_id and app_secret:
        logger.info("Attempting OAuth browser flow...")
        new_token = run_oauth_flow(app_id, app_secret, api_version)
        if new_token:
            if validate_token(new_token, api_version):
                _persist_token(new_token)
                logger.info("Authenticated via OAuth")
                return new_token

    logger.error("Authentication failed. Ensure META_APP_ID and META_APP_SECRET are set in .env")
    return None
