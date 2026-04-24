# Meta Ads MCP Server

An MCP server that gives Claude direct access to the Meta (Facebook/Instagram) Marketing API. Manage campaigns, analyze performance, and get insights — all through natural conversation.

## What You Can Do

**Campaign Management** — create, update, pause, and delete campaigns directly from Claude.

**Performance Analytics** — pull spend, impressions, clicks, conversions, CPA, ROAS, and more at any level (account, campaign, ad set, ad) with breakdowns by age, gender, country, device, and placement.

**Example prompts:**
- "Show me all active campaigns and their spend this week"
- "Break down campaign X performance by country for the last 30 days"
- "Pause all campaigns spending more than $100/day with CPA above $50"
- "Compare last 7 days vs previous 7 days for my top campaigns"

## Available Tools

| Tool | Description |
|------|-------------|
| `list_ad_accounts` | Discover accessible ad accounts |
| `list_campaigns` | List campaigns with optional status filter |
| `get_campaign` | Get campaign details |
| `create_campaign` | Create a new campaign |
| `update_campaign` | Update campaign name, status, or budget |
| `delete_campaign` | Archive a campaign |
| `get_account_insights` | Account performance by campaign/ad set/ad level |
| `get_campaign_insights` | Campaign performance with optional breakdowns |
| `get_adset_insights` | Ad set performance with optional breakdowns |
| `get_ad_insights` | Ad performance with optional breakdowns |

### Insights Options

All insight tools support:
- **Date presets**: `today`, `yesterday`, `last_7d`, `last_14d`, `last_30d`, `last_90d`, `this_month`, `last_month`
- **Custom date range**: `{"since": "2024-01-01", "until": "2024-01-31"}`
- **Breakdowns**: `age`, `gender`, `country`, `device_platform`, `publisher_platform`, `platform_position`

## Quick Start

### 1. Prerequisites

- Python 3.11+
- A [Meta Developer](https://developers.facebook.com/apps/) app with **Facebook Login** enabled
- `http://localhost:8888/callback` added to your app's **Valid OAuth Redirect URIs**

### 2. Install

```bash
git clone https://github.com/YonatanLahav/meta-ads-mcp.git
cd meta-ads-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
```

Get these from [Meta Developer Apps](https://developers.facebook.com/apps/) → your app → **App Settings > Basic**.

### 4. Authenticate

```bash
python scripts/auth.py
```

Opens your browser for OAuth. After approval, a 60-day token is saved to `.env` automatically. The server refreshes it silently on each startup.

### 5. Add to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "/path/to/meta-ads-mcp/venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/meta-ads-mcp"
    }
  }
}
```

Replace `/path/to/` with the actual project path. Restart Claude Desktop.

## How Auth Works

1. **On startup** — validates your token and silently refreshes it for another 60 days
2. **If expired** — tries silent refresh first; if that fails and you're running interactively, opens browser for OAuth automatically
3. **If running as daemon** (Claude Desktop) — logs an error directing you to run `python scripts/auth.py` manually

You should never need to re-authenticate unless 60+ days pass without starting the server, or you revoke the token.

## Project Structure

```
src/
├── server.py              # Entry point — MCP server, tool routing
├── config/
│   └── settings.py        # Environment config loading
├── types/
│   └── config.py          # Pydantic config models
├── services/
│   ├── base.py            # Base service — SDK init, pagination, retry
│   ├── account.py         # Ad account operations
│   ├── campaign.py        # Campaign CRUD
│   └── insights.py        # Performance insights
├── tools/
│   ├── helpers.py         # Shared response formatting
│   ├── account.py         # Account tool schemas + handlers
│   ├── campaign.py        # Campaign tool schemas + handlers
│   └── insights.py        # Insights tool schemas + handlers
└── utils/
    ├── logger.py          # JSON logging to stderr
    ├── error_handler.py   # Meta API error mapping
    ├── retry.py           # Exponential backoff with jitter
    └── token_manager.py   # Token validation, refresh, OAuth flow
```

## Development

```bash
source venv/bin/activate
pytest                # run tests
ruff check src/       # lint
ruff format src/      # format
```

## Planned Features

- Ad set, ad, and creative management
- Audience tools (custom audiences, targeting suggestions)
- Budget optimization and pacing
- Batch operations

## License

MIT
