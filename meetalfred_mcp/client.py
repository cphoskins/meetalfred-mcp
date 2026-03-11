"""MeetAlfred API client — independent from MCP layer.

Wraps both the MeetAlfred **webhook API** (read-heavy, webhook_key auth)
and the **internal API** (/api/v1/, JWT auth) for full CRUD operations.

Webhook auth: ``webhook_key`` query parameter — generate at Settings > Integrations > Webhooks.
Internal auth: JWT token — extract from browser cookie/localStorage.
"""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_BASE_URL = "https://api.meetalfred.com/api/integrations/webhook"
DEFAULT_API_BASE_URL = "https://api.meetalfred.com/api/v1"


class MeetAlfredClient:
    """HTTP client for MeetAlfred — webhook API + internal API (dual auth)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        jwt_token: str | None = None,
        api_base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("MEETALFRED_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "MeetAlfred API key is required. Set MEETALFRED_API_KEY or pass api_key."
            )
        self.base_url = (
            base_url
            or os.environ.get("MEETALFRED_BASE_URL", "")
            or DEFAULT_BASE_URL
        ).rstrip("/")

        # Internal API (optional — needed for tags, campaign CRUD, replies)
        self.jwt_token = jwt_token or os.environ.get("MEETALFRED_JWT_TOKEN", "")
        self.api_base_url = (
            api_base_url
            or os.environ.get("MEETALFRED_API_BASE_URL", "")
            or DEFAULT_API_BASE_URL
        ).rstrip("/")

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _require_jwt(self) -> None:
        """Raise if JWT token is not configured."""
        if not self.jwt_token:
            raise ValueError(
                "JWT token required for this operation. "
                "Set MEETALFRED_JWT_TOKEN or pass jwt_token."
            )

    # ------------------------------------------------------------------
    # Generic request helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a webhook API request with webhook_key auth."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        all_params = {"webhook_key": self.api_key}
        if params:
            all_params.update(params)
        resp = self.session.request(
            method, url, params=all_params, json=json_body
        )
        resp.raise_for_status()
        if not resp.text.strip():
            return {}
        return resp.json()

    def _api_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an internal API request with JWT Bearer auth."""
        self._require_jwt()
        url = f"{self.api_base_url}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        resp = self.session.request(
            method, url, params=params, json=json_body, headers=headers
        )
        resp.raise_for_status()
        if not resp.text.strip():
            return {}
        return resp.json()

    # ------------------------------------------------------------------
    # Campaigns
    # ------------------------------------------------------------------

    def get_campaigns(self, campaign_type: str = "active") -> Any:
        """Retrieve campaigns.

        Args:
            campaign_type: One of 'active', 'draft', 'archived', 'all'.
        """
        return self._request("GET", "/campaigns", params={"type": campaign_type})

    # ------------------------------------------------------------------
    # Leads
    # ------------------------------------------------------------------

    def get_leads(
        self,
        campaign_id: int | None = None,
        page: int = 0,
        per_page: int = 25,
    ) -> Any:
        """Fetch leads. Returns data in 'actions' array with campaign and person objects.

        Args:
            campaign_id: Filter to a specific campaign ID.
            page: Page number (starts at 0).
            per_page: Results per page.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if campaign_id is not None:
            params["campaign"] = campaign_id
        return self._request("GET", "/new-leads", params=params)

    def add_lead(
        self,
        campaign_id: int,
        linkedin_profile_url: str,
        email: str | None = None,
        **custom_fields: Any,
    ) -> Any:
        """Add a new lead to a campaign.

        Args:
            campaign_id: Target campaign ID (required).
            linkedin_profile_url: LinkedIn profile URL (required).
            email: Email address (required only for email/CSV campaigns).
            **custom_fields: Custom CSV fields prefixed with csv_ (e.g. csv_company="Acme").
        """
        body: dict[str, Any] = {
            "campaign": campaign_id,
            "linkedin_profile_url": linkedin_profile_url,
        }
        if email:
            body["email"] = email
        body.update(custom_fields)
        return self._request("POST", "/add_lead_to_campaign", json_body=body)

    # ------------------------------------------------------------------
    # Replies
    # ------------------------------------------------------------------

    def get_replies(
        self,
        page: int = 0,
        per_page: int = 25,
    ) -> Any:
        """Retrieve replies from leads. Returns data in 'actions' array.

        Args:
            page: Page number (starts at 0).
            per_page: Results per page.
        """
        return self._request(
            "GET", "/new-reply-detected", params={"page": page, "per_page": per_page}
        )

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def get_connections(
        self,
        return_only_synced: bool = True,
        page: int = 0,
        per_page: int = 25,
    ) -> Any:
        """Retrieve LinkedIn connections.

        Args:
            return_only_synced: Only return synced connections.
            page: Page number (starts at 0).
            per_page: Results per page.
        """
        params: dict[str, Any] = {
            "return_only_synced": str(return_only_synced).lower(),
            "page": page,
            "per_page": per_page,
        }
        return self._request("GET", "/new-connections", params=params)

    # ------------------------------------------------------------------
    # Team
    # ------------------------------------------------------------------

    def get_team_members(self) -> Any:
        """Retrieve team members (requires team owner access)."""
        return self._request("GET", "/get_team_members")

    def get_member_connections(
        self,
        page: int = 0,
        per_page: int = 25,
    ) -> Any:
        """Retrieve connections across team members.

        Args:
            page: Page number (starts at 0).
            per_page: Results per page.
        """
        return self._request(
            "GET",
            "/get_member_connections",
            params={"page": page, "per_page": per_page},
        )

    # ------------------------------------------------------------------
    # Activity / Last Actions
    # ------------------------------------------------------------------

    VALID_ACTIONS = (
        "invites",
        "already_connected",
        "already_invited",
        "accepted",
        "messages",
        "replies",
        "emails",
        "email_replies",
        "twitter",
        "twitter_replies",
        "all_replies",
        "greetings",
    )

    def get_last_actions(
        self,
        action: str = "all_replies",
        page: int = 0,
        per_page: int = 25,
    ) -> Any:
        """Retrieve recent actions/activity.

        Args:
            action: Action type filter. One of: invites, already_connected,
                already_invited, accepted, messages, replies, emails,
                email_replies, twitter, twitter_replies, all_replies, greetings.
            page: Page number (starts at 0).
            per_page: Results per page.
        """
        if action not in self.VALID_ACTIONS:
            raise ValueError(
                f"Invalid action '{action}'. Must be one of: {', '.join(self.VALID_ACTIONS)}"
            )
        return self._request(
            "GET",
            "/get-last-actions",
            params={"action": action, "page": page, "per_page": per_page},
        )

    # ==================================================================
    # Internal API (JWT auth) — tags, campaigns CRUD, replies
    # ==================================================================

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def get_all_tags(self) -> Any:
        """Retrieve all tags (no pagination)."""
        return self._api_request("GET", "/tags/all")

    def list_tags(
        self,
        page: int = 1,
        per_page: int = 25,
        sort_field: str = "tag",
        sort_order: str = "ASC",
    ) -> Any:
        """Retrieve tags with pagination.

        Args:
            page: Page number (starts at 1 for internal API).
            per_page: Results per page.
            sort_field: Field to sort by (default 'tag').
            sort_order: 'ASC' or 'DESC'.
        """
        return self._api_request(
            "GET",
            "/tags",
            params={
                "page": page,
                "perPage": per_page,
                "sortField": sort_field,
                "sortOrder": sort_order,
            },
        )

    def create_tag(self, name: str) -> Any:
        """Create a new tag.

        Args:
            name: Tag name.
        """
        return self._api_request("POST", "/tags", json_body={"tag": name})

    def update_tag(self, tag_id: int, name: str) -> Any:
        """Rename a tag.

        Args:
            tag_id: Tag ID.
            name: New tag name.
        """
        return self._api_request("PUT", f"/tags/{tag_id}", json_body={"tag": name})

    def delete_tag(self, tag_id: int) -> Any:
        """Delete a tag.

        Args:
            tag_id: Tag ID.
        """
        return self._api_request("DELETE", f"/tags/{tag_id}")

    # ------------------------------------------------------------------
    # Campaigns (internal API — richer than webhook)
    # ------------------------------------------------------------------

    def list_campaigns_detailed(
        self,
        status: str = "active",
        category: str = "linkedin",
        page: int = 1,
        per_page: int = 25,
        sort_field: str = "createdAt",
        sort_order: str = "DESC",
        search: str = "",
        run_state: str = "",
    ) -> Any:
        """List campaigns with full details via internal API.

        Args:
            status: 'active', 'draft', 'archived', or 'all'.
            category: 'linkedin', 'email', 'twitter', or 'all'.
            page: Page number (starts at 1).
            per_page: Results per page.
            sort_field: Sort field (default 'createdAt').
            sort_order: 'ASC' or 'DESC'.
            search: Search string to filter campaigns by name.
            run_state: Filter by run state (e.g. 'running', 'paused', '').
        """
        params: dict[str, Any] = {
            "status": status,
            "category": category,
            "page": page,
            "perPage": per_page,
            "sortField": sort_field,
            "sortOrder": sort_order,
            "filter": "all",
        }
        if search:
            params["search"] = search
        if run_state:
            params["runState"] = run_state
        return self._api_request("GET", "/campaigns", params=params)

    def get_campaign(self, campaign_id: int) -> Any:
        """Get a single campaign by ID.

        Args:
            campaign_id: Campaign ID.
        """
        return self._api_request("GET", f"/campaigns/{campaign_id}")

    def get_campaign_counts(self, category: str = "linkedin") -> Any:
        """Get campaign counts by status.

        Args:
            category: 'linkedin', 'email', 'twitter'.
        """
        return self._api_request(
            "GET", "/campaigns/counts", params={"category": category}
        )

    def update_campaign(self, campaign_id: int, **fields: Any) -> Any:
        """Update campaign fields.

        Args:
            campaign_id: Campaign ID.
            **fields: Fields to update (e.g. label, status).
        """
        return self._api_request(
            "PUT", f"/campaigns/{campaign_id}", json_body=fields
        )

    def delete_campaign(self, campaign_id: int) -> Any:
        """Delete a campaign.

        Args:
            campaign_id: Campaign ID.
        """
        return self._api_request("DELETE", f"/campaigns/{campaign_id}")

    # ------------------------------------------------------------------
    # Replies (internal API — for sending)
    # ------------------------------------------------------------------

    def list_replies_detailed(
        self,
        page: int = 1,
        per_page: int = 25,
        sort_field: str = "date",
        sort_order: str = "DESC",
    ) -> Any:
        """List replies with full details via internal API.

        Args:
            page: Page number (starts at 1).
            per_page: Results per page.
            sort_field: Sort field (default 'date').
            sort_order: 'ASC' or 'DESC'.
        """
        return self._api_request(
            "GET",
            "/campaigns/replies",
            params={
                "page": page,
                "perPage": per_page,
                "sortField": sort_field,
                "sortOrder": sort_order,
            },
        )

    # ------------------------------------------------------------------
    # Campaign Operations
    # ------------------------------------------------------------------

    def pause_campaign(self, campaign_id: int) -> Any:
        """Pause a running campaign.

        Args:
            campaign_id: Campaign ID.
        """
        return self._api_request(
            "PATCH",
            f"/campaigns/{campaign_id}/running-state",
            json_body={"runState": "paused"},
        )

    def resume_campaign(self, campaign_id: int) -> Any:
        """Resume a paused campaign.

        Args:
            campaign_id: Campaign ID.
        """
        return self._api_request(
            "PATCH",
            f"/campaigns/{campaign_id}/running-state",
            json_body={"runState": "running"},
        )

    def rename_campaign(self, campaign_id: int, name: str) -> Any:
        """Rename a campaign.

        Args:
            campaign_id: Campaign ID.
            name: New campaign name.
        """
        return self._api_request(
            "PATCH", f"/campaigns/{campaign_id}/name", json_body={"name": name}
        )

    def clone_campaign(self, campaign_id: int) -> Any:
        """Clone (duplicate) a campaign.

        Args:
            campaign_id: Campaign ID to clone.
        """
        return self._api_request("POST", f"/campaigns/{campaign_id}/clone")

    def archive_campaign(self, campaign_id: int) -> Any:
        """Archive a campaign.

        Args:
            campaign_id: Campaign ID.
        """
        return self._api_request("PATCH", f"/campaigns/{campaign_id}/archive")

    def get_campaign_sequence(self, campaign_id: int) -> Any:
        """Get the touch sequence for a campaign.

        Args:
            campaign_id: Campaign ID.

        Returns the touchSequence object from the campaign data.
        """
        campaign = self._api_request("GET", f"/campaigns/{campaign_id}")
        return campaign.get("touchSequence", {})

    def update_campaign_sequence(
        self, campaign_id: int, sequence: list[dict[str, Any]]
    ) -> Any:
        """Update the touch sequence for a campaign.

        Args:
            campaign_id: Campaign ID.
            sequence: List of touch step dicts. Each step should have at minimum
                a ``type`` field (e.g. "LI View", "LI Connect", "LI Message")
                and the relevant fields for that type (message, delay_number,
                delay_time_unit, connect_followup, followup_message, etc.).
        """
        return self._api_request(
            "PATCH",
            f"/campaigns/{campaign_id}/sequence",
            json_body={"touchSequence": {"sequence": sequence}},
        )

    def get_campaigns_grouped(self) -> Any:
        """Get all campaigns grouped by category (linkedin, email, twitter)."""
        return self._api_request("GET", "/campaigns/grouped")

    # ------------------------------------------------------------------
    # Conversations / Messaging
    # ------------------------------------------------------------------

    def get_conversation_messages(
        self,
        conversation_id: str,
        entity_urn: str = "",
        created_before: str = "",
    ) -> Any:
        """Get messages in a conversation.

        Args:
            conversation_id: Conversation URN (from reply data).
            entity_urn: Lead entity URN (optional).
            created_before: ISO timestamp for pagination (optional).
        """
        params: dict[str, Any] = {}
        if entity_urn:
            params["entityUrn"] = entity_urn
        if created_before:
            params["createdBefore"] = created_before
        return self._api_request(
            "GET", f"/conversations/{conversation_id}/messages", params=params or None
        )

    def send_message(self, conversation_id: str, message: str) -> Any:
        """Send a message in a conversation (reply to a lead).

        Args:
            conversation_id: Conversation URN (from reply data).
            message: Message text to send.
        """
        return self._api_request(
            "POST",
            "/conversations/messages",
            json_body={"conversationId": conversation_id, "message": message},
        )

    # ------------------------------------------------------------------
    # Lead Management (internal API)
    # ------------------------------------------------------------------

    def get_campaign_leads(
        self,
        campaign_id: int,
        lead_type: str = "approved",
        page: int = 1,
        per_page: int = 25,
    ) -> Any:
        """List leads in a campaign with status filtering.

        Args:
            campaign_id: Campaign ID.
            lead_type: Lead status filter — 'approved', 'connected', 'replied',
                'messaged', 'invitesPending', etc.
            page: Page number (starts at 1).
            per_page: Results per page.
        """
        return self._api_request(
            "GET",
            f"/leads/campaign/{campaign_id}",
            params={"page": page, "perPage": per_page, "type": lead_type},
        )

    def get_lead_statuses(self, campaign_id: int) -> Any:
        """Get lead status counts for a campaign.

        Args:
            campaign_id: Campaign ID.
        """
        return self._api_request("GET", f"/leads/campaign/{campaign_id}/statuses")

    def return_lead_to_campaign(
        self, entity_urns: list[str], campaign_id: int | None = None
    ) -> Any:
        """Return leads to a campaign sequence.

        Args:
            entity_urns: List of lead entity URNs.
            campaign_id: Campaign ID (for single-campaign return).
        """
        if campaign_id:
            return self._api_request(
                "PATCH",
                f"/leads/campaign/{campaign_id}/return",
                json_body={"entityUrns": entity_urns},
            )
        return self._api_request(
            "PATCH",
            "/leads/return-to-campaign",
            json_body={"entityUrns": entity_urns},
        )

    def add_tags_to_leads(self, entity_urns: list[str], tag_ids: list[int]) -> Any:
        """Add tags to one or more leads.

        Args:
            entity_urns: List of lead entity URNs.
            tag_ids: List of tag IDs to add.
        """
        return self._api_request(
            "POST",
            "/leads/add-tags",
            json_body={"entityUrns": entity_urns, "tagIds": tag_ids},
        )

    def set_lead_tags(self, entity_urn: str, tag_ids: list[int]) -> Any:
        """Set (replace) tags on a lead.

        Args:
            entity_urn: Lead entity URN.
            tag_ids: List of tag IDs (replaces existing).
        """
        return self._api_request(
            "PUT",
            f"/leads/{entity_urn}/set-tags",
            json_body={"tagIds": tag_ids},
        )

    def exclude_leads(self, entity_urns: list[str], exclude: bool = True) -> Any:
        """Exclude or un-exclude leads.

        Args:
            entity_urns: List of lead entity URNs.
            exclude: True to exclude, False to un-exclude.
        """
        return self._api_request(
            "POST",
            "/leads/exclude",
            json_body={"entityUrns": entity_urns, "exclude": exclude},
        )

    # ------------------------------------------------------------------
    # Posts (Social Publishing)
    # ------------------------------------------------------------------

    def list_posts(
        self,
        page: int = 1,
        per_page: int = 25,
    ) -> Any:
        """List scheduled/published posts.

        Args:
            page: Page number (starts at 1).
            per_page: Results per page.
        """
        return self._api_request(
            "GET", "/posts", params={"page": page, "perPage": per_page}
        )

    def get_post_types(self) -> Any:
        """Get post type counts (linkedIn, facebook, instagram, twitter)."""
        return self._api_request("GET", "/posts/types")

    def get_post(self, post_id: int) -> Any:
        """Get a single post by ID.

        Args:
            post_id: Post ID.
        """
        return self._api_request("GET", f"/posts/{post_id}")

    def create_post(
        self,
        title: str,
        content: str,
        scheduled_at: str,
        post_types: list[str] | None = None,
        post_as: str = "You",
        audience: str = "anyone",
        allow_comments: bool = True,
    ) -> Any:
        """Create a new scheduled post.

        Args:
            title: Post title (internal label, not shown on LinkedIn).
            content: Post body text.
            scheduled_at: ISO 8601 datetime string (e.g. '2026-03-15T14:00:00.000Z').
            post_types: List of platforms (e.g. ['linkedin']). Defaults to ['linkedin'].
            post_as: 'You' (personal profile) or company page name.
            audience: 'anyone' or other audience scope.
            allow_comments: Whether to allow comments.
        """
        body = {
            "title": title,
            "content": content,
            "scheduledAt": scheduled_at,
            "postTypes": post_types or ["linkedin"],
            "postAs": post_as,
            "audience": audience,
            "allowComments": allow_comments,
        }
        return self._api_request("POST", "/posts", json_body=body)

    def update_post(self, post_id: int, **fields: Any) -> Any:
        """Update a post.

        Args:
            post_id: Post ID.
            **fields: Fields to update (content, title, scheduledAt, etc.).
        """
        return self._api_request("PATCH", f"/posts/{post_id}", json_body=fields)

    def update_post_time(self, post_id: int, scheduled_at: str) -> Any:
        """Update the scheduled time of a post.

        Args:
            post_id: Post ID.
            scheduled_at: New ISO 8601 datetime string.
        """
        return self._api_request(
            "PATCH", f"/posts/{post_id}/post-time",
            json_body={"scheduledAt": scheduled_at},
        )

    def archive_post(self, post_id: int) -> Any:
        """Archive a post.

        Args:
            post_id: Post ID.
        """
        return self._api_request("PATCH", f"/posts/{post_id}/archive")

    def delete_post(self, post_id: int) -> Any:
        """Delete a post.

        Args:
            post_id: Post ID.
        """
        return self._api_request("DELETE", f"/posts/{post_id}")

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def get_notifications(self, page: int = 1, per_page: int = 50) -> Any:
        """Get notifications.

        Args:
            page: Page number (starts at 1).
            per_page: Results per page.
        """
        return self._api_request(
            "GET", "/notifications", params={"page": page, "perPage": per_page}
        )

    def get_unread_notification_count(self) -> Any:
        """Get count of unread notifications."""
        return self._api_request("GET", "/notifications/unread-count")

    def mark_all_notifications_read(self) -> Any:
        """Mark all notifications as read."""
        return self._api_request("PATCH", "/notifications/mark-all-as-read")

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------

    def get_current_user(self) -> Any:
        """Get the current authenticated user's profile."""
        return self._api_request("GET", "/users/me")
