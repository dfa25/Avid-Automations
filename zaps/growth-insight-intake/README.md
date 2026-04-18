# Growth Insight Intake — Build Guide

Two-zap + three Slack Workflows system that routes Slack file uploads into the correct Google Drive folder via a Google Apps Script webhook.

## Architecture

```
📁 File uploaded to #growth-insight (or #debugging for testing)
         ↓
⚡ Zap 1 — triggers on new message with file
         ↓
🤖 Bot posts message + THREE "Continue" buttons in channel
   [Continue (Agency)]  [Continue (Publisher)]  [Continue (Internal)]
         ↓
👆 User clicks the button matching their source type
   → Correct Slack Workflow form appears (Agency / Publisher / Internal)
         ↓
📝 User fills form:
   • Intel Type
   • Account / Agency
   • Category
   • Product Area
   • Short Summary
         ↓
✅ Form submitted → Slack Workflow posts answers to channel
         ↓
⚡ Zap 2 — triggers on form response message
         ↓
🔀 Route by Source Type × Media Type → Drive folder ID
         ↓
📡 Call Google Apps Script webhook with file URL + folder ID
   (bypasses Zapier's 250 MB cap — Apps Script streams directly from Slack to Drive)
         ↓
   ┌─────────────────────────────────┐
   │ Success                         │ Failure
   │ ✅ React to user's original     │ ⚠️ Slack alert to Marwin
   │    upload message               │
   └─────────────────────────────────┘
         ↓ (Agency / Publisher only)
⚡ Existing zaps trigger (Audio Brain / Video Converter / Transcript → Notion)
         ↓
📊 Notion record created + Slack notification
   ⚠️ Internal files: Drive only — no Notion record
```

## Why Apps Script, Not Zapier Drive Upload?

Avid is on **Zapier Starter ($29/mo)**, which caps file transfers at **250 MB**. Market insights regularly include **1–4 GB video files**. The Google Apps Script webhook receives the Slack private download URL and copies the file directly to Google Drive — no size cap.

---

## Current Status

| Component                   | Status          | Notes                                                  |
|-----------------------------|-----------------|--------------------------------------------------------|
| Zap 1                       | ✅ Published     | Update channel to #growth-insight when live            |
| Slack Workflow — Agency      | ✅ Working       |                                                        |
| Slack Workflow — Publisher   | ✅ Working       |                                                        |
| Slack Workflow — Internal    | ✅ Working       |                                                        |
| Zap 2                       | 🔧 In progress  | Needs webhook step added                               |
| Apps Script webhook          | 🔧 In progress  | See `file-router.gs` — deploy at script.google.com    |
| 6 existing Drive→Notion zaps | ✅ Working       |                                                        |

---

## Channel IDs

- `#debugging` (test) → `C0AFEGUUZ99`
- `#growth-insight` (production) → get from Slack: right-click channel → Copy Link → last segment
- Alert user: `<@U03LVEFBFHA>` (Marwin)

---

## Drive Folder IDs

All 9 source × media combinations have folders. Internal files go to Drive only — existing zaps should skip Notion record creation for `source_type = internal`.

| Source Type | Media Type   | Folder ID                             | Notion record? |
|-------------|--------------|---------------------------------------|----------------|
| agency      | audio        | `1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz`   | ✅ Yes          |
| agency      | video        | `10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA`   | ✅ Yes          |
| agency      | transcript   | `1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1`   | ✅ Yes          |
| publisher   | audio        | `1dsJVpjwSPmlObgww_wKpE200kcooB_m2`   | ✅ Yes          |
| publisher   | video        | `1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c`   | ✅ Yes          |
| publisher   | transcript   | `1C6QC9gZ3dHx1FZfTNF6L6cw298KudCOD`   | ✅ Yes          |
| internal    | audio        | `1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm`   | ❌ Drive only   |
| internal    | video        | `1sSh0Ubg3X-qvcydXmPRZcIwhgLiPGgph`   | ❌ Drive only   |
| internal    | transcript   | `1rbPJNA_1YQRwHJoLBIzdZMVcoc1hqqa4`   | ❌ Drive only   |

> ⚠️ **Publisher/Audio folder ID fix**: An earlier version had a typo — `wKpG` — which 404s. Correct ID has `wKpE`: `1dsJVpjwSPmlObgww_wKpE200kcooB_m2`.

---

## Three Slack Workflows (Option B)

There are **three** Slack Workflows — one per source type. Zap 1's bot message includes three buttons:

| Button label           | Workflow            | Encodes source_type |
|------------------------|---------------------|---------------------|
| Continue (Agency)      | Agency Intake Form  | `agency`            |
| Continue (Publisher)   | Publisher Intake Form | `publisher`       |
| Continue (Internal)    | Internal Intake Form | `internal`         |

Each workflow posts a structured response that Zap 2 parses. The `source_type` is encoded by which workflow was triggered, not parsed from freetext.

---

## Zap 1 — Build Steps

### Step 1: Trigger — Slack: New Message Posted to Channel

- App: Slack
- Event: **New Message Posted to Channel**
- Channel: `#debugging` (swap to `#growth-insight` when live)
- Trigger for Bot Messages: **No**

### Step 2: Filter — Only Continue If…

- `All Files Count` **greater than** `0`

### Step 3: Action — Slack: Send Channel Message

- App: Slack
- Event: **Send Channel Message**
- Channel: same as trigger
- Message text (embed the file URL so Zap 2 can parse it):
  ```
  📎 New file ready for intake.
  Uploaded by: {{step1.user_name}}
  File: {{step1.all_files_title}}
  file_url: {{step1.all_files_url_private_download}}
  file_type: {{step1.all_files_filetype}}
  original_ts: {{step1.ts}}

  Click the button matching your source:
  ```
- Add **three** workflow buttons:
  - Label `Continue (Agency)` → Agency Workflow URL
  - Label `Continue (Publisher)` → Publisher Workflow URL
  - Label `Continue (Internal)` → Internal Workflow URL

---

## Zap 2 — Build Steps

### Step 1: Trigger — Slack: New Message Posted to Channel

- App: Slack
- Event: **New Message Posted to Channel**
- Channel: `#debugging`
- Trigger for Bot Messages: **Yes** (the form response is posted by the Workflow bot)

### Step 2: Filter — Only Continue If…

- Message text **contains** `Intel Type:` (unique header from Workflow form responses)

### Step 3: Code by Zapier (Python) — Route

- Action: **Run Python**
- Input Data — map from Step 1:
  - `message_text` → step 1 → `Text`
  - `file_url` → *(leave blank — script extracts from the Zap 1 bot message embedded in the response)*
  - `file_type` → *(leave blank — script extracts from message)*
- Code: paste `zap2-route.py`

### Step 4: Paths — Route by source_type × media_type

All 9 source/media combinations now have Drive folders. Unrecognised source or file type triggers the alert path.

| Path | Filter                                                    | Action                                        |
|------|-----------------------------------------------------------|-----------------------------------------------|
| A    | `source_type` = agency, `media_type` = audio              | Webhooks → POST to Apps Script webhook        |
| B    | `source_type` = agency, `media_type` = video              | Webhooks → POST to Apps Script webhook        |
| C    | `source_type` = agency, `media_type` = transcript         | Webhooks → POST to Apps Script webhook        |
| D    | `source_type` = publisher, `media_type` = audio           | Webhooks → POST to Apps Script webhook        |
| E    | `source_type` = publisher, `media_type` = video           | Webhooks → POST to Apps Script webhook        |
| F    | `source_type` = publisher, `media_type` = transcript      | Webhooks → POST to Apps Script webhook        |
| G    | `source_type` = internal, `media_type` = audio            | Webhooks → POST to Apps Script webhook        |
| H    | `source_type` = internal, `media_type` = video            | Webhooks → POST to Apps Script webhook        |
| I    | `source_type` = internal, `media_type` = transcript       | Webhooks → POST to Apps Script webhook        |
| Z    | *(default / no match)*                                    | Slack alert — tag Marwin to investigate       |

### Apps Script webhook action config (Paths A–I)

- App: **Webhooks by Zapier**
- Event: **POST**
- URL: your deployed Apps Script web app URL (from script.google.com)
- Payload Type: **JSON**
- Data:
  ```json
  {
    "fileUrl":    "{{file_url}}",
    "folderId":   "{{folder_id}}",
    "fileName":   "{{file_name_base}}",
    "fileType":   "{{file_type}}",
    "originalTs": "{{original_ts}}",
    "channelId":  "C0AFEGUUZ99"
  }
  ```

### On success: react ✅ to original upload message

After a successful webhook call, add a step in each Path A–I:

- App: Slack
- Event: **Add Reaction**
- Channel: same channel as Zap 1 trigger
- Message timestamp: `original_ts` (from the routing code output)
- Emoji: `white_check_mark`

### Slack alert config (Path Z and on Apps Script failure)

- App: Slack
- Event: **Send Channel Message**
- Channel: `#debugging` (swap to `#growth-insight` in production)
- Message:
  ```
  ⚠️ <@U03LVEFBFHA> — intake needs manual routing
  Source: {{source_type}}
  Media: {{media_type}}
  Account: {{account}}
  Intel Type: {{intel_type}}
  Summary: {{summary}}
  File URL: {{file_url}}
  Reason: {{alert_reason}}
  ```

---

## Apps Script Webhook (file-router.gs)

See `file-router.gs`. Deploy as a Web App at **script.google.com** (not run in CI).

The script:
1. Receives POST with `fileUrl`, `folderId`, `fileName`, `fileType`, `originalTs`, `channelId`
2. Authenticates with Slack using the bot token stored in Script Properties
3. Fetches the file from Slack (streams around Zapier's 250 MB limit)
4. Creates the file in the specified Drive folder
5. Returns `{"status": "ok", "fileId": "..."}` on success, or `{"status": "error", "message": "..."}` on failure

**Deploy settings:**
- Execute as: **Me**
- Who has access: **Anyone** (Zapier needs unauthenticated access)
- Store `SLACK_BOT_TOKEN` in Project → Settings → Script Properties

---

## Zap 2 Route Code (zap2-route.py)

See `zap2-route.py`. Key changes from earlier version:

- All 9 Drive folders are now populated — no more empty strings
- Publisher/Audio folder ID corrected: `wKpE` not `wKpG`
- `original_ts` added to output (used for ✅ reaction)
- `notion_record` added to output (`"yes"` for agency/publisher, `"no"` for internal)

---

## Remaining Work

- [ ] **Deploy Apps Script** — upload `file-router.gs` to script.google.com, deploy as Web App, copy URL into Zapier webhook steps (Paths A–I)
- [ ] **Set SLACK_BOT_TOKEN** in Apps Script Project → Settings → Script Properties
- [ ] **Confirm three Slack Workflow URLs** — paste into Zap 1's three Continue buttons
- [ ] **Filter internal in existing Notion zaps** — add a filter step: skip if `source_type = internal`
- [ ] **Swap channels** — `#debugging` → `#growth-insight` once tested end-to-end

---

## Accounts

- Slack: `58107765`
- Google Drive: `59727506`
- Anthropic: same connection as existing Drive→Notion zaps
