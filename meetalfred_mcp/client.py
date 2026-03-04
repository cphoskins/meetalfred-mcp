"""MeetAlfred API client — independent from MCP layer.

Wraps the MeetAlfred webhook API. Base URL defaults to the public API
but can be overridden for white-label instances via MEETALFRED_BASE_URL.

Authentication is via the ``webhook_key`` query parameter on every request.
Generate yours at Settings > Integrations > Webhooks.
"""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_BASE_URL = "https://api.meetalfred.com/api/integrations/webhook"


class MeetAlfredClient:
    """Low-level HTTP client for the MeetAlfred webhook API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
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
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # ------------------------------------------------------------------
    # Generic request helper
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an HTTP request with webhook_key auth and return parsed JSON."""
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
