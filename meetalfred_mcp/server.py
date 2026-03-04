"""MeetAlfred MCP Server — campaign monitoring, lead management, and reply tracking.

Transport: stdio
Auth: MEETALFRED_API_KEY environment variable (webhook key from Settings > Integrations > Webhooks)
Optional: MEETALFRED_BASE_URL for white-label instances
"""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from .client import MeetAlfredClient

mcp = FastMCP(
    "meetalfred",
    instructions=(
        "MeetAlfred MCP server for LinkedIn automation campaign monitoring. "
        "Pull campaign data, track replies, manage leads, and review activity. "
        "Use get_campaigns first to find campaign IDs for filtering other tools. "
        "Pages start at 0 (not 1)."
    ),
)

_client: MeetAlfredClient | None = None


def _get_client() -> MeetAlfredClient:
    """Lazy-initialize the MeetAlfred client."""
    global _client
    if _client is None:
        _client = MeetAlfredClient(
            api_key=os.environ.get("MEETALFRED_API_KEY", ""),
            base_url=os.environ.get("MEETALFRED_BASE_URL", ""),
        )
    return _client


# ------------------------------------------------------------------
# Campaigns
# ------------------------------------------------------------------


@mcp.tool()
def get_campaigns(campaign_type: str = "active") -> str:
    """List MeetAlfred campaigns with their IDs, names, and status.

    Use campaign IDs from this response to filter leads and other tools.

    Args:
        campaign_type: Filter by type — 'active', 'draft', 'archived', or 'all'.
    """
    try:
        result = _get_client().get_campaigns(campaign_type=campaign_type)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Leads
# ------------------------------------------------------------------


@mcp.tool()
def get_leads(
    campaign_id: int = 0,
    page: int = 0,
    per_page: int = 25,
) -> str:
    """Fetch leads with campaign and person details.

    Returns an 'actions' array with campaign info and person details
    (name, title, company, LinkedIn URL, email, etc.).

    Args:
        campaign_id: Filter to a specific campaign ID (0 = all campaigns).
        page: Page number (starts at 0).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().get_leads(
            campaign_id=campaign_id if campaign_id else None,
            page=page,
            per_page=per_page,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def add_lead(
    campaign_id: int,
    linkedin_profile_url: str,
    email: str = "",
) -> str:
    """Add a new lead to a MeetAlfred campaign.

    Args:
        campaign_id: Target campaign ID (required, from get_campaigns).
        linkedin_profile_url: Full LinkedIn profile URL of the lead (required).
        email: Email address (required only for email/CSV campaigns).
    """
    try:
        result = _get_client().add_lead(
            campaign_id=campaign_id,
            linkedin_profile_url=linkedin_profile_url,
            email=email or None,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Replies
# ------------------------------------------------------------------


@mcp.tool()
def get_replies(
    page: int = 0,
    per_page: int = 25,
) -> str:
    """Get replies received from leads across all campaigns.

    Returns reply messages with lead info (name, LinkedIn URL, reply text,
    campaign, timestamp). Use to monitor responses and identify follow-ups.

    Args:
        page: Page number (starts at 0).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().get_replies(page=page, per_page=per_page)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Connections
# ------------------------------------------------------------------


@mcp.tool()
def get_connections(
    return_only_synced: bool = True,
    page: int = 0,
    per_page: int = 25,
) -> str:
    """Get LinkedIn connections with full profile data.

    Returns connection details: name, headline, company, email, phone,
    LinkedIn URL, skills, location, connected date, and more.

    Args:
        return_only_synced: Only return synced connections (default true).
        page: Page number (starts at 0).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().get_connections(
            return_only_synced=return_only_synced,
            page=page,
            per_page=per_page,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Team
# ------------------------------------------------------------------


@mcp.tool()
def get_team_members() -> str:
    """List team members (requires team owner access)."""
    try:
        result = _get_client().get_team_members()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_member_connections(
    page: int = 0,
    per_page: int = 25,
) -> str:
    """Get connections across team members.

    Args:
        page: Page number (starts at 0).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().get_member_connections(page=page, per_page=per_page)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Activity / Last Actions
# ------------------------------------------------------------------


@mcp.tool()
def get_last_actions(
    action: str = "all_replies",
    page: int = 0,
    per_page: int = 25,
) -> str:
    """Get recent activity and actions performed by MeetAlfred.

    Powerful tool for monitoring campaign activity — invites sent,
    connections accepted, messages sent, replies received, etc.

    Args:
        action: Action type to retrieve. Options:
            - 'invites' — LinkedIn invites sent
            - 'accepted' — accepted connection requests
            - 'already_connected' — leads already connected
            - 'already_invited' — leads already invited
            - 'messages' — LinkedIn messages and InMails sent
            - 'replies' — LinkedIn replies received
            - 'emails' — emails sent
            - 'email_replies' — email replies received
            - 'twitter' — X (Twitter) messages sent
            - 'twitter_replies' — X replies received
            - 'all_replies' — all replies across all channels (default)
            - 'greetings' — birthday, anniversary, job change messages
        page: Page number (starts at 0).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().get_last_actions(
            action=action, page=page, per_page=per_page
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def main() -> None:
    """Run the MeetAlfred MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
