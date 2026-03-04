"""MeetAlfred API client — independent from MCP layer.

Wraps the MeetAlfred webhook/REST API. Base URL defaults to the public
API (api.meetalfred.com) but can be overridden for white-label instances.

Authentication is via API key passed in the ``X-Alfred-Auth`` header.
Generate yours at Settings > Integrations > Webhooks in your MeetAlfred
dashboard.
"""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_BASE_URL = "https://api.meetalfred.com/api/v1"


class MeetAlfredClient:
    """Low-level HTTP client for the MeetAlfred API."""

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
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Alfred-Auth": self.api_key,
            }
        )

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
        """Execute an HTTP request and return parsed JSON."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.request(method, url, params=params, json=json_body)
        resp.raise_for_status()
        if not resp.text.strip():
            return {}
        return resp.json()

    # ------------------------------------------------------------------
    # Campaigns
    # ------------------------------------------------------------------

    def get_campaigns(self) -> Any:
        """Retrieve list of campaigns."""
        return self._request("GET", "/campaigns")

    # ------------------------------------------------------------------
    # Leads
    # ------------------------------------------------------------------

    def get_leads(
        self,
        campaign_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Any:
        """Fetch leads with optional filtering."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if campaign_id:
            params["campaign_id"] = campaign_id
        if status:
            params["status"] = status
        return self._request("GET", "/leads", params=params)

    def add_lead(
        self,
        campaign_id: str,
        linkedin_url: str | None = None,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        company: str | None = None,
        **extra_fields: Any,
    ) -> Any:
        """Add a new lead to a campaign."""
        body: dict[str, Any] = {"campaign_id": campaign_id}
        if linkedin_url:
            body["linkedin_url"] = linkedin_url
        if email:
            body["email"] = email
        if first_name:
            body["first_name"] = first_name
        if last_name:
            body["last_name"] = last_name
        if company:
            body["company"] = company
        body.update(extra_fields)
        return self._request("POST", "/leads", json_body=body)

    # ------------------------------------------------------------------
    # Replies
    # ------------------------------------------------------------------

    def get_replies(
        self,
        campaign_id: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Any:
        """Retrieve replies from leads."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if campaign_id:
            params["campaign_id"] = campaign_id
        return self._request("GET", "/replies", params=params)

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def get_connections(
        self,
        page: int = 1,
        per_page: int = 50,
    ) -> Any:
        """Retrieve connection data between leads and team members."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        return self._request("GET", "/connections", params=params)

    # ------------------------------------------------------------------
    # Team
    # ------------------------------------------------------------------

    def get_team_members(self) -> Any:
        """Retrieve list of team members."""
        return self._request("GET", "/teams/members")

    def get_member_connections(
        self,
        member_id: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Any:
        """Retrieve connections for a specific team member."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if member_id:
            params["member_id"] = member_id
        return self._request("GET", "/members/connections", params=params)

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    def get_last_actions(
        self,
        page: int = 1,
        per_page: int = 50,
    ) -> Any:
        """Retrieve recent account activity."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        return self._request("GET", "/actions/last", params=params)

    # ------------------------------------------------------------------
    # User / Preferences (discovered via browser network inspection)
    # ------------------------------------------------------------------

    def get_user_preferences(self) -> Any:
        """Retrieve current user preferences."""
        return self._request("GET", "/users/preferences")

    def get_me(self) -> Any:
        """Retrieve current user profile."""
        return self._request("GET", "/users/me")
