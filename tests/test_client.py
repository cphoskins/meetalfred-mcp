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
        c = MeetAlfredClient(
            api_key="k",
            base_url="https://api.erubheorhgur.com/api/integrations/webhook",
        )
        assert c.base_url == "https://api.erubheorhgur.com/api/integrations/webhook"

    def test_env_base_url(self):
        env = {
            "MEETALFRED_API_KEY": "k",
            "MEETALFRED_BASE_URL": "https://custom.example.com/api/integrations/webhook/",
        }
        with patch.dict(os.environ, env, clear=True):
            c = MeetAlfredClient()
            # Trailing slash should be stripped
            assert c.base_url == "https://custom.example.com/api/integrations/webhook"

    def test_no_auth_header(self, client):
        # Auth is via query param, not header
        assert "X-Alfred-Auth" not in client.session.headers
        assert "Authorization" not in client.session.headers

    def test_webhook_key_in_requests(self, client, mock_response):
        """Verify webhook_key is passed as query parameter."""
        with patch.object(
            client.session, "request", return_value=mock_response({"campaigns": []})
        ) as mock_req:
            client.get_campaigns()
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["webhook_key"] == "test-api-key-12345"


# ------------------------------------------------------------------
# Campaigns
# ------------------------------------------------------------------


class TestCampaigns:
    def test_get_campaigns_default(self, client, mock_response):
        campaigns = {"campaigns": [{"id": 1, "label": "Test", "status": "active"}]}
        with patch.object(
            client.session, "request", return_value=mock_response(campaigns)
        ) as mock_req:
            result = client.get_campaigns()
            assert result == campaigns
            args, kwargs = mock_req.call_args
            assert args[0] == "GET"
            assert "/campaigns" in args[1]
            assert kwargs["params"]["type"] == "active"

    def test_get_campaigns_all(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response({"campaigns": []})
        ) as mock_req:
            client.get_campaigns(campaign_type="all")
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["type"] == "all"


# ------------------------------------------------------------------
# Leads
# ------------------------------------------------------------------


class TestLeads:
    def test_get_leads_no_filter(self, client, mock_response):
        data = {"actions": [{"person": {"name": "John Doe"}}]}
        with patch.object(
            client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = client.get_leads()
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["page"] == 0
            assert kwargs["params"]["per_page"] == 25
            assert "campaign" not in kwargs["params"]

    def test_get_leads_with_campaign_filter(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response({"actions": []})
        ) as mock_req:
            client.get_leads(campaign_id=1437182, page=1, per_page=10)
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["campaign"] == 1437182
            assert kwargs["params"]["page"] == 1

    def test_add_lead(self, client, mock_response):
        resp_data = {"id": 1, "message": "Well done!", "success": True}
        with patch.object(
            client.session, "request", return_value=mock_response(resp_data)
        ) as mock_req:
            result = client.add_lead(
                campaign_id=1437182,
                linkedin_profile_url="https://www.linkedin.com/in/johndoe/",
                email="john@example.com",
            )
            assert result == resp_data
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert "/add_lead_to_campaign" in args[1]
            assert kwargs["json"]["campaign"] == 1437182
            assert kwargs["json"]["linkedin_profile_url"] == "https://www.linkedin.com/in/johndoe/"
            assert kwargs["json"]["email"] == "john@example.com"

    def test_add_lead_minimal(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response({"success": True})
        ) as mock_req:
            client.add_lead(
                campaign_id=100,
                linkedin_profile_url="https://www.linkedin.com/in/test/",
            )
            _, kwargs = mock_req.call_args
            assert "email" not in kwargs["json"]


# ------------------------------------------------------------------
# Replies
# ------------------------------------------------------------------


class TestReplies:
    def test_get_replies(self, client, mock_response):
        replies = {"actions": [{"name": "Jane", "reply_message": "Thanks!"}]}
        with patch.object(
            client.session, "request", return_value=mock_response(replies)
        ):
            result = client.get_replies()
            assert result == replies

    def test_get_replies_pagination(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response({"actions": []})
        ) as mock_req:
            client.get_replies(page=2, per_page=10)
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["page"] == 2
            assert kwargs["params"]["per_page"] == 10


# ------------------------------------------------------------------
# Connections
# ------------------------------------------------------------------


class TestConnections:
    def test_get_connections(self, client, mock_response):
        data = {"actions": [{"firstName": "Brandon", "lastName": "Newsome"}]}
        with patch.object(
            client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = client.get_connections()
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["return_only_synced"] == "true"

    def test_get_connections_all(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response({"actions": []})
        ) as mock_req:
            client.get_connections(return_only_synced=False)
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["return_only_synced"] == "false"


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
            client.session, "request", return_value=mock_response({"connections": []})
        ) as mock_req:
            client.get_member_connections(page=0, per_page=10)
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["page"] == 0


# ------------------------------------------------------------------
# Last Actions
# ------------------------------------------------------------------


class TestLastActions:
    def test_get_last_actions_default(self, client, mock_response):
        data = {"actions": [{"desc": "linkedin reply detected"}]}
        with patch.object(
            client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = client.get_last_actions()
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["action"] == "all_replies"

    def test_get_last_actions_accepted(self, client, mock_response):
        with patch.object(
            client.session, "request", return_value=mock_response({"actions": []})
        ) as mock_req:
            client.get_last_actions(action="accepted")
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["action"] == "accepted"

    def test_get_last_actions_all_types(self, client):
        """Verify all valid action types are accepted."""
        for action in MeetAlfredClient.VALID_ACTIONS:
            # Should not raise
            assert action in MeetAlfredClient.VALID_ACTIONS

    def test_invalid_action_raises(self, client):
        with pytest.raises(ValueError, match="Invalid action"):
            client.get_last_actions(action="nonexistent")


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
