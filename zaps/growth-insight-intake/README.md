# Growth Insight Intake — Build Guide

Two-zap + Slack Workflow system that replaces the old two-zap + Zapier Storage setup.

## Architecture

```
📁 File uploaded to #growth-insight (or #debugging for testing)
         ↓
⚡ Zap 1 — triggers on new message with file
         ↓
🤖 Bot posts message + "Continue" button in channel
         ↓
👆 User clicks Continue → Slack Workflow form appears
         ↓
📝 User fills form:
   • Intel Type
   • Source & Interview Type
   • Account / Agency
   • Category
   • Product Area
   • Short Summary
         ↓
✅ Form submitted → Slack Workflow posts answers to channel
         ↓
⚡ Zap 2 — triggers on form response
         ↓
🔀 Route by Source Type × Media Type
         ↓
📁 Upload to correct Google Drive folder
         ↓
⚡ Existing zaps trigger (Audio Brain / Video Converter / Transcript → Notion)
         ↓
📊 Notion record created + Slack notification
```

## Current Status

| Component              | Status         | Notes                                      |
|------------------------|----------------|--------------------------------------------|
| Zap 1                  | ✅ Published    | Update channel to #growth-insight when live |
| Slack Workflow (form)  | ✅ Working      |                                            |
| Zap 2                  | 🔧 In progress | Blocked on file-fetching — see below       |
| 6 existing zaps        | ✅ Working      | Will add Urgency + Type fields later       |

## Channel IDs

- `#debugging` (test) → `C0AFEGUUZ99`
- `#growth-insight` (production) → get from Slack: right-click channel → Copy Link → last segment of URL
- Alert user: `<@U03LVEFBFHA>` (Marwin)

## Drive Folder IDs

| Source Type | Media Type   | Folder ID                           | Existing Zap |
|-------------|--------------|-------------------------------------|--------------|
| agency      | audio        | `1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz` | ✅ Working    |
| agency      | video        | `10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA` | ✅ Working    |
| agency      | transcript   | `1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1` | ✅ Working    |
| publisher   | audio        | `1dsJVpjwSPmlObgww_wKpG200kcooB_m2` | ✅ Working    |
| publisher   | video        | `1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c` | ✅ Working    |
| publisher   | transcript   | *no folder yet — TBC (Daniel)*      | ❌ TBC        |
| internal    | audio        | `1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm` | ✅ Working    |
| internal    | video        | *no folder yet — TBC (Daniel)*      | ❌ TBC        |
| internal    | transcript   | *no folder yet — TBC (Daniel)*      | ❌ TBC        |
| unknown     | any          | *Slack alert only*                  | —            |

---

## The File-Fetching Blocker (Zap 2)

**The problem:** Zap 1 has the file (from the Slack trigger). Zap 2 is triggered by the *form response* message, which is a separate Slack message with no file attached. Zap 2 needs a way to get the original file.

### Option A — Slack Workflow passes the file URL through (preferred if it works)

1. Zap 1's bot message text includes the file's private download URL as a plain-text field, e.g.:
   ```
   New file ready for intake.
   file_url: https://files.slack.com/files-pri/...
   file_type: mp3
   ```
2. In Slack Workflow Builder, add a variable that captures the `file_url` from the trigger message text.
3. The form completion post includes this variable.
4. Zap 2 reads `file_url` directly from the form response message.

**Test first:** Check if Slack Workflow Builder lets you extract a variable from the triggering message body. If yes, this is the cleanest path.

### Option B — Stage to Google Drive, then move (reliable fallback)

1. **Zap 1** uploads the file immediately to a `_Staging` folder in Google Drive.
2. **Zap 1's bot message** includes the staging Drive file ID in its text:
   ```
   staging_file_id: 1aBcDeFgH...
   ```
3. **Slack Workflow** captures `staging_file_id` from the trigger message and includes it in the form response.
4. **Zap 2** reads `staging_file_id` from form response, then uses Google Drive → **Move File** to the correct destination folder.

**Staging folder ID:** Create one named `_Staging - Intake` in the shared Drive and paste the ID here: `STAGING_FOLDER_ID_TBD`

### Option C — Zapier Storage (if Slack Workflow can't pass variables)

1. **Zap 1** stores file metadata in Zapier Storage with key = `intake_{slack_user_id}`.
   - Value: `{"file_url": "...", "file_type": "mp3"}`
2. **Zap 1's bot message** mentions the user by ID (e.g. `<@U03LVEFBFHA>` filled dynamically).
3. **Slack Workflow** captures the Slack user ID from the triggering message.
4. **Zap 2** uses Zapier Storage → **Get Value** with key `intake_{user_id}` to retrieve the file URL.

---

## Zap 1 — Build Steps

### Step 1: Trigger — Slack: New Message Posted to Channel

- App: Slack
- Event: **New Message Posted to Channel**
- Channel: `#debugging` (swap to `#growth-insight` when live)
- Trigger for Bot Messages: **No**

*Post a test message with a file attached to get sample data.*

### Step 2: Filter — Only Continue If…

Continue only if ALL:
- `All Files Count` **greater than** `0`

*(Optional: also filter out image-only files: `All Files Filetype` does not contain `png,jpg,jpeg,gif,webp,bmp`)*

### Step 3: Action — Slack: Send Channel Message (bot with Continue button)

- App: Slack
- Event: **Send Channel Message**
- Channel: same as trigger
- Message: include the file URL so Slack Workflow can capture it (see Option A above):
  ```
  📎 New file ready for intake.
  Uploaded by: {{step1.user_name}}
  File: {{step1.all_files_title}}
  file_url: {{step1.all_files_url_private_download}}
  file_type: {{step1.all_files_filetype}}

  Click *Continue* to fill in the intake form.
  ```
- Add a workflow button: label **Continue**, link to your Slack Workflow URL

---

## Zap 2 — Build Steps

### Step 1: Trigger — Slack: New Message Posted to Channel

- App: Slack
- Event: **New Message Posted to Channel**
- Channel: `#debugging`
- Trigger for Bot Messages: **Yes** (the form response is posted by the Slack Workflow bot)

*Post a test form response to get sample data.*

### Step 2: Filter — Only Continue If…

Continue only if ALL:
- Message text **contains** some unique string from your Slack Workflow form response (e.g. `Intel Type:` or whatever header the form response uses)

*(This prevents Zap 2 from triggering on every message in the channel.)*

### Step 3: Code by Zapier (Python) — Route

- Action: **Run Python**
- Input Data — map these from Step 1 (the form response message text) + file info (from Option A/B/C above):
  - `message_text` → step 1 → `Text`
  - `file_url` → step 1 → extracted variable (Option A/B/C)
  - `file_type` → step 1 → extracted variable
- Code: paste `zap2-route.py`

### Step 4: Paths — Route by source_type × media_type

Create a **Paths** action with paths for each folder + alert paths:

| Path | Filter                                                    | Action                                   |
|------|-----------------------------------------------------------|------------------------------------------|
| A    | `source_type` = agency AND `media_type` = audio           | Google Drive → Upload File               |
| B    | `source_type` = agency AND `media_type` = video           | Google Drive → Upload File               |
| C    | `source_type` = agency AND `media_type` = transcript      | Google Drive → Upload File               |
| D    | `source_type` = publisher AND `media_type` = audio        | Google Drive → Upload File               |
| E    | `source_type` = publisher AND `media_type` = video        | Google Drive → Upload File               |
| F    | `source_type` = publisher AND `media_type` = transcript   | Slack alert (no folder yet)              |
| G    | `source_type` = internal AND `media_type` = audio         | Google Drive → Upload File               |
| H    | `source_type` = internal AND `media_type` = video         | Slack alert (no folder yet)              |
| I    | `source_type` = internal AND `media_type` = transcript    | Slack alert (no folder yet)              |
| Z    | *(default / no match)*                                    | Slack alert — tag Marwin to investigate  |

### Google Drive Upload action config (Paths A–E, G)

- App: Google Drive
- Event: **Upload File**
- Folder: step 3 → `folder_id`
- File: `file_url` (from step 1 / Option A/B/C)
- File Name: step 3 → `file_name_base`
- File Extension: `file_type`
- Convert to Document: **No**

### Slack Alert action config (Paths F, H, I, Z)

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

## Zap 2 Route Code (zap2-route.py)

See `zap2-route.py` — paste its contents into the Code by Zapier step.

---

## Remaining Work

- [ ] **Resolve file-fetching** — test Option A first; fall back to B or C
- [ ] **Create 3 missing Drive folders** (Daniel to confirm):
  - Publisher → Transcript/Doc
  - Internal IP → Video
  - Internal IP → Transcript/Doc
- [ ] **Add folder IDs to route table above** once created
- [ ] **Update existing zaps** to pass new form fields: `Urgency` and `Type`
- [ ] **Daniel to verify** the form questionnaire is complete/correct
- [ ] **Swap channels** from `#debugging` → `#growth-insight` once Zap 2 is tested end-to-end

## Accounts

- Slack: `58107765`
- Google Drive: `59727506`
- Anthropic: same connection as existing Drive→Notion zaps
