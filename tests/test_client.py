"""Unit tests for MeetAlfredClient — all HTTP calls are mocked."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from meetalfred_mcp.client import DEFAULT_BASE_URL, MeetAlfredClient


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a client with a dummy API key."""
    return MeetAlfredClient(api_key="test-api-key-12345")


@pytest.fixture
def mock_response():
    """Factory for mocked requests.Response objects."""

    def _make(json_data=None, status_code=200, text=""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data if json_data is not None else {}
        resp.text = text or (str(json_data) if json_data is not None else "")
        resp.raise_for_status.return_value = None
        return resp

    return _make


# ------------------------------------------------------------------
# Initialization
# ------------------------------------------------------------------


class TestClientInit:
    def test_raises_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                MeetAlfredClient()

    def test_reads_env_var(self):
        env = {"MEETALFRED_API_KEY": "env-key-999"}
        with patch.dict(os.environ, env, clear=True):
            c = MeetAlfredClient()
            assert c.api_key == "env-key-999"

    def test_constructor_overrides_env(self):
        env = {"MEETALFRED_API_KEY": "env-key"}
        with patch.dict(os.environ, env, clear=True):
            c = MeetAlfredClient(api_key="constructor-key")
            assert c.api_key == "constructor-key"

    def test_default_base_url(self, client):
        assert client.base_url == DEFAULT_BASE_URL

    def test_custom_base_url(self):
        c = MeetAlfredClient(api_key="k", base_url="https://proactivebda.ai/api/v1")
        assert c.base_url == "https://proactivebda.ai/api/v1"

    def test_env_base_url(self):
        env = {
            "MEETALFRED_API_KEY": "k",
            "MEETALFRED_BASE_URL": "https://custom.example.com/api/v1/",
        }
        with patch.dict(os.environ, env, clear=True):
            c = MeetAlfredClient()
            # Trailing slash should be stripped
            assert c.base_url == "https://custom.example.com/api/v1"

    def test_auth_header_set(self, client):
        assert client.session.headers["X-Alfred-Auth"] == "test-api-key-12345"


# ------------------------------------------------------------------
# Campaigns
# ------------------------------------------------------------------


class TestCampaigns:
    def test_get_campaigns(self, client, mock_response):
        campaigns = [{"id": "c1", "name": "Recruiter Outreach", "status": "active"}]
        with patch.object(
            client.session, "request", return_value=mock_response(campaigns)
        ) as mock_req:
            result = client.get_campaigns()
            assert result == campaigns
            mock_req.assert_called_once()
            args, kwargs = mock_req.call_args
            assert args[0] == "GET"
            assert "/campaigns" in args[1]


# ------------------------------------------------------------------
# Leads
# ------------------------------------------------------------------


class TestLeads:
    def test_get_leads_no_filter(self, client, mock_response):
        leads = [{"id": "l1", "name": "John Doe"}]
        with patch.object(
            client.session, "request", return_value=mock_response(leads)
        ) as mock_req:
            result = client.get_leads()
            assert result == leads
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["page"] == 1
            assert kwargs["params"]["per_page"] == 50

    def test_get_leads_with_campaign_filter(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response([])
        ) as mock_req:
            client.get_leads(campaign_id="c1", status="replied")
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["campaign_id"] == "c1"
            assert kwargs["params"]["status"] == "replied"

    def test_add_lead(self, client, mock_response):
        resp_data = {"id": "l2", "status": "added"}
        with patch.object(
            client.session, "request", return_value=mock_response(resp_data)
        ) as mock_req:
            result = client.add_lead(
                campaign_id="c1",
                linkedin_url="https://linkedin.com/in/johndoe",
                first_name="John",
                last_name="Doe",
            )
            assert result == resp_data
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert kwargs["json"]["campaign_id"] == "c1"
            assert kwargs["json"]["linkedin_url"] == "https://linkedin.com/in/johndoe"


# ------------------------------------------------------------------
# Replies
# ------------------------------------------------------------------


class TestReplies:
    def test_get_replies(self, client, mock_response):
        replies = [{"lead_id": "l1", "message": "Thanks for connecting!"}]
        with patch.object(
            client.session, "request", return_value=mock_response(replies)
        ):
            result = client.get_replies()
            assert result == replies

    def test_get_replies_filtered(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response([])
        ) as mock_req:
            client.get_replies(campaign_id="c1", page=2, per_page=25)
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["campaign_id"] == "c1"
            assert kwargs["params"]["page"] == 2
            assert kwargs["params"]["per_page"] == 25


# ------------------------------------------------------------------
# Connections
# ------------------------------------------------------------------


class TestConnections:
    def test_get_connections(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response([])
        ):
            result = client.get_connections()
            assert result == []


# ------------------------------------------------------------------
# Team
# ------------------------------------------------------------------


class TestTeam:
    def test_get_team_members(self, client, mock_response):
        members = [{"id": "m1", "name": "Paul Hoskins"}]
        with patch.object(
            client.session, "request", return_value=mock_response(members)
        ):
            result = client.get_team_members()
            assert result == members

    def test_get_member_connections(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response([])
        ) as mock_req:
            client.get_member_connections(member_id="m1")
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["member_id"] == "m1"


# ------------------------------------------------------------------
# Activity
# ------------------------------------------------------------------


class TestActivity:
    def test_get_last_actions(self, client, mock_response):
        actions = [{"type": "connection_request", "lead": "l1"}]
        with patch.object(
            client.session, "request", return_value=mock_response(actions)
        ):
            result = client.get_last_actions()
            assert result == actions


# ------------------------------------------------------------------
# User
# ------------------------------------------------------------------


class TestUser:
    def test_get_me(self, client, mock_response):
        user = {"id": "u1", "email": "paul@proactioncto.com"}
        with patch.object(
            client.session, "request", return_value=mock_response(user)
        ):
            result = client.get_me()
            assert result == user


# ------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------


class TestErrorHandling:
    def test_http_error_raised(self, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized")
        with patch.object(client.session, "request", return_value=mock_resp):
            with pytest.raises(Exception, match="401 Unauthorized"):
                client.get_campaigns()
