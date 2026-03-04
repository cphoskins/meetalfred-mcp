"""MeetAlfred MCP Server — tools for campaign monitoring, lead management, and reply tracking.

Transport: stdio
Auth: MEETALFRED_API_KEY environment variable (from Settings > Integrations > Webhooks)
Optional: MEETALFRED_BASE_URL for white-label instances (defaults to api.meetalfred.com)
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
        "Use get_campaigns first to find campaign IDs for filtering other tools."
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
def get_campaigns() -> str:
    """List all MeetAlfred campaigns with their IDs, names, and status.

    Use campaign IDs from this response to filter leads, replies, and other tools.
    """
    try:
        result = _get_client().get_campaigns()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Leads
# ------------------------------------------------------------------


@mcp.tool()
def get_leads(
    campaign_id: str = "",
    status: str = "",
    page: int = 1,
    per_page: int = 50,
) -> str:
    """Fetch leads from MeetAlfred, optionally filtered by campaign and status.

    Args:
        campaign_id: Filter to a specific campaign (from get_campaigns).
        status: Filter by lead status (e.g., 'active', 'replied', 'connected').
        page: Page number (starts at 1).
        per_page: Results per page (default 50).
    """
    try:
        result = _get_client().get_leads(
            campaign_id=campaign_id or None,
            status=status or None,
            page=page,
            per_page=per_page,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def add_lead(
    campaign_id: str,
    linkedin_url: str = "",
    email: str = "",
    first_name: str = "",
    last_name: str = "",
    company: str = "",
) -> str:
    """Add a new lead to a MeetAlfred campaign.

    At minimum, provide a campaign_id and either a linkedin_url or email.

    Args:
        campaign_id: Target campaign ID (required, from get_campaigns).
        linkedin_url: LinkedIn profile URL of the lead.
        email: Email address of the lead.
        first_name: Lead's first name.
        last_name: Lead's last name.
        company: Lead's company name.
    """
    try:
        result = _get_client().add_lead(
            campaign_id=campaign_id,
            linkedin_url=linkedin_url or None,
            email=email or None,
            first_name=first_name or None,
            last_name=last_name or None,
            company=company or None,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Replies
# ------------------------------------------------------------------


@mcp.tool()
def get_replies(
    campaign_id: str = "",
    page: int = 1,
    per_page: int = 50,
) -> str:
    """Get replies received from leads across campaigns.

    Use this to monitor campaign responses and identify leads to follow up with.

    Args:
        campaign_id: Filter to a specific campaign (from get_campaigns).
        page: Page number (starts at 1).
        per_page: Results per page (default 50).
    """
    try:
        result = _get_client().get_replies(
            campaign_id=campaign_id or None,
            page=page,
            per_page=per_page,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Connections
# ------------------------------------------------------------------


@mcp.tool()
def get_connections(
    page: int = 1,
    per_page: int = 50,
) -> str:
    """Get connection data between leads and team members.

    Args:
        page: Page number (starts at 1).
        per_page: Results per page (default 50).
    """
    try:
        result = _get_client().get_connections(page=page, per_page=per_page)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Team
# ------------------------------------------------------------------


@mcp.tool()
def get_team_members() -> str:
    """List team members associated with the MeetAlfred account."""
    try:
        result = _get_client().get_team_members()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_member_connections(
    member_id: str = "",
    page: int = 1,
    per_page: int = 50,
) -> str:
    """Get connections for a specific team member.

    Args:
        member_id: Team member ID (from get_team_members).
        page: Page number (starts at 1).
        per_page: Results per page (default 50).
    """
    try:
        result = _get_client().get_member_connections(
            member_id=member_id or None,
            page=page,
            per_page=per_page,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Activity
# ------------------------------------------------------------------


@mcp.tool()
def get_last_actions(
    page: int = 1,
    per_page: int = 50,
) -> str:
    """Get recent account activity and actions taken.

    Useful for monitoring campaign progress and reviewing what happened recently.

    Args:
        page: Page number (starts at 1).
        per_page: Results per page (default 50).
    """
    try:
        result = _get_client().get_last_actions(page=page, per_page=per_page)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# User
# ------------------------------------------------------------------


@mcp.tool()
def get_me() -> str:
    """Get the current MeetAlfred user profile and account info."""
    try:
        result = _get_client().get_me()
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
