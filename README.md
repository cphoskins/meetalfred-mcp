# meetalfred-mcp

<!-- mcp-name: io.github.cphoskins/meetalfred-mcp -->

MCP server for [MeetAlfred](https://meetalfred.com) — LinkedIn automation campaign monitoring, lead management, reply tracking, messaging, tag management, and campaign CRUD.

## Features

- **Campaign monitoring** — list, filter, pause/resume, rename, clone, archive campaigns
- **Lead management** — fetch leads, add to campaigns, tag, exclude, return to campaign
- **Reply tracking** — pull replies, view conversation threads, send messages
- **Tag management** — full CRUD on tags (create, list, update, delete)
- **Lead tagging** — add/set tags on individual leads or in bulk
- **Activity feed** — review recent account actions across all channels
- **Notifications** — check unread count
- **Team visibility** — list team members and their connections
- **User profile** — get current authenticated user info
- **White-label support** — configurable base URLs for custom instances

## Dual API Architecture

This server uses **two MeetAlfred API layers**:

| Layer | Auth | Required | Capabilities |
|-------|------|----------|-------------|
| **Webhook API** | `MEETALFRED_API_KEY` | Yes | Campaigns, leads, replies, connections, activity (read-heavy) |
| **Internal API** | `MEETALFRED_JWT_TOKEN` | No | Tags CRUD, campaign management, messaging, lead ops, notifications |

The webhook API provides core read operations. The internal API (optional) enables full CRUD, messaging, and richer data. Both work simultaneously.

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

### Get your JWT token (optional, for internal API)

1. Log in to MeetAlfred in your browser
2. Open DevTools > Application > Cookies
3. Copy the `token` cookie value

### Claude Code

Add to your `.claude/settings.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "meetalfred": {
      "command": "meetalfred-mcp",
      "env": {
        "MEETALFRED_API_KEY": "your-api-key-here",
        "MEETALFRED_JWT_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

### White-label instances

If you're using a white-label MeetAlfred instance, set the base URLs:

```json
{
  "mcpServers": {
    "meetalfred": {
      "command": "meetalfred-mcp",
      "env": {
        "MEETALFRED_API_KEY": "your-api-key-here",
        "MEETALFRED_JWT_TOKEN": "your-jwt-token-here",
        "MEETALFRED_BASE_URL": "https://api.your-instance.com/api/integrations/webhook",
        "MEETALFRED_API_BASE_URL": "https://api.your-instance.com/api/v1"
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
        "MEETALFRED_API_KEY": "your-api-key-here",
        "MEETALFRED_JWT_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

## Tools

### Webhook API (requires `MEETALFRED_API_KEY`)

| Tool | Description |
|------|-------------|
| `get_campaigns` | List campaigns by type (active, draft, archived, all) |
| `get_leads` | Fetch leads with campaign and person details |
| `add_lead` | Add a new lead to a campaign (LinkedIn URL required) |
| `get_replies` | Get reply messages from leads across campaigns |
| `get_connections` | Get LinkedIn connections with full profile data |
| `get_team_members` | List team members (requires team owner access) |
| `get_member_connections` | Get connections across team members |
| `get_last_actions` | Get recent activity by type (invites, accepted, messages, replies, etc.) |

### Internal API — Tags (requires `MEETALFRED_JWT_TOKEN`)

| Tool | Description |
|------|-------------|
| `get_all_tags` | Get all tags (no pagination) |
| `list_tags` | List tags with pagination and sorting |
| `create_tag` | Create a new tag |
| `update_tag` | Rename an existing tag |
| `delete_tag` | Delete a tag |

### Internal API — Campaigns (requires `MEETALFRED_JWT_TOKEN`)

| Tool | Description |
|------|-------------|
| `list_campaigns_detailed` | List campaigns with full details, stats, and filtering |
| `get_campaign` | Get full details of a single campaign |
| `get_campaign_counts` | Get campaign counts by status |
| `get_campaigns_grouped` | Get all campaigns grouped by category |
| `update_campaign` | Update campaign fields (name, status) |
| `delete_campaign` | Delete a campaign |
| `pause_campaign` | Pause a running campaign |
| `resume_campaign` | Resume a paused campaign |
| `rename_campaign` | Rename a campaign |
| `clone_campaign` | Clone (duplicate) a campaign |
| `archive_campaign` | Archive a campaign |

### Internal API — Messaging (requires `MEETALFRED_JWT_TOKEN`)

| Tool | Description |
|------|-------------|
| `list_replies_detailed` | List replies with full details and sorting |
| `get_conversation_messages` | Get messages in a conversation thread |
| `send_message` | Send a message in a conversation (reply to a lead) |

### Internal API — Lead Management (requires `MEETALFRED_JWT_TOKEN`)

| Tool | Description |
|------|-------------|
| `get_campaign_leads` | List leads in a campaign with status filtering |
| `get_lead_statuses` | Get lead status counts for a campaign |
| `return_lead_to_campaign` | Return leads to a campaign sequence |
| `add_tags_to_leads` | Add tags to one or more leads |
| `exclude_leads` | Exclude or un-exclude leads from campaigns |

### Internal API — Other (requires `MEETALFRED_JWT_TOKEN`)

| Tool | Description |
|------|-------------|
| `get_current_user` | Get the current authenticated user's profile |
| `get_unread_notification_count` | Get count of unread notifications |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MEETALFRED_API_KEY` | Yes | API key from Settings > Integrations > Webhooks |
| `MEETALFRED_JWT_TOKEN` | No | JWT token for internal API (enables tags, campaign CRUD, messaging) |
| `MEETALFRED_BASE_URL` | No | Override webhook API base URL for white-label instances |
| `MEETALFRED_API_BASE_URL` | No | Override internal API base URL for white-label instances |

## Common Workflows

### Reply to a lead

```
1. list_replies_detailed() → find reply with conversationUrn
2. get_conversation_messages(conversationUrn) → read conversation history
3. send_message(conversationUrn, "Your reply text")
```

### Return a lead to a campaign

```
1. get_campaign_leads(campaignId, "replied") → find lead entityUrn
2. return_lead_to_campaign([entityUrn], campaignId)
```

### Tag leads from a campaign

```
1. get_all_tags() → find or create tag IDs
2. get_campaign_leads(campaignId) → get entity URNs
3. add_tags_to_leads([entityUrns], [tagIds])
```

## Development

```bash
git clone https://github.com/cphoskins/meetalfred-mcp.git
cd meetalfred-mcp
pip install -e ".[dev]"
pytest tests/
```

## License

MIT
