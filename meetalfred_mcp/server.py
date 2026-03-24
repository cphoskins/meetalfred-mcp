"""MeetAlfred MCP Server — campaign monitoring, lead management, reply tracking, and CRUD.

Transport: stdio
Auth:
  MEETALFRED_API_KEY — webhook key (Settings > Integrations > Webhooks)
  MEETALFRED_JWT_TOKEN — JWT token for internal API (optional, enables tags/campaign CRUD/replies)
Optional:
  MEETALFRED_BASE_URL — override webhook API base URL (white-label instances)
  MEETALFRED_API_BASE_URL — override internal API base URL
"""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from .client import MeetAlfredClient

mcp = FastMCP(
    "meetalfred",
    instructions=(
        "MeetAlfred MCP server for LinkedIn automation campaign monitoring and management. "
        "Pull campaign data, track replies, manage leads, CRUD tags, review activity, "
        "and create/schedule LinkedIn posts. "
        "Use get_campaigns first to find campaign IDs for filtering other tools. "
        "Webhook API tools: pages start at 0. Internal API tools: pages start at 1. "
        "Internal API tools (tags, campaign CRUD, detailed replies, posts) require MEETALFRED_JWT_TOKEN."
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


# ==================================================================
# Internal API tools (require MEETALFRED_JWT_TOKEN)
# ==================================================================

# ------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------


@mcp.tool()
def get_all_tags() -> str:
    """Get all tags (no pagination). Requires JWT token.

    Returns a flat list of all tags with their IDs and names.
    """
    try:
        result = _get_client().get_all_tags()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def list_tags(
    page: int = 1,
    per_page: int = 25,
    sort_field: str = "tag",
    sort_order: str = "ASC",
) -> str:
    """List tags with pagination. Requires JWT token.

    Args:
        page: Page number (starts at 1).
        per_page: Results per page (default 25).
        sort_field: Field to sort by (default 'tag').
        sort_order: 'ASC' or 'DESC'.
    """
    try:
        result = _get_client().list_tags(
            page=page, per_page=per_page,
            sort_field=sort_field, sort_order=sort_order,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def create_tag(name: str) -> str:
    """Create a new tag. Requires JWT token.

    Args:
        name: Tag name to create.
    """
    try:
        result = _get_client().create_tag(name=name)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def update_tag(tag_id: int, name: str) -> str:
    """Rename an existing tag. Requires JWT token.

    Args:
        tag_id: Tag ID (from get_all_tags or list_tags).
        name: New tag name.
    """
    try:
        result = _get_client().update_tag(tag_id=tag_id, name=name)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def delete_tag(tag_id: int) -> str:
    """Delete a tag. Requires JWT token.

    Args:
        tag_id: Tag ID (from get_all_tags or list_tags).
    """
    try:
        result = _get_client().delete_tag(tag_id=tag_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Campaigns (internal API — richer details)
# ------------------------------------------------------------------


@mcp.tool()
def list_campaigns_detailed(
    status: str = "active",
    category: str = "linkedin",
    page: int = 1,
    per_page: int = 25,
    search: str = "",
    run_state: str = "",
) -> str:
    """List campaigns with full details via internal API. Requires JWT token.

    Richer than get_campaigns — includes stats, run state, category filtering.

    Args:
        status: 'active', 'draft', 'archived', or 'all'.
        category: 'linkedin', 'email', 'twitter', or 'all'.
        page: Page number (starts at 1).
        per_page: Results per page (default 25).
        search: Filter campaigns by name.
        run_state: Filter by run state ('running', 'paused', or '').
    """
    try:
        result = _get_client().list_campaigns_detailed(
            status=status, category=category,
            page=page, per_page=per_page,
            search=search, run_state=run_state,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaign(campaign_id: int) -> str:
    """Get full details of a single campaign. Requires JWT token.

    Args:
        campaign_id: Campaign ID (from get_campaigns or list_campaigns_detailed).
    """
    try:
        result = _get_client().get_campaign(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaign_counts(category: str = "linkedin") -> str:
    """Get campaign counts by status (active, draft, archived). Requires JWT token.

    Args:
        category: 'linkedin', 'email', or 'twitter'.
    """
    try:
        result = _get_client().get_campaign_counts(category=category)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def update_campaign(campaign_id: int, label: str = "", status: str = "") -> str:
    """Update campaign fields. Requires JWT token.

    Args:
        campaign_id: Campaign ID.
        label: New campaign name (optional).
        status: New status — 'active', 'draft', 'archived' (optional).
    """
    try:
        fields: dict = {}
        if label:
            fields["label"] = label
        if status:
            fields["status"] = status
        if not fields:
            return json.dumps({"status": "error", "message": "No fields to update"})
        result = _get_client().update_campaign(campaign_id=campaign_id, **fields)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def delete_campaign(campaign_id: int) -> str:
    """Delete a campaign. Requires JWT token. Use with caution.

    Args:
        campaign_id: Campaign ID to delete.
    """
    try:
        result = _get_client().delete_campaign(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Replies (internal API — detailed)
# ------------------------------------------------------------------


@mcp.tool()
def list_replies_detailed(
    page: int = 1,
    per_page: int = 25,
) -> str:
    """List replies with full details via internal API. Requires JWT token.

    Richer than get_replies — includes sorting, more metadata.

    Args:
        page: Page number (starts at 1).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().list_replies_detailed(
            page=page, per_page=per_page,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Campaign Operations
# ------------------------------------------------------------------


@mcp.tool()
def pause_campaign(campaign_id: int) -> str:
    """Pause a running campaign. Requires JWT token.

    Args:
        campaign_id: Campaign ID to pause.
    """
    try:
        result = _get_client().pause_campaign(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def resume_campaign(campaign_id: int) -> str:
    """Resume a paused campaign. Requires JWT token.

    Args:
        campaign_id: Campaign ID to resume.
    """
    try:
        result = _get_client().resume_campaign(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def rename_campaign(campaign_id: int, name: str) -> str:
    """Rename a campaign. Requires JWT token.

    Args:
        campaign_id: Campaign ID.
        name: New campaign name.
    """
    try:
        result = _get_client().rename_campaign(campaign_id=campaign_id, name=name)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def clone_campaign(campaign_id: int) -> str:
    """Clone (duplicate) a campaign. Requires JWT token.

    Args:
        campaign_id: Campaign ID to clone.
    """
    try:
        result = _get_client().clone_campaign(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def archive_campaign(campaign_id: int) -> str:
    """Archive a campaign. Requires JWT token.

    Args:
        campaign_id: Campaign ID to archive.
    """
    try:
        result = _get_client().archive_campaign(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaign_sequence(campaign_id: int) -> str:
    """Get the touch sequence for a campaign. Requires JWT token.

    Returns the sequence steps with their types, messages, delays, and settings.
    Useful for inspecting the current sequence before updating it.

    Args:
        campaign_id: Campaign ID.
    """
    try:
        result = _get_client().get_campaign_sequence(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def update_campaign_sequence(campaign_id: int, sequence: list[dict]) -> str:
    """Update the touch sequence (message templates, delays, actions) for a campaign.
    Requires JWT token.

    IMPORTANT: This replaces the entire sequence. First call get_campaign_sequence
    to read the current sequence, modify only the fields you need, then pass the
    full sequence back.

    Each step in the sequence should have at minimum:
    - type: "LI View", "LI Connect", or "LI Message"
    - delay_number: Number of delay units before this step
    - delay_time_unit: "day(s)" or "hour(s)"

    For "LI Connect" steps:
    - message: Connection request message text
    - connect_followup: true/false (send follow-up on acceptance)
    - followup_message: Message sent when connection is accepted

    For "LI Message" steps:
    - message: Direct message text

    For "LI View" steps:
    - view: true/false
    - auto_endorse: true/false
    - auto_post_like: true/false
    - auto_follow: true/false

    Template variables: {{first_name}}, {{last_name}}, {{company}}, {{title}}

    Args:
        campaign_id: Campaign ID to update.
        sequence: List of touch step dicts (replaces entire sequence).
    """
    try:
        result = _get_client().update_campaign_sequence(
            campaign_id=campaign_id, sequence=sequence
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaigns_grouped() -> str:
    """Get all campaigns grouped by category (linkedin, email, twitter). Requires JWT token."""
    try:
        result = _get_client().get_campaigns_grouped()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Conversations / Messaging
# ------------------------------------------------------------------


@mcp.tool()
def get_conversation_messages(
    conversation_id: str,
    entity_urn: str = "",
) -> str:
    """Get messages in a conversation thread. Requires JWT token.

    Use the conversationUrn from reply data to load the full conversation.

    Args:
        conversation_id: Conversation URN (from reply data).
        entity_urn: Lead entity URN (optional, for context).
    """
    try:
        result = _get_client().get_conversation_messages(
            conversation_id=conversation_id, entity_urn=entity_urn,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def send_message(conversation_id: str, message: str) -> str:
    """Send a message in a conversation (reply to a lead). Requires JWT token.

    Workflow: Use list_replies_detailed to find conversationUrn, then send_message.

    Args:
        conversation_id: Conversation URN (from reply data).
        message: Message text to send.
    """
    try:
        result = _get_client().send_message(
            conversation_id=conversation_id, message=message,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Lead Management (internal API)
# ------------------------------------------------------------------


@mcp.tool()
def get_campaign_leads(
    campaign_id: int,
    lead_type: str = "approved",
    page: int = 1,
    per_page: int = 25,
    excluded_only: bool = False,
) -> str:
    """List leads in a campaign with status filtering. Requires JWT token.

    Args:
        campaign_id: Campaign ID.
        lead_type: Status filter — 'approved', 'connected', 'replies',
            'allReplies', 'messaged', 'invitesPending', 'followedUp',
            'viewed', 'requested', 'alreadyConnected', 'alreadyInvited',
            'inmailed', 'emailed', 'emailReplies', 'invitesWithdraw', etc.
        page: Page number (starts at 1).
        per_page: Results per page (default 25).
        excluded_only: If True, return only excluded leads (default False).
    """
    try:
        result = _get_client().get_campaign_leads(
            campaign_id=campaign_id, lead_type=lead_type,
            page=page, per_page=per_page,
            excluded_only=excluded_only,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_lead_statuses(campaign_id: int) -> str:
    """Get lead status counts for a campaign (views, connects, replies, etc.). Requires JWT token.

    Args:
        campaign_id: Campaign ID.
    """
    try:
        result = _get_client().get_lead_statuses(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def return_lead_to_campaign(
    entity_urns: list[str],
    campaign_id: int = 0,
) -> str:
    """Return leads to a campaign sequence. Requires JWT token.

    Re-enqueues stopped/excluded leads so they continue receiving campaign touches.

    Args:
        entity_urns: List of lead entity URNs (e.g. ['ACoAAA...']).
        campaign_id: Campaign ID (optional, for single-campaign return).
    """
    try:
        result = _get_client().return_lead_to_campaign(
            entity_urns=entity_urns,
            campaign_id=campaign_id if campaign_id else None,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def add_tags_to_leads(entity_urns: list[str], tag_ids: list[int]) -> str:
    """Add tags to one or more leads. Requires JWT token.

    Args:
        entity_urns: List of lead entity URNs.
        tag_ids: List of tag IDs to add (from get_all_tags).
    """
    try:
        result = _get_client().add_tags_to_leads(
            entity_urns=entity_urns, tag_ids=tag_ids,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def exclude_leads(entity_urns: list[str], exclude: bool = True) -> str:
    """Exclude or un-exclude leads from campaigns. Requires JWT token.

    Args:
        entity_urns: List of lead entity URNs.
        exclude: True to exclude, False to un-exclude (default True).
    """
    try:
        result = _get_client().exclude_leads(
            entity_urns=entity_urns, exclude=exclude,
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Posts (Social Publishing)
# ------------------------------------------------------------------


@mcp.tool()
def list_posts(
    page: int = 1,
    per_page: int = 25,
) -> str:
    """List scheduled and published LinkedIn posts. Requires JWT token.

    Returns posts with ID, title, status, scheduled time, post URL, and engagement stats.

    Args:
        page: Page number (starts at 1).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().list_posts(page=page, per_page=per_page)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_post_types() -> str:
    """Get post counts by platform type (linkedIn, facebook, instagram, twitter). Requires JWT token."""
    try:
        result = _get_client().get_post_types()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_post(post_id: int) -> str:
    """Get full details of a single post. Requires JWT token.

    Returns title, content, status, scheduled time, platform, audience, and engagement.

    Args:
        post_id: Post ID (from list_posts).
    """
    try:
        result = _get_client().get_post(post_id=post_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def create_post(
    title: str,
    content: str,
    scheduled_at: str,
    post_types: list[str] = ["linkedin"],
    post_as: str = "You",
    audience: str = "anyone",
    allow_comments: bool = True,
) -> str:
    """Create a new scheduled LinkedIn post. Requires JWT token.

    The post will be published at the scheduled time via MeetAlfred.
    After creation, use list_posts to verify and get the post ID.

    Args:
        title: Internal label for the post (not shown on LinkedIn).
        content: The post body text that will appear on LinkedIn.
        scheduled_at: When to publish, ISO 8601 format (e.g. '2026-03-15T14:00:00.000Z').
        post_types: Platforms to post to (default ['linkedin']).
        post_as: Post as 'You' (personal profile) or company page name.
        audience: Visibility scope (default 'anyone').
        allow_comments: Whether to allow comments (default true).
    """
    try:
        result = _get_client().create_post(
            title=title,
            content=content,
            scheduled_at=scheduled_at,
            post_types=post_types,
            post_as=post_as,
            audience=audience,
            allow_comments=allow_comments,
        )
        # create_post returns empty body on 201, so confirm via list
        return json.dumps({"status": "success", "data": result or {"created": True}}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def update_post(
    post_id: int,
    title: str = "",
    content: str = "",
    scheduled_at: str = "",
    audience: str = "",
    allow_comments: bool = True,
) -> str:
    """Update a scheduled post. Requires JWT token.

    Only pending posts can be updated. Pass only the fields you want to change.

    Args:
        post_id: Post ID (from list_posts).
        title: New internal title (optional).
        content: New post body text (optional).
        scheduled_at: New scheduled time in ISO 8601 format (optional).
        audience: New audience scope (optional).
        allow_comments: Whether to allow comments.
    """
    try:
        fields: dict = {}
        if title:
            fields["title"] = title
        if content:
            fields["content"] = content
        if scheduled_at:
            fields["scheduledAt"] = scheduled_at
        if audience:
            fields["audience"] = audience
        fields["allowComments"] = allow_comments
        if len(fields) <= 1:
            return json.dumps({"status": "error", "message": "No fields to update"})
        result = _get_client().update_post(post_id=post_id, **fields)
        return json.dumps({"status": "success", "data": result or {"updated": True}}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def update_post_time(post_id: int, scheduled_at: str) -> str:
    """Reschedule a pending post. Requires JWT token.

    Args:
        post_id: Post ID (from list_posts).
        scheduled_at: New scheduled time in ISO 8601 format (e.g. '2026-03-15T14:00:00.000Z').
    """
    try:
        result = _get_client().update_post_time(post_id=post_id, scheduled_at=scheduled_at)
        return json.dumps({"status": "success", "data": result or {"updated": True}}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def archive_post(post_id: int) -> str:
    """Archive a post. Requires JWT token.

    Args:
        post_id: Post ID (from list_posts).
    """
    try:
        result = _get_client().archive_post(post_id=post_id)
        return json.dumps({"status": "success", "data": result or {"archived": True}}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def delete_post(post_id: int) -> str:
    """Delete a post. Requires JWT token. Use with caution.

    Args:
        post_id: Post ID (from list_posts).
    """
    try:
        result = _get_client().delete_post(post_id=post_id)
        return json.dumps({"status": "success", "data": result or {"deleted": True}}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Statistics & Analytics
# ------------------------------------------------------------------


@mcp.tool()
def get_statistics() -> str:
    """Get global account statistics — invites sent/accepted, messages, replies, profile views,
    and acceptance/reply percentages. Requires JWT token.

    Returns all-time totals across all campaigns. No date filtering is supported by the API.
    """
    try:
        result = _get_client().get_statistics()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaign_activity_chart(campaign_id: int, days: int = 30) -> str:
    """Get daily activity breakdown for a campaign (last 30 days). Requires JWT token.

    Includes connect requests, connections, views, messages, responses, follow-ups per day.
    The API always returns 30 days — use the days parameter to limit to the most recent N days.

    Args:
        campaign_id: Campaign ID (from get_campaigns or list_campaigns_detailed).
        days: Number of most recent days to return (1–30, default 30).
    """
    try:
        result = _get_client().get_campaign_activity_chart(
            campaign_id=campaign_id, days=days
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaign_progress(campaign_id: int) -> str:
    """Get campaign completion progress and lead status counts. Requires JWT token.

    Returns overall progress percentage and counts of active, completed,
    waiting-for-connect, and paused leads.

    Args:
        campaign_id: Campaign ID (from get_campaigns or list_campaigns_detailed).
    """
    try:
        result = _get_client().get_campaign_progress(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaign_sequence_progress(campaign_id: int) -> str:
    """Get detailed sequence funnel with per-step lead counts. Requires JWT token.

    Shows how many leads have reached each step of the campaign sequence —
    useful for identifying drop-off points in the funnel.

    Args:
        campaign_id: Campaign ID (from get_campaigns or list_campaigns_detailed).
    """
    try:
        result = _get_client().get_campaign_sequence_progress(campaign_id=campaign_id)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_campaign_actions(
    campaign_id: int,
    page: int = 1,
    per_page: int = 25,
) -> str:
    """Get campaign actions (found, viewed, requested connect, connected, messaged, etc.)
    with full person profile data. Requires JWT token.

    Each action records a touchpoint event for a lead. The person object includes
    name, email, employer, title, location, LinkedIn data, social handles, school, etc.

    Args:
        campaign_id: Campaign ID (from get_campaigns or list_campaigns_detailed).
        page: Page number (starts at 1).
        per_page: Results per page (default 25).
    """
    try:
        result = _get_client().get_campaign_actions(
            campaign_id=campaign_id, page=page, per_page=per_page
        )
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def get_dashboard() -> str:
    """Get dashboard view with all campaigns, their sequences, and configuration.
    Requires JWT token.

    Returns a high-level overview of all campaigns with their current state,
    sequences, and settings — useful for a quick account health check.
    """
    try:
        result = _get_client().get_dashboard()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# Notifications
# ------------------------------------------------------------------


@mcp.tool()
def get_unread_notification_count() -> str:
    """Get count of unread notifications. Requires JWT token."""
    try:
        result = _get_client().get_unread_notification_count()
        return json.dumps({"status": "success", "data": result}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ------------------------------------------------------------------
# User
# ------------------------------------------------------------------


@mcp.tool()
def get_current_user() -> str:
    """Get the current authenticated user's profile. Requires JWT token."""
    try:
        result = _get_client().get_current_user()
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
