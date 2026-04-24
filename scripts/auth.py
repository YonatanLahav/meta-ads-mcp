"""
Meta OAuth Authentication Script

Run this once to get a long-lived access token (valid for 60 days).
The token is saved to .env automatically.

Usage:
    python scripts/auth.py

Prerequisites:
    - META_APP_ID and META_APP_SECRET set in .env
    - Your app's Valid OAuth Redirect URIs must include: http://localhost:8888/callback
      (Set this in Meta App Dashboard > Facebook Login > Settings)
"""

import http.server
import json
import os
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

REDIRECT_URI = "http://localhost:8888/callback"
REDIRECT_PORT = 8888
SCOPES = "ads_management,ads_read,business_management"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


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


def exchange_code_for_token(app_id: str, app_secret: str, code: str) -> str:
    params = urllib.parse.urlencode({
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    })
    url = f"https://graph.facebook.com/v21.0/oauth/access_token?{params}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    return data["access_token"]


def exchange_for_long_lived_token(app_id: str, app_secret: str, short_token: str) -> str:
    params = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })
    url = f"https://graph.facebook.com/v21.0/oauth/access_token?{params}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    return data["access_token"]


def verify_token(token: str) -> dict:
    url = f"https://graph.facebook.com/v21.0/me?access_token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    auth_code: str | None = None
    error: str | None = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authentication successful!</h2>"
                             b"<p>You can close this tab and return to the terminal.</p>"
                             b"</body></html>")
        elif "error" in params:
            CallbackHandler.error = params.get("error_description", params["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h2>Error: {CallbackHandler.error}</h2></body></html>".encode())
        else:
            self.send_response(404)
            self.end_headers()

        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format, *args):
        pass


def main():
    env = load_env()
    app_id = env.get("META_APP_ID") or os.getenv("META_APP_ID")
    app_secret = env.get("META_APP_SECRET") or os.getenv("META_APP_SECRET")

    if not app_id or not app_secret:
        print("Error: META_APP_ID and META_APP_SECRET must be set in .env")
        print()
        print("To get these:")
        print("  1. Go to https://developers.facebook.com/apps/")
        print("  2. Select your app (or create one)")
        print("  3. Go to App Settings > Basic")
        print("  4. Copy App ID and App Secret into .env")
        sys.exit(1)

    auth_url = (
        f"https://www.facebook.com/v21.0/dialog/oauth?"
        f"client_id={app_id}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={SCOPES}"
        f"&response_type=code"
    )

    print("Starting OAuth flow...")
    print(f"Opening browser for authentication...")
    print()

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)

    webbrowser.open(auth_url)

    print(f"Waiting for callback on {REDIRECT_URI} ...")
    print("(If the browser didn't open, visit this URL manually:)")
    print(f"  {auth_url}")
    print()

    server.handle_request()
    server.server_close()

    if CallbackHandler.error:
        print(f"Authentication failed: {CallbackHandler.error}")
        sys.exit(1)

    if not CallbackHandler.auth_code:
        print("No authorization code received.")
        sys.exit(1)

    print("Got authorization code. Exchanging for access token...")

    short_token = exchange_code_for_token(app_id, app_secret, CallbackHandler.auth_code)
    print("Got short-lived token. Exchanging for long-lived token...")

    long_token = exchange_for_long_lived_token(app_id, app_secret, short_token)

    print("Verifying token...")
    user_info = verify_token(long_token)
    print(f"Authenticated as: {user_info.get('name', 'Unknown')} (ID: {user_info.get('id')})")

    save_token_to_env(long_token)
    print()
    print(f"Long-lived token saved to {ENV_PATH}")
    print("This token is valid for 60 days.")
    print("Run this script again when it expires.")


if __name__ == "__main__":
    main()
