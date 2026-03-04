"""Unit tests for MeetAlfredClient — all HTTP calls are mocked."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from meetalfred_mcp.client import DEFAULT_BASE_URL, DEFAULT_API_BASE_URL, MeetAlfredClient


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a client with a dummy API key."""
    return MeetAlfredClient(api_key="test-api-key-12345")


@pytest.fixture
def jwt_client():
    """Create a client with both webhook API key and JWT token."""
    return MeetAlfredClient(
        api_key="test-api-key-12345",
        jwt_token="test-jwt-token-abc",
    )


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

    def test_jwt_token_from_constructor(self):
        c = MeetAlfredClient(api_key="k", jwt_token="my-jwt")
        assert c.jwt_token == "my-jwt"

    def test_jwt_token_from_env(self):
        env = {"MEETALFRED_API_KEY": "k", "MEETALFRED_JWT_TOKEN": "env-jwt"}
        with patch.dict(os.environ, env, clear=True):
            c = MeetAlfredClient()
            assert c.jwt_token == "env-jwt"

    def test_api_base_url_default(self, client):
        assert client.api_base_url == DEFAULT_API_BASE_URL

    def test_api_base_url_custom(self):
        c = MeetAlfredClient(
            api_key="k",
            api_base_url="https://api.custom.com/api/v1/",
        )
        assert c.api_base_url == "https://api.custom.com/api/v1"

    def test_require_jwt_raises(self, client):
        """Internal API calls without JWT should raise."""
        with pytest.raises(ValueError, match="JWT token required"):
            client.get_all_tags()

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


# ==================================================================
# Internal API tests (JWT auth)
# ==================================================================


class TestApiRequest:
    def test_api_request_uses_bearer_auth(self, jwt_client, mock_response):
        """Verify internal API uses Authorization: Bearer header."""
        with patch.object(
            jwt_client.session, "request", return_value=mock_response([])
        ) as mock_req:
            jwt_client.get_all_tags()
            _, kwargs = mock_req.call_args
            assert kwargs["headers"]["Authorization"] == "Bearer test-jwt-token-abc"

    def test_api_request_no_webhook_key(self, jwt_client, mock_response):
        """Internal API should NOT include webhook_key in params."""
        with patch.object(
            jwt_client.session, "request", return_value=mock_response([])
        ) as mock_req:
            jwt_client.get_all_tags()
            _, kwargs = mock_req.call_args
            assert kwargs.get("params") is None or "webhook_key" not in (kwargs.get("params") or {})

    def test_api_request_uses_api_base_url(self, jwt_client, mock_response):
        """Internal API should use api_base_url, not webhook base_url."""
        with patch.object(
            jwt_client.session, "request", return_value=mock_response([])
        ) as mock_req:
            jwt_client.get_all_tags()
            args, _ = mock_req.call_args
            assert DEFAULT_API_BASE_URL in args[1]


# ------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------


class TestTags:
    def test_get_all_tags(self, jwt_client, mock_response):
        tags = [{"id": 1, "tag": "VIP"}, {"id": 2, "tag": "Lead"}]
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(tags)
        ):
            result = jwt_client.get_all_tags()
            assert result == tags

    def test_list_tags(self, jwt_client, mock_response):
        data = {"data": [{"id": 1, "tag": "VIP"}], "total": 1}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = jwt_client.list_tags(page=2, per_page=10)
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["page"] == 2
            assert kwargs["params"]["perPage"] == 10
            assert kwargs["params"]["sortField"] == "tag"
            assert kwargs["params"]["sortOrder"] == "ASC"

    def test_create_tag(self, jwt_client, mock_response):
        created = {"id": 3, "tag": "Prospect"}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(created)
        ) as mock_req:
            result = jwt_client.create_tag(name="Prospect")
            assert result == created
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert kwargs["json"]["tag"] == "Prospect"

    def test_update_tag(self, jwt_client, mock_response):
        updated = {"id": 1, "tag": "Important"}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(updated)
        ) as mock_req:
            result = jwt_client.update_tag(tag_id=1, name="Important")
            assert result == updated
            args, kwargs = mock_req.call_args
            assert args[0] == "PUT"
            assert "/tags/1" in args[1]
            assert kwargs["json"]["tag"] == "Important"

    def test_delete_tag(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.delete_tag(tag_id=5)
            args, _ = mock_req.call_args
            assert args[0] == "DELETE"
            assert "/tags/5" in args[1]


# ------------------------------------------------------------------
# Campaigns (internal API)
# ------------------------------------------------------------------


class TestCampaignsInternal:
    def test_list_campaigns_detailed(self, jwt_client, mock_response):
        data = {"data": [{"id": 100, "label": "Test Campaign"}], "total": 1}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = jwt_client.list_campaigns_detailed(status="active", category="linkedin")
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["status"] == "active"
            assert kwargs["params"]["category"] == "linkedin"
            assert kwargs["params"]["sortField"] == "createdAt"
            assert kwargs["params"]["sortOrder"] == "DESC"

    def test_list_campaigns_detailed_with_search(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({"data": []})
        ) as mock_req:
            jwt_client.list_campaigns_detailed(search="recruiter", run_state="running")
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["search"] == "recruiter"
            assert kwargs["params"]["runState"] == "running"

    def test_get_campaign(self, jwt_client, mock_response):
        campaign = {"id": 100, "label": "Test", "steps": []}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(campaign)
        ) as mock_req:
            result = jwt_client.get_campaign(campaign_id=100)
            assert result == campaign
            args, _ = mock_req.call_args
            assert "/campaigns/100" in args[1]

    def test_get_campaign_counts(self, jwt_client, mock_response):
        counts = {"active": 3, "draft": 1, "archived": 2}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(counts)
        ) as mock_req:
            result = jwt_client.get_campaign_counts(category="email")
            assert result == counts
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["category"] == "email"

    def test_update_campaign(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({"id": 100})
        ) as mock_req:
            jwt_client.update_campaign(campaign_id=100, label="Renamed", status="archived")
            args, kwargs = mock_req.call_args
            assert args[0] == "PUT"
            assert "/campaigns/100" in args[1]
            assert kwargs["json"]["label"] == "Renamed"
            assert kwargs["json"]["status"] == "archived"

    def test_delete_campaign(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.delete_campaign(campaign_id=100)
            args, _ = mock_req.call_args
            assert args[0] == "DELETE"
            assert "/campaigns/100" in args[1]


# ------------------------------------------------------------------
# Replies (internal API)
# ------------------------------------------------------------------


class TestRepliesInternal:
    def test_list_replies_detailed(self, jwt_client, mock_response):
        data = {"data": [{"name": "Jane", "message": "Thanks!"}], "total": 1}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = jwt_client.list_replies_detailed(page=1, per_page=10)
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["page"] == 1
            assert kwargs["params"]["perPage"] == 10
            assert kwargs["params"]["sortField"] == "date"
            assert kwargs["params"]["sortOrder"] == "DESC"


# ------------------------------------------------------------------
# User
# ------------------------------------------------------------------


class TestCampaignOperations:
    def test_pause_campaign(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.pause_campaign(campaign_id=100)
            args, kwargs = mock_req.call_args
            assert args[0] == "PATCH"
            assert "/campaigns/100/running-state" in args[1]
            assert kwargs["json"]["runState"] == "paused"

    def test_resume_campaign(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.resume_campaign(campaign_id=100)
            args, kwargs = mock_req.call_args
            assert args[0] == "PATCH"
            assert kwargs["json"]["runState"] == "running"

    def test_rename_campaign(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.rename_campaign(campaign_id=100, name="New Name")
            args, kwargs = mock_req.call_args
            assert args[0] == "PATCH"
            assert "/campaigns/100/name" in args[1]
            assert kwargs["json"]["name"] == "New Name"

    def test_clone_campaign(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({"id": 200})
        ) as mock_req:
            result = jwt_client.clone_campaign(campaign_id=100)
            assert result == {"id": 200}
            args, _ = mock_req.call_args
            assert args[0] == "POST"
            assert "/campaigns/100/clone" in args[1]

    def test_archive_campaign(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.archive_campaign(campaign_id=100)
            args, _ = mock_req.call_args
            assert args[0] == "PATCH"
            assert "/campaigns/100/archive" in args[1]

    def test_get_campaigns_grouped(self, jwt_client, mock_response):
        data = [{"category": "linkedin", "campaigns": []}]
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(data)
        ):
            result = jwt_client.get_campaigns_grouped()
            assert result == data


# ------------------------------------------------------------------
# Conversations / Messaging
# ------------------------------------------------------------------


class TestConversations:
    def test_get_conversation_messages(self, jwt_client, mock_response):
        messages = [{"text": "Hello", "createdAt": "2026-03-01T10:00:00Z"}]
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(messages)
        ) as mock_req:
            result = jwt_client.get_conversation_messages(
                conversation_id="conv-123", entity_urn="urn:li:abc"
            )
            assert result == messages
            args, kwargs = mock_req.call_args
            assert "/conversations/conv-123/messages" in args[1]
            assert kwargs["params"]["entityUrn"] == "urn:li:abc"

    def test_send_message(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({"sent": True})
        ) as mock_req:
            result = jwt_client.send_message(
                conversation_id="conv-123", message="Thanks for connecting!"
            )
            assert result == {"sent": True}
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert "/conversations/messages" in args[1]
            assert kwargs["json"]["conversationId"] == "conv-123"
            assert kwargs["json"]["message"] == "Thanks for connecting!"


# ------------------------------------------------------------------
# Lead Management (internal API)
# ------------------------------------------------------------------


class TestLeadManagement:
    def test_get_campaign_leads(self, jwt_client, mock_response):
        data = {"total": 215, "leads": [{"entityUrn": "abc"}]}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = jwt_client.get_campaign_leads(
                campaign_id=100, lead_type="connected", page=2
            )
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["type"] == "connected"
            assert kwargs["params"]["page"] == 2

    def test_get_lead_statuses(self, jwt_client, mock_response):
        data = {"leadsCount": 215, "repliesCount": 10}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = jwt_client.get_lead_statuses(campaign_id=100)
            assert result == data
            args, _ = mock_req.call_args
            assert "/leads/campaign/100/statuses" in args[1]

    def test_return_lead_to_campaign_with_id(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.return_lead_to_campaign(
                entity_urns=["urn1", "urn2"], campaign_id=100
            )
            args, kwargs = mock_req.call_args
            assert args[0] == "PATCH"
            assert "/leads/campaign/100/return" in args[1]
            assert kwargs["json"]["entityUrns"] == ["urn1", "urn2"]

    def test_return_lead_to_campaign_batch(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.return_lead_to_campaign(entity_urns=["urn1"])
            args, kwargs = mock_req.call_args
            assert "/leads/return-to-campaign" in args[1]

    def test_add_tags_to_leads(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.add_tags_to_leads(
                entity_urns=["urn1", "urn2"], tag_ids=[1, 2]
            )
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert "/leads/add-tags" in args[1]
            assert kwargs["json"]["entityUrns"] == ["urn1", "urn2"]
            assert kwargs["json"]["tagIds"] == [1, 2]

    def test_set_lead_tags(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.set_lead_tags(entity_urn="urn1", tag_ids=[3, 4])
            args, kwargs = mock_req.call_args
            assert args[0] == "PUT"
            assert "/leads/urn1/set-tags" in args[1]
            assert kwargs["json"]["tagIds"] == [3, 4]

    def test_exclude_leads(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.exclude_leads(entity_urns=["urn1"], exclude=True)
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert "/leads/exclude" in args[1]
            assert kwargs["json"]["exclude"] is True


# ------------------------------------------------------------------
# Notifications
# ------------------------------------------------------------------


class TestNotifications:
    def test_get_notifications(self, jwt_client, mock_response):
        data = {"notifications": [], "total": 0}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(data)
        ) as mock_req:
            result = jwt_client.get_notifications(page=1, per_page=10)
            assert result == data
            _, kwargs = mock_req.call_args
            assert kwargs["params"]["page"] == 1
            assert kwargs["params"]["perPage"] == 10

    def test_get_unread_count(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({"count": 5})
        ):
            result = jwt_client.get_unread_notification_count()
            assert result == {"count": 5}

    def test_mark_all_read(self, jwt_client, mock_response):
        with patch.object(
            jwt_client.session, "request", return_value=mock_response({})
        ) as mock_req:
            jwt_client.mark_all_notifications_read()
            args, _ = mock_req.call_args
            assert args[0] == "PATCH"


# ------------------------------------------------------------------
# User
# ------------------------------------------------------------------


class TestUser:
    def test_get_current_user(self, jwt_client, mock_response):
        user = {"id": 940316, "name": "Paul Hoskins"}
        with patch.object(
            jwt_client.session, "request", return_value=mock_response(user)
        ) as mock_req:
            result = jwt_client.get_current_user()
            assert result == user
            args, _ = mock_req.call_args
            assert "/users/me" in args[1]
