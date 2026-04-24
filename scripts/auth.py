"""
Meta OAuth Authentication Script

Run this manually to get a long-lived access token (valid for 60 days).
The token is saved to .env automatically.

Usage:
    python scripts/auth.py

Prerequisites:
    - META_APP_ID and META_APP_SECRET set in .env
    - Your app's Valid OAuth Redirect URIs must include: http://localhost:8888/callback
      (Set this in Meta App Dashboard > Facebook Login > Settings)

Note: The MCP server runs this flow automatically on startup when the token
is invalid. This script is for manual authentication when needed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import load_meta_config
from src.utils.token_manager import run_oauth_flow, validate_token, save_token_to_env


def main():
    config = load_meta_config()
    app_id = config.app_id if config else None
    app_secret = config.app_secret if config else None
    api_version = config.api_version if config else "v21.0"

    if not app_id or not app_secret:
        print("Error: META_APP_ID and META_APP_SECRET must be set in .env")
        print()
        print("To get these:")
        print("  1. Go to https://developers.facebook.com/apps/")
        print("  2. Select your app (or create one)")
        print("  3. Go to App Settings > Basic")
        print("  4. Copy App ID and App Secret into .env")
        sys.exit(1)

    print("Starting OAuth flow...")
    token = run_oauth_flow(app_id, app_secret, api_version)

    if not token:
        print("Authentication failed.")
        sys.exit(1)

    user = validate_token(token, api_version)
    if user:
        print(f"Authenticated as: {user.get('name', 'Unknown')} (ID: {user.get('id')})")

    save_token_to_env(token)
    print(f"Long-lived token saved to .env")
    print("This token is valid for 60 days.")
    print("The server will refresh it automatically on startup.")


if __name__ == "__main__":
    main()
