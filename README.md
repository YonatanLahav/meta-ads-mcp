# Meta Ads MCP Server (Python)

An MCP (Model Context Protocol) server that lets AI assistants like Claude manage Meta (Facebook/Instagram) ad campaigns programmatically.

## Features

- **Campaign management** — create, read, update, delete campaigns
- **Automatic retry** with exponential backoff for transient errors
- **Structured error handling** with Meta API error code mapping
- **JSON logging** to stderr (won't interfere with MCP stdio transport)

## Prerequisites

- Python 3.11+
- A Meta Developer account with a registered app
- A Meta access token with `ads_management`, `ads_read`, and `business_management` permissions

## Setup

### 1. Clone and create virtual environment

```bash
cd meta-ads-mcp-server-python
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Meta App credentials:

```
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_API_VERSION=v21.0
```

To get App ID and App Secret:
1. Go to [Meta Developer Apps](https://developers.facebook.com/apps/)
2. Select your app (or create one)
3. Go to **App Settings > Basic**
4. Copy the App ID and App Secret into `.env`

Make sure your app has **Facebook Login** enabled and `http://localhost:8888/callback` is listed in **Valid OAuth Redirect URIs** (under Facebook Login > Settings).

### 4. Authenticate via OAuth

```bash
python scripts/auth.py
```

This will:
1. Open your browser to Facebook's login/permissions page
2. After you approve, catch the callback on `localhost:8888`
3. Exchange the code for a **long-lived token** (valid 60 days)
4. Save the token to `.env` automatically

Run this again when the token expires.

**Alternative (manual token):** If you prefer, you can skip the OAuth script and paste a token directly into `.env` as `META_ACCESS_TOKEN=your_token`. You can generate one at the [Graph API Explorer](https://developers.facebook.com/tools/explorer/).

### 5. Configure for Claude Desktop

Add this to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "/path/to/meta-ads-mcp-server-python/venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/meta-ads-mcp-server-python",
      "env": {
        "META_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

Replace `/path/to/` with the actual path to the project directory.

Claude Desktop will start and stop the server automatically — no need to keep it running manually.

## Project Structure

```
src/
├── server.py              # Entry point — creates MCP server, registers tools
├── config/
│   └── settings.py        # Loads config from environment variables
├── types/
│   └── config.py          # Pydantic models (MetaAdsConfig)
├── services/
│   ├── base.py            # Base service — SDK init, pagination, retry wrapper
│   ├── account.py         # Ad account operations
│   ├── campaign.py        # Campaign CRUD operations
│   └── insights.py        # Performance insights and analytics
├── tools/
│   ├── helpers.py         # Shared response formatting
│   ├── account.py         # Account tool definitions + handlers
│   ├── campaign.py        # Campaign tool definitions + handlers
│   └── insights.py        # Insights tool definitions + handlers
└── utils/
    ├── logger.py          # Structured JSON logging to stderr
    ├── error_handler.py   # Meta API error classification & mapping
    ├── retry.py           # Exponential backoff with jitter
    └── token_manager.py   # Token validation, refresh, and OAuth flow
```

## Architecture

```
Claude Desktop (MCP client)
        │
        │ stdio (stdin/stdout)
        ▼
    server.py  ──  routes tool calls
        │
        ▼
    tools/     ──  schema definitions + argument mapping
        │
        ▼
    services/  ──  Meta Marketing API calls via facebook-business SDK
        │
        ▼
    utils/     ──  retry, error handling, logging
```

## Available Tools

| Domain     | Tools                                                   |
|------------|---------------------------------------------------------|
| Accounts   | list ad accounts                                        |
| Campaigns  | list, get, create, update, delete                       |
| Insights   | account insights, campaign insights, ad set insights, ad insights |

Insights tools support date presets (`last_7d`, `last_30d`, etc.), custom date ranges, and breakdowns by age, gender, country, device, and placement.

### Planned Features

Additional tool domains are planned for future releases:
- Ad set, ad, and creative management
- Audience management
- Budget optimization tools
- Batch operations

## Development

```bash
source venv/bin/activate

# Run tests
pytest

# Lint
ruff check src/

# Format
ruff format src/
```

## License

MIT
