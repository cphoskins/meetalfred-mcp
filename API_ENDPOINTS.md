# MeetAlfred Internal API Endpoints

Discovered 2026-03-04 by inspecting the MeetAlfred SPA at `proactivebda.ai` (white-label).

## API Architecture

| Client | Base URL | Auth | Description |
|--------|----------|------|-------------|
| **v1** (`_`) | `https://api.erubheorhgur.com/api/v1` | `Authorization: Bearer <JWT>` | Primary API -- all campaign, lead, conversation, tag, and user operations |
| **v2** (`S1`) | `https://api.erubheorhgur.com/api/v2` | `Authorization: Bearer <JWT>` | New inbox/conversation list endpoint |
| **base** (`So`) | `https://api.erubheorhgur.com/api` | `Authorization: Bearer <JWT>` | Salesforce integrations only |
| **webhook** | `https://api.meetalfred.com/api/integrations/webhook` | `?webhook_key=<key>` | Read-only webhook API (already implemented in client.py) |

The JWT token is stored in a cookie named `token` on the `proactivebda.ai` domain. The JWT payload contains `sub` (user ID), `name`, `iat`, and `exp`. Expiration is ~1 year from issuance.

The frontend is a React SPA using **axios** for HTTP requests. The axios instances are configured with interceptors that automatically attach the JWT from cookie storage.

For the white-label deployment at `proactivebda.ai`, the API base is `api.erubheorhgur.com`. For the canonical `app.meetalfred.com` deployment, the base is `api.meetalfred.com`. The JS bundle selects between them based on the hostname.

---

## Priority Endpoints (Requested Features)

### 1. Reply Sending (via Inbox Conversations)

There is no direct "reply to a campaign reply" endpoint. Instead, replies are sent through the **conversation messaging** system:

#### List Conversations (v2 -- preferred for inbox)

```
GET /api/v2/conversations?filters=&search=&nextCursor=
```

**Response:**
```json
{
  "me": {
    "entityUrn": "ACoAAAAplVMBH42CGnvu5zC8QBcErojshgF3Lqs",
    "objectUrn": "2725203",
    "firstName": "Paul",
    "lastName": "Hoskins",
    "headline": "...",
    "imageUrl": "..."
  },
  "pagination": {
    "nextCursor": "REVTQ0VORElORyYx..."
  },
  "data": [
    {
      "conversationId": "2-OGVmZmUzODktNTIzNS00N2IyLWJhOGEtODFjZDQxMjgyYjY5XzEwMA==",
      "participants": [
        {
          "entityUrn": "ACoAAAYlxhcBNiwi...",
          "objectUrn": "103138839",
          "firstName": "Erika",
          "lastName": "Colon",
          "headline": "CEO UP TALENT LLC.",
          "imageUrl": "..."
        }
      ],
      "from": "ACoAAAYlxhcBNiwi...",
      "isGroup": false,
      "lastActivityAt": 1772590428738,
      "content": "Hi Erika, ...",
      "unreadCount": 0,
      "isSponsored": false,
      "isLinkedinOffer": false,
      "groupTitle": null
    }
  ]
}
```

**Query params:** `filters` (string), `search` (string), `nextCursor` (pagination token).

#### Get Conversation Messages

```
GET /api/v1/conversations/{conversationId}/messages?entityUrn=&createdBefore=
```

**Response:**
```json
{
  "metadata": { "participants": [] },
  "elements": [
    {
      "createdAt": 1772465328109,
      "dashEntityUrn": "urn:li:fsd_message:...",
      "entityUrn": "urn:li:fs_event:(...)",
      "eventContent": {
        "com.linkedin.voyager.messaging.event.MessageEvent": {
          "body": "",
          "attributedBody": {
            "text": "Thank you for the info Paul..."
          }
        }
      },
      "subtype": "MEMBER_TO_MEMBER",
      "from": {
        "com.linkedin.voyager.messaging.MessagingMember": {
          "miniProfile": {
            "firstName": "Shenikwa",
            "lastName": "Novachich",
            "entityUrn": "urn:li:fs_miniProfile:ACoAAAsmi-EB...",
            "publicIdentifier": "shenikwa-novachich-39579952"
          }
        }
      },
      "quickReplyRecommendations": [...]
    }
  ]
}
```

#### Send Message (LinkedIn regular)

```
POST /api/v1/conversations/messages
```

**Request body** (passed directly as `e` argument):
```json
{
  "conversationId": "2-NjA5OTI3ZDktZTI4NS00YjhiLWE3YWItMzhjMmYxMTFjOWI0XzEwMA==",
  "message": "Thanks for getting back to me! ..."
}
```

*Note: The JS source shows `aE=e=>_.post("/conversations/messages",e)` -- the body `e` is passed directly.*

#### Send Message with Attachment

```
POST /api/v1/conversations/{conversationId}/message-with-attachment
Content-Type: multipart/form-data
```

**Request body:** FormData with `files` and `message` fields.

*JS source: `sE=({conversationId:e,files:r,message:n})=>{const a=wo({files:r,message:n});return _.post(\`/conversations/${e}/message-with-attachment\`,a)}`*

#### Send Sales Navigator Message

```
POST /api/v1/conversations/{conversationId}/send-sn-message
```

**Request body:**
```json
{
  "message": "Your message text here"
}
```

#### Modify Conversation (mark read/archive)

```
POST /api/v1/conversations/{conversationId}/modify
```

**Request body:**
```json
{
  "action": "markRead",
  "isSales": false
}
```

*`action` values likely include: `markRead`, `markUnread`, `archive`, `unarchive`.*

#### Get Sales Navigator Conversations

```
GET /api/v1/conversations/sn-conversations?query=&createdBefore=
```

#### Get Sales Navigator Messages

```
GET /api/v1/conversations/{conversationId}/sn-messages
```

---

### 2. Return-to-Campaign

Two variants exist:

#### Return Lead to Specific Campaign

```
PATCH /api/v1/leads/campaign/{campaignId}/return
```

**Request body** (second argument `r`):
```json
{
  "entityUrns": ["ACoAAAsmi-EB..."],
  "touchIndex": 0
}
```

*Note: The `r` body structure is not 100% clear from minified source, but it takes some body parameter. This likely contains the lead entityUrns and possibly a touch index to resume from.*

#### Return Multiple Leads to Their Campaigns (batch)

```
PATCH /api/v1/leads/return-to-campaign
```

**Request body:**
```json
{
  "entityUrns": ["ACoAAAsmi-EB...", "ACoAAADYemQB..."]
}
```

*JS source: `$E=e=>_.patch("/leads/return-to-campaign",{entityUrns:e})` -- takes an array of entityUrns.*

---

### 3. Campaign Creation

Campaign creation is a multi-step flow:

#### Step 1: Create Campaign with Audience

```
POST /api/v1/campaigns/audience
```

**Request body** (the `e` argument contains the full campaign config):
This is the primary campaign creation endpoint. The body likely includes:
```json
{
  "name": "Campaign Name",
  "category": "linkedin",
  "campaignType": "sales navigator saved search",
  "searchParameters": {
    "keywords": "",
    "connections": { "first": false, "second": false, "third": false },
    "profileLanguages": { "english": false, ... },
    "specifyKeywords": { "firstName": "", "lastName": "", "title": "", "company": "", "school": "" },
    "industries": [],
    "currentCompanies": [],
    "pastCompanies": [],
    "schools": [],
    "locations": [],
    "companyPublicIdentifier": "",
    "eventUrl": ""
  },
  "salesNavigatorUrl": "https://www.linkedin.com/sales/search/people?savedSearchId=...",
  "touchSequence": {
    "sequence": [
      {
        "type": "LI View",
        "delay_time_unit": "day(s)",
        "delay_number": 1,
        "message": "",
        "followup_message": "",
        "subject": "",
        "connect_followup": false,
        "revoke_invite": false,
        "days_til_revoke": 0,
        "auto_endorse": false,
        "auto_post_like": false,
        "auto_follow": false,
        "view": true,
        "endorsements_count": 1,
        "posts_count": 1,
        "tags": [],
        "attachments": [],
        "proceed_to_next": false,
        "gmail_signature": false,
        "auto_follow_twitter": false
      },
      {
        "type": "LI Connect",
        "delay_time_unit": "day(s)",
        "delay_number": 1,
        "message": "Hi {{first_name}}, ...",
        "followup_message": "{{first_name}}, ...",
        "connect_followup": true,
        "tags": [],
        "attachments": []
      },
      {
        "type": "LI Message",
        "delay_time_unit": "day(s)",
        "delay_number": 3,
        "message": "Hi {{first_name}}, ...",
        "tags": []
      }
    ]
  },
  "excludeNoPhotos": false,
  "premiumOnly": false,
  "openLinkOnly": false,
  "excludeInvitedProfiles": true,
  "maxSearchAmount": 2500,
  "autoApproveLeads": true,
  "getNewLeads": true,
  "isLinkedinOnly": true,
  "includeMessageOnly": true,
  "noFirstConnections": false,
  "retargetLeads": false
}
```

**Touch sequence `type` values (observed):**
- `"LI View"` -- View profile (optionally endorse, like posts, follow)
- `"LI Connect"` -- Send connection request with message + optional follow-up message
- `"LI Message"` -- Send direct message (to already-connected leads)
- Email, Twitter, InMail types also exist (see campaign categories)

**Template variables:** `{{first_name}}`, `{{last_name}}`, `{{company}}`, `{{title}}`, etc.

#### Step 1b: Create from CSV

```
POST /api/v1/campaigns/linked-in/audience/csv   (LinkedIn campaigns)
POST /api/v1/campaigns/email/audience/csv        (Email campaigns)
POST /api/v1/campaigns/twitter/audience/csv      (Twitter campaigns)
```

#### Step 1c: Create from Connections

```
POST /api/v1/campaigns/{campaignId}/audience/connections
POST /api/v1/campaigns/{campaignId}/audience/sales-explorer-connections
```

#### Step 2: Publish Campaign

```
POST /api/v1/campaigns/{campaignId}/publish
```

**Request body** (second argument `r`):
```json
{}
```

*This moves the campaign from draft to active.*

#### Update Campaign Audience (after creation)

```
PATCH /api/v1/campaigns/{campaignId}/audience
```

#### Update Campaign Sequence

```
PATCH /api/v1/campaigns/{campaignId}/sequence
```

**Request body:**
```json
{
  "touchSequence": { "sequence": [...] }
}
```

#### Update Campaign Running State (pause/resume)

```
PATCH /api/v1/campaigns/{campaignId}/running-state
```

**Request body:**
```json
{
  "runState": "running"
}
```

*Values: `"running"`, `"paused"`.*

#### Other Campaign Operations

```
PATCH /api/v1/campaigns/{campaignId}/name          -- Rename
PATCH /api/v1/campaigns/{campaignId}/archive        -- Archive/unarchive
PATCH /api/v1/campaigns/{campaignId}/restart-search -- Restart lead search
POST  /api/v1/campaigns/{campaignId}/clone          -- Clone campaign
DELETE /api/v1/campaigns/{campaignId}               -- Delete campaign
```

---

## All Discovered Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/sign-in` | Sign in |
| POST | `/auth/sign-up` | Sign up |
| POST | `/auth/forgot-password` | Forgot password |
| PATCH | `/auth/set-new-password/{token}` | Set new password |
| POST | `/auth/send-verification-link` | Send email verification link |
| PATCH | `/auth/verify-email/{token}` | Verify email |
| GET | `/auth/microsoft/code-url` | Get Microsoft OAuth URL |
| POST | `/auth/exchange/{token}` | Exchange token |

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/me` | Current user profile |
| GET | `/users/me/real` | Real (non-impersonated) user |
| POST | `/users/me/bots` | Bot status update |
| GET | `/users/email` | User email info |
| GET | `/users/signature` | Email signature |
| PATCH | `/users/signature` | Update email signature |
| GET | `/users/me/linked-in` | LinkedIn profile info |
| GET | `/users/preferences` | User preferences |
| GET | `/users/me/referral` | Referral info |
| POST | `/users/change-password` | Change password |
| PATCH | `/users/change-email` | Change email |
| PATCH | `/users/edit-auto-withdraw` | Update auto-withdrawal settings |
| PATCH | `/users/edit-daily-limits` | Update daily limits |
| PATCH | `/users/edit-greetings` | Update greeting settings |
| PATCH | `/users/edit-operating-hours` | Update work hours |
| PATCH | `/users/set-cloud-timezone` | Set timezone |
| POST | `/users/impersonate` | Impersonate user (team admin) |
| POST | `/users/stop-impersonating` | Stop impersonating |
| PATCH | `/users/update` | Update user profile |
| POST | `/users/set-contract-id` | Set Sales Navigator contract |
| PATCH | `/users/language` | Set language |
| PATCH | `/users/me/complete-walkthrough` | Mark walkthrough complete |
| PATCH | `users/set-credentials` | Set credentials |
| POST | `/users/me/unsubscribed-emails/csv` | Export unsubscribed emails |
| PATCH | `/users/me/toggle-unsubscribe-link` | Toggle unsubscribe link |
| GET | `/users/me/mail-settings` | Get mail settings |
| PUT | `/users/me/mail-settings` | Update mail settings |
| DELETE | `/users/me/mail-settings` | Delete mail settings |
| GET | `/users/me/invites-restriction` | Get invite restrictions |
| GET | `/users/me/cloud-bot-info` | Get cloud bot info |
| POST | `/users/integrations/test-email` | Test email integration |
| POST | `/users/apply-se-waitlist` | Apply for Sales Explorer waitlist |
| GET | `/users/saved-searches` | Get saved LinkedIn searches |
| PATCH | `/users/refresh-saved-searches` | Refresh saved searches |

### Features

| Method | Path | Description |
|--------|------|-------------|
| GET | `/me/features` | Feature flags for current user |

### Campaigns

| Method | Path | Description |
|--------|------|-------------|
| GET | `/campaigns` | List campaigns (params: category, status, page, perPage, sortField, sortOrder, search, runState, filter) |
| GET | `/campaigns/{id}` | Get campaign detail (param: countIgnoredLeads=true) |
| GET | `/campaigns/counts` | Campaign counts by status (param: category) |
| GET | `/campaigns/grouped` | All campaigns grouped by category |
| GET | `/campaigns/dashboard` | Dashboard view with campaign data |
| GET | `/campaigns/statistics` | Campaign statistics |
| GET | `/campaigns/search-list` | Campaign search list |
| GET | `/campaigns/search-list/connections` | Campaign connections search list |
| GET | `/campaigns/{id}/search-list/ignored` | Ignored leads in search |
| GET | `/campaigns/{id}/list-item` | Campaign list item |
| GET | `/campaigns/{id}/activity/chart` | Activity chart data |
| GET | `/campaigns/{id}/actions` | Campaign actions (params) |
| GET | `/campaigns/{id}/progress` | Campaign progress |
| GET | `/campaigns/{id}/sequence-progress` | Sequence progress |
| POST | `/campaigns/audience` | **Create campaign** |
| POST | `/campaigns/linked-in/audience/csv` | Create LinkedIn campaign from CSV |
| POST | `/campaigns/email/audience/csv` | Create email campaign from CSV |
| POST | `/campaigns/twitter/audience/csv` | Create Twitter campaign from CSV |
| PATCH | `/campaigns/{id}/{sourceId}/audience/csv` | Update campaign audience from CSV |
| POST | `/campaigns/{id}/audience/connections` | Add connections as audience |
| POST | `/campaigns/{id}/audience/sales-explorer-connections` | Add Sales Nav connections |
| PATCH | `/campaigns/{id}/{sourceId}/audience/connections` | Update audience connections |
| PATCH | `/campaigns/{id}/{sourceId}/audience/sales-explorer-connections` | Update SN audience |
| POST | `/campaigns/{id}/publish` | **Publish campaign** (draft -> active) |
| PATCH | `/campaigns/{id}/audience` | Update campaign audience |
| PATCH | `/campaigns/{id}/running-state` | **Pause/resume** (body: `{runState: "running"|"paused"}`) |
| PATCH | `/campaigns/{id}/sequence` | Update touch sequence |
| PATCH | `/campaigns/{id}/archive` | Archive/unarchive |
| PATCH | `/campaigns/{id}/name` | Rename campaign |
| PATCH | `/campaigns/{id}/restart-search` | Restart lead search |
| POST | `/campaigns/{id}/clone` | Clone campaign |
| DELETE | `/campaigns/{id}` | Delete campaign |
| POST | `/campaigns/interactive-questions` | Interactive questions (AI?) |
| GET | `/campaigns/activity` | Campaign activity (params) |
| GET | `/campaigns/replies` | **List replies** (params: page, perPage, sortField, sortOrder) |
| POST | `/campaigns/replies/csv` | Export replies as CSV |
| POST | `/campaigns/{id}/activity/csv` | Export activity as CSV |
| GET | `/search/autocomplete` | Search autocomplete |

### Leads

| Method | Path | Description |
|--------|------|-------------|
| POST | `/leads` | Create a lead |
| GET | `/leads/{entityUrn}?objectUrn=` | Get lead detail |
| PATCH | `/leads/{entityUrn}` | Update lead |
| POST | `/leads/add-tags` | Add tags to leads (body: `{entityUrns: [...], tagIds: [...]}`) |
| PUT | `/leads/{entityUrn}/set-tags` | Set tags on lead (body: `{tagIds: [...]}`) |
| PUT | `/leads/{entityUrn}/create-set-tag` | Create and set tag on lead |
| PATCH | `/leads/{entityUrn}/tags` | Update lead tags (body: `{tagIds: [...]}`) |
| GET | `/leads/campaign/{campaignId}/statuses` | Lead status counts for campaign |
| GET | `/leads/campaign/{campaignId}` | **List leads in campaign** (params: page, perPage, type, excludedOnly) |
| GET | `/leads/campaign/{campaignId}/all` | All leads in campaign (no pagination) |
| POST | `/leads/csv` | Export leads as CSV (body: `{receiverEmail, entityUrns}`) |
| PATCH | `/leads/{entityUrn}/campaign/{campaignId}/custom-data` | Update lead custom data |
| DELETE | `/leads/{entityUrn}/campaign/{campaignId}/custom-data` | Delete lead custom data |
| PATCH | `/leads/campaign/{campaignId}/skip` | Skip leads in campaign |
| DELETE | `/leads/campaign/{campaignId}/ignored` | Remove from ignored (body: `{entityUrns: [...]}`) |
| DELETE | `/leads/campaign/{campaignId}/ignored/all` | Remove all ignored |
| PATCH | `/leads/campaign/{campaignId}/return` | **Return lead to campaign** |
| PATCH | `/leads/return-to-campaign` | **Batch return to campaign** (body: `{entityUrns: [...]}`) |
| GET | `/leads/campaign/{campaignId}/ignored` | List ignored leads |
| GET | `/leads/{entityUrn}/campaign/{campaignId}/actions` | Lead actions in campaign |
| GET | `/leads/campaign/{campaignId}/zapier` | Zapier integration data |
| POST | `/leads/exclude` | **Exclude leads** (body: `{entityUrns: [...], exclude: true|false}`) |
| GET | `/leads/replied` | Leads that have replied |
| POST | `/leads/campaign/{campaignId}/csv` | Export campaign leads CSV |

**Lead `type` values for campaign leads listing:**
`approved`, `alreadyConnected`, `alreadyInvited`, `viewed`, `requested`, `invitesPending`, `connected`, `followedUp`, `messaged`, `inmailed`, `inmailSkipped`, `replies`, `allReplies`, `inmailReplies`, `eventMessages`, `userInteraction`, `invitesWithdraw`, `emailed`, `emailsBounced`, `emailReplies`, `emailOpened`, `followedTwitter`, `twitterMessageSent`, `groupMessageSent`, `twitterUnableToMessage`, `noEmailFound`, `unableToSendMessage`, `emailUnsubscribed`, `leadPostponed`, `messagePostponed`, `ignored`, `unableToSendInmail`, `inviteToEventFailed`, `inviteToEventSent`, `inviteToCompanyFailed`, `inviteToCompanySent`, `chainedMessagesSent`, `unableToSendChainedMessages`

### Lead Sources

| Method | Path | Description |
|--------|------|-------------|
| POST | `/lead-sources` | Create lead source |
| GET | `/lead-sources/campaign/{campaignId}` | Get lead sources for campaign |
| POST | `/lead-sources/campaign/{campaignId}/audience/sales-explorer-connections` | Add SN connections as source |

### Conversations / Inbox

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/conversations` | **List conversations** (v2 -- params: filters, search, nextCursor) |
| GET | `/conversations/{conversationId}/messages` | **Get messages** (params: entityUrn, createdBefore) |
| POST | `/conversations/messages` | **Send message** (body: `{conversationId, message}`) |
| POST | `/conversations/{conversationId}/message-with-attachment` | Send with attachment (multipart) |
| POST | `/conversations/{conversationId}/send-sn-message` | **Send SN message** (body: `{message}`) |
| POST | `/conversations/{conversationId}/modify` | **Mark read/archive** (body: `{action, isSales}`) |
| GET | `/conversations/sn-conversations` | List SN conversations (params: query, createdBefore) |
| GET | `/conversations/{conversationId}/sn-messages` | Get SN messages |

### Connections

| Method | Path | Description |
|--------|------|-------------|
| GET | `/connections` | List connections (requires entityUrn param) |
| POST | `/connections` | Create connection record |
| POST | `/connections/csv` | Export connections CSV |
| PATCH | `/connections/{entityUrn}` | Update connection |
| PATCH | `/connections/{entityUrn}/notes` | Update connection notes |
| GET | `/connections/{entityUrn}/actions` | Connection actions |
| GET | `/connections/tagged` | Connections by tag (params: selectedTags, page) |

### Tags

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tags/all` | All tags (no pagination) |
| GET | `/tags` | List tags (paginated) |
| POST | `/tags` | Create tag (body: `{tag: "name"}`) |
| PATCH | `/tags/{id}` | Update tag |
| DELETE | `/tags/{id}` | Delete tag |

### Invitations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/invites` | List invitations (paginated) |
| POST | `/invites/change-status` | Change invitation status |

### Notifications

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications/unread-count` | Unread count |
| GET | `/notifications` | List notifications (paginated) |
| PATCH | `/notifications/mark-all-as-read` | Mark all read |
| PATCH | `/notifications/{id}/mark-as-read` | Mark one read |

### Templates

| Method | Path | Description |
|--------|------|-------------|
| GET | `/templates` | List all templates |
| GET | `/templates/personal` | Personal templates |
| GET | `/templates/library` | Template library |
| GET | `/templates/team` | Team templates |
| GET | `/templates/categories` | Template categories |
| POST | `/templates` | Create template |
| PUT | `/templates/{id}` | Update template |
| PATCH | `/templates/{id}/toggle-availability` | Toggle availability |
| DELETE | `/templates/{id}` | Delete template |

### Sequence Templates (Campaign Templates)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sequence-templates` | List sequence templates |
| GET | `/sequence-templates/categories` | Sequence template categories |
| GET | `/sequence-templates/available` | Available sequence templates |
| GET | `/sequence-templates/{id}` | Get sequence template |
| POST | `/sequence-templates` | Create sequence template |
| PATCH | `/sequence-templates/{id}` | Update sequence template |
| PATCH | `/sequence-templates/{id}/toggle-availability` | Toggle availability |
| DELETE | `/sequence-templates/{id}` | Delete sequence template |

### Posts (Social Publishing)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/posts` | List posts |
| GET | `/posts/types` | Post types |
| GET | `/posts/{id}` | Get post |
| POST | `/posts` | Create post |
| PATCH | `/posts/{id}` | Update post |
| PATCH | `/posts/{id}/post-time` | Update post time |
| PATCH | `/posts/{id}/archive` | Archive post |
| DELETE | `/posts/{id}` | Delete post |

### Trends

| Method | Path | Description |
|--------|------|-------------|
| GET | `/trends` | List trends |
| POST | `/trends` | Create trend topic |
| PATCH | `/trends/{id}` | Update trend |
| DELETE | `/trends/{id}` | Delete trend |
| POST | `/trend-posts/{id}/like` | Like a trend post |

### LinkedIn Integration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/linked-in/check-connection` | Check LinkedIn connection status |
| PATCH | `/linked-in/update-credentials` | Update LinkedIn credentials |
| POST | `/linked-in/verify-code` | Verify 2FA code |
| DELETE | `/linked-in/remove-credentials` | Remove LinkedIn credentials |
| GET | `/linked-in/groups` | List LinkedIn groups |
| POST | `/linked-in/groups/refresh` | Refresh groups |
| GET | `/linked-in/events` | List LinkedIn events |
| GET | `/linked-in/companies` | List companies |
| GET | `/linked-in/verify-on-the-fly/{id}` | Verify on the fly status |
| POST | `/linked-in/verify-on-the-fly/` | Start verify on the fly |
| POST | `/linked-in/verify-on-the-fly/verify-code` | Submit verify code |
| POST | `/linked-in/verify-on-the-fly/login` | Login for verify |
| POST | `/linked-in/verify-on-the-fly/test-email` | Test email for verify |

### Email Integration (Gmail/Microsoft)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/gmail/sign-in` | Gmail OAuth sign-in |
| DELETE | `/gmail` | Remove Gmail integration |
| GET | `/gmail/aliases` | Gmail aliases |
| PATCH | `/gmail/aliases` | Update Gmail aliases |
| GET | `/microsoft/outlook/code-url` | Get Microsoft OAuth URL |
| POST | `/microsoft/outlook/sign-in` | Microsoft sign-in |
| DELETE | `/microsoft/outlook` | Remove Microsoft integration |
| POST | `/smtp-settings/test` | Test SMTP settings |

### Twitter Integration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/twitter/auth-url` | Get Twitter auth URL |
| POST | `/twitter/verify-login` | Verify Twitter login |
| GET | `/twitter/details/user` | Get Twitter user details |
| DELETE | `/twitter` | Remove Twitter integration |

### Facebook Integration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/facebook` | Facebook status |
| POST | `/facebook/save-data` | Save Facebook data |
| GET | `/facebook/options` | Facebook options |
| POST | `/facebook/options` | Update Facebook options |
| GET | `/facebook/access-token` | Get access token |
| POST | `/facebook/clear-login` | Clear Facebook login |
| POST | `/facebook/exchange-access-token` | Exchange access token |

### Teams

| Method | Path | Description |
|--------|------|-------------|
| GET | `/teams/{teamId}` | Get team |
| GET | `/teams/members` | List team members |
| GET | `/teams/{teamId}/members` | List members of specific team |
| GET | `/teams/{teamId}/invites` | Team invites |
| POST | `/teams/{teamId}/invites` | Send team invite |
| POST | `/teams/{teamId}/invites/ghost` | Send ghost invite |
| DELETE | `/teams/{teamId}/members/{memberId}` | Remove member |
| DELETE | `/teams/invites/{id}/remove` | Remove invite |
| PATCH | `/teams/{teamId}` | Update team |
| PATCH | `/teams/{teamId}/members/{memberId}` | Update member |
| GET | `/teams/invites/{id}` | Get invite details |
| POST | `/teams/invites/{id}/reject` | Reject invite |
| POST | `/teams/invites/{id}/accept` | Accept invite |
| PATCH | `/teams/toggle-enable-member-inbox` | Toggle member inbox |
| PATCH | `/teams/toggle-share-member-leads` | Toggle lead sharing |
| PATCH | `/teams/toggle-verify-on-the-fly-status` | Toggle verify on the fly |
| PATCH | `/teams/send-disconnected-email` | Send disconnected email |
| GET | `/teams/stats` | Team stats |
| GET | `/teams/stats/{id}` | Team member stats |
| POST | `/teams/leave` | Leave team |
| GET | `/teams/invites/first` | First invite |
| POST | `/teams/invites/{id}/clicked` | Mark invite clicked |
| POST | `/teams/stats/csv` | Export team stats CSV |
| POST | `/teams/members/{id}/move-to-ghost` | Move member to ghost |

### Groups (Lead Groups)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/groups` | List groups (paginated) |
| GET | `/groups/all` | All groups |
| POST | `/groups` | Create group |
| PATCH | `/groups/{id}` | Update group |
| DELETE | `/groups/{id}` | Delete group |
| POST | `/groups/{groupId}/members/{memberId}` | Add member to group |
| DELETE | `/groups/{groupId}/members/{memberId}` | Remove member from group |

### Billing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/billing` | Billing info |
| GET | `/billing/invoices` | List invoices |
| POST | `/billing/subscriptions` | Create subscription |
| PATCH | `/billing/subscriptions` | Update subscription |
| DELETE | `/billing/subscriptions` | Delete subscription |
| POST | `/billing/subscriptions/pause` | Pause subscription |
| POST | `/billing/subscriptions/unpause` | Unpause subscription |
| PATCH | `/billing/subscriptions/resume` | Resume subscription |
| PATCH | `/billing/subscriptions/cancel` | Cancel subscription |
| PATCH | `/billing/subscriptions/apply-discount` | Apply discount |
| POST | `/billing/subscriptions/close-cancel` | Close cancel flow |
| POST | `/billing/subscriptions/payment-confirmed` | Payment confirmed |
| POST | `/billing/subscriptions/payment-failed` | Payment failed |
| PATCH | `/billing/company` | Update billing company |
| PATCH | `/billing/update-card-details` | Update card |
| GET | `/billing/plan-update-invoice` | Plan update invoice preview |
| GET | `/billing/upcoming-invoice` | Upcoming invoice |
| GET | `/billing/plan-price` | Plan pricing |
| GET | `/billing/cancel-discount` | Cancel discount info |

### Salesforce Integration (via `/api` base, not `/api/v1`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/integrations/salesforce/connect` | Connect Salesforce (body: `{code}`) |
| POST | `/integrations/salesforce/export-leads` | Export leads (body: `{leadEntityUrns: [...]}`) |
| POST | `/integrations/salesforce/remove` | Remove Salesforce |

### White Label

| Method | Path | Description |
|--------|------|-------------|
| GET | `/whitelabels` | Get white label config |
| GET | `/whitelabels/branding` | Get branding |
| PATCH | `/whitelabels/branding` | Update branding |
| PATCH | `/whitelabels/toggle-status` | Toggle white label |
| PUT | `/whitelabels/smtp-settings` | Update SMTP |
| PATCH | `/whitelabels/domain` | Update domain |
| DELETE | `/whitelabels/smtp-settings` | Delete SMTP settings |
| DELETE | `/whitelabels/domain` | Delete domain |
| PATCH | `/whitelabels/domain/verify-dns` | Verify DNS |

### Misc

| Method | Path | Description |
|--------|------|-------------|
| GET | `/intercom` | Intercom config |

---

## Key Data Structures

### Campaign Object (from `GET /campaigns/{id}`)

```json
{
  "id": 1437182,
  "userId": 940316,
  "status": "active",
  "runState": "running",
  "name": "fCTO - Executive Recruiters",
  "category": "linkedin",
  "campaignType": "sales navigator saved search",
  "salesNavigatorUrl": "https://www.linkedin.com/sales/search/people?savedSearchId=...",
  "searchParameters": { ... },
  "touchSequence": {
    "sequence": [
      { "type": "LI View", "delay_number": 1, "delay_time_unit": "day(s)", ... },
      { "type": "LI Connect", "message": "...", "followup_message": "...", "connect_followup": true, ... },
      { "type": "LI Message", "message": "...", ... }
    ]
  },
  "numOfTouches": 5,
  "numberOfPendingLeads": 0,
  "getNewLeads": true,
  "autoApproveLeads": true,
  "isSearchEnded": true,
  "excludeNoPhotos": false,
  "premiumOnly": false,
  "openLinkOnly": false,
  "excludeInvitedProfiles": true,
  "maxSearchAmount": 2500,
  "isLinkedinOnly": true,
  "includeMessageOnly": true,
  "teamId": 28612,
  "isRemoved": false
}
```

### Reply Object (from `GET /campaigns/replies`)

```json
{
  "total": 178,
  "replies": [
    {
      "personKey": "ACoAAAsmi-EB...",
      "person": {
        "key": "ACoAAAsmi-EB...",
        "firstName": "Shenikwa",
        "lastName": "Novachich",
        "name": "Shenikwa Novachich",
        "email": "shenikwa.novachich@e2optics.com",
        "currentEmployer": "E2 Optics",
        "currentTitle": "Recruiter",
        "location": "Buckeye, Arizona, United States",
        "linkedInHandle": "shenikwa-novachich-39579952",
        "linkedInData": { ... },
        "phone": "6022905678"
      },
      "message": "Thank you for the info Paul...",
      "conversationUrn": "2-NjA5OTI3ZDktZTI4NS00YjhiLWE3YWItMzhjMmYxMTFjOWI0XzEwMA==",
      "createdAt": "2026-03-02T16:14:49.089Z",
      "msgCreatedAt": "2026-03-02T15:28:48.000Z",
      "isExcluded": false,
      "isReturnToCampaign": false,
      "campaignId": 1437182,
      "campaignName": "fCTO - Executive Recruiters",
      "leadStatus": "approved",
      "description": "linkedin reply detected",
      "campaignStatus": "active",
      "isCampaignRemoved": false,
      "isLeadRemoved": false
    }
  ]
}
```

### Lead Object (from `GET /leads/campaign/{id}?type=approved`)

```json
{
  "total": 215,
  "leads": [
    {
      "entityUrn": "ACwAADt2g1oB...",
      "status": "approved",
      "conversationUrn": null,
      "isReturnToCampaign": null,
      "isExcluded": false,
      "nextTouchIndex": 2,
      "createdAt": "2026-02-22T20:06:24.029Z",
      "customData": null,
      "csvColumns": null,
      "person": {
        "key": "ACwAADt2g1oB...",
        "firstName": "Brandon",
        "lastName": "Newsome",
        "name": "Brandon Newsome",
        "email": "brandon@jorbly.com",
        "currentEmployer": "Jorbly",
        "currentTitle": "Lead Recruiter",
        "linkedInHandle": "brandon-newsome-aa212723a",
        "linkedInData": { ... }
      }
    }
  ]
}
```

### User Object (from `GET /users/me`)

```json
{
  "id": 940316,
  "name": "Paul Hoskins",
  "firstName": "Paul",
  "lastName": "Hoskins",
  "email": "paul@uniphibda.com",
  "timezone": { "name": "America/Chicago", ... },
  "linkedInEmail": "paul@hoskins.me",
  "isLinkedInLoginValid": true,
  "hasLinkedInPremium": true,
  "hasLinkedInSalesNavigator": true,
  "lastTeamId": 28612,
  "cloudBotStatus": {
    "loginStatus": "LOGGED_IN",
    "salesStatus": "SALES_NAVIGATOR_ACTIVE"
  },
  "companies": [
    { "name": "ProAction", "entityUrn": "urn:li:fsd_company:105932818" }
  ]
}
```

### Campaigns Grouped (from `GET /campaigns/grouped`)

```json
[
  {
    "category": "linkedin",
    "campaigns": [
      { "id": 1437182, "name": "fCTO - Executive Recruiters" },
      { "id": 1295862, "name": "SaaS TX v1 20250902" },
      { "id": 1238092, "name": "HIPAA 20250613 Eastern US" }
    ]
  }
]
```

### Lead Statuses (from `GET /leads/campaign/{id}/statuses`)

```json
{
  "leadsCount": 215,
  "repliesCount": 10,
  "viewedLeadsCount": 215,
  "requestedLeadsCount": 214,
  "connectedLeadsCount": 38,
  "followedUpLeadsCount": 33,
  "invitesPendingCount": 176,
  "messagedLeadsCount": 0,
  "inmailedLeadsCount": 0
}
```

---

## Reply-to-Lead Workflow

To reply to a campaign lead who has replied:

1. `GET /api/v1/campaigns/replies?page=1&perPage=25` -- find the reply, extract `conversationUrn`
2. `GET /api/v1/conversations/{conversationUrn}/messages` -- load conversation history
3. `POST /api/v1/conversations/messages` with body `{conversationId: conversationUrn, message: "..."}` -- send reply

For Sales Navigator conversations:
1. `GET /api/v1/conversations/sn-conversations`
2. `GET /api/v1/conversations/{conversationId}/sn-messages`
3. `POST /api/v1/conversations/{conversationId}/send-sn-message` with body `{message: "..."}`

## Return-to-Campaign Workflow

When a lead is excluded or stopped in a campaign and you want to re-enqueue them:

1. Find the lead's `entityUrn` from the replies or leads list
2. **Single lead:** `PATCH /api/v1/leads/campaign/{campaignId}/return` with body containing the entityUrn
3. **Batch:** `PATCH /api/v1/leads/return-to-campaign` with body `{entityUrns: ["ACoAAA...", ...]}`

## Campaign Creation Workflow

1. `POST /api/v1/campaigns/audience` -- create campaign with audience config, search params, and touch sequence
2. (Optional) Add more audience: `POST /api/v1/campaigns/{id}/audience/connections` or `/audience/sales-explorer-connections`
3. `POST /api/v1/campaigns/{id}/publish` -- publish the campaign (moves from draft to active)
4. `PATCH /api/v1/campaigns/{id}/running-state` with `{runState: "running"}` -- start execution

---

## Notes

- The `GET /campaigns` list endpoint consistently returns 500 on direct calls; use `GET /campaigns/dashboard` or `GET /campaigns/grouped` as alternatives for listing campaigns.
- The `GET /connections` endpoint requires an `entityUrn` parameter.
- Pagination on the internal API uses `page` (1-indexed) and `perPage`. The webhook API uses 0-indexed `page` and `per_page`.
- All timestamps in responses are ISO 8601 strings or Unix milliseconds.
- The JWT token has ~1 year expiration.
- The white-label API domain (`api.erubheorhgur.com`) and canonical domain (`api.meetalfred.com`) are interchangeable for API calls as long as the JWT matches.
