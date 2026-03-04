# meetalfred-mcp

<!-- mcp-name: io.github.cphoskins/meetalfred-mcp -->

MCP server for [MeetAlfred](https://meetalfred.com) — LinkedIn automation campaign monitoring, lead management, and reply tracking.

## Features

- **Campaign monitoring** — list campaigns and their status
- **Lead management** — fetch leads with filters, add new leads to campaigns
- **Reply tracking** — pull replies from leads for review and follow-up
- **Activity feed** — review recent account actions
- **Team visibility** — list team members and their connections
- **White-label support** — configurable base URL for custom instances

## Installation

```bash
pip install meetalfred-mcp
```

Or install from source:

```bash
git clone https://github.com/cphoskins/meetalfred-mcp.git
cd meetalfred-mcp
pip install -e .
```

## Configuration

### Get your API key

1. Log in to MeetAlfred
2. Go to **Settings > Integrations > Webhooks**
3. Generate an API key

### Claude Code

Add to your `.claude/settings.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "meetalfred": {
      "command": "meetalfred-mcp",
      "env": {
        "MEETALFRED_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### White-label instances

If you're using a white-label MeetAlfred instance, set the base URL:

```json
{
  "mcpServers": {
    "meetalfred": {
      "command": "meetalfred-mcp",
      "env": {
        "MEETALFRED_API_KEY": "your-api-key-here",
        "MEETALFRED_BASE_URL": "https://your-instance.com/api/v1"
      }
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meetalfred": {
      "command": "python",
      "args": ["-m", "meetalfred_mcp.server"],
      "env": {
        "MEETALFRED_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `get_campaigns` | List all campaigns with IDs, names, and status |
| `get_leads` | Fetch leads, optionally filtered by campaign and status |
| `add_lead` | Add a new lead to a campaign (LinkedIn URL or email) |
| `get_replies` | Get replies received from leads |
| `get_connections` | Get connection data between leads and team members |
| `get_team_members` | List team members |
| `get_member_connections` | Get connections for a specific team member |
| `get_last_actions` | Get recent account activity |
| `get_me` | Get current user profile |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MEETALFRED_API_KEY` | Yes | API key from Settings > Integrations > Webhooks |
| `MEETALFRED_BASE_URL` | No | Override for white-label instances (default: `https://api.meetalfred.com/api/v1`) |

## Development

```bash
git clone https://github.com/cphoskins/meetalfred-mcp.git
cd meetalfred-mcp
pip install -e ".[dev]"
pytest tests/
```

## License

MIT
