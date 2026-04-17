# Shazam Intake Zap — Build Guide

Single Zapier zap that replaces the old two-zap + Storage setup.

## What it does

```
User posts in #growth-capture:
  #shazam
  Source: Agency — Design Partner
  Account: WPP
  Summary: Pricing model unclear
  [attaches file]
           ↓
Trigger: new message with #shazam
           ↓
Parse fields from message (parse.py)
           ↓
If any field missing → Anthropic infers it
           ↓
Merge parsed + AI results (merge.py)
           ↓
Route to Drive folder based on source_type × media_type
           ↓
Rename: [Intel Type] — [Account] — [Summary]
           ↓
Existing Drive → Notion zap takes over
```

## Prerequisites

- Slack connected in Zapier (already done — account 58107765)
- Google Drive connected in Zapier (already done — account 59727506)
- Anthropic connected in Zapier (already done, used in Drive→Notion zaps)
- Channel ID for `#growth-capture` — **fill in below before build**

## Channel ID

- `#debugging` (test channel) → `C0AFEGUUZ99`
- `#growth-capture` (production channel) → `CHANNEL_ID_TBD` ← get from Slack: right-click channel → Copy Link → last segment of URL
- Alert channel: `#debugging` during testing, swap to `#growth-capture` in production
- Alert user mention: `<@U03LVEFBFHA>` (Marwin)

## Drive folder IDs

| source_type | media_type | Folder ID                               |
|-------------|------------|-----------------------------------------|
| agency      | audio      | `1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz`     |
| agency      | video      | `10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA`     |
| agency      | transcript | `1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1`     |
| publisher   | audio      | `1dsJVpjwSPmlObgww_wKpG200kcooB_m2`     |
| publisher   | video      | `1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c`     |
| publisher   | transcript | *no folder — Slack alert*               |
| internal    | audio      | `1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm`     |
| internal    | video      | `1sSh0Ubg3X-qvcydXmPRZcIwhgLiPGgph`     |
| internal    | transcript | *no folder — Slack alert*               |
| unknown     | any        | *Slack alert*                           |

## Build steps in Zapier UI

### 1. Trigger — Slack: New Message Posted to Channel

- App: Slack
- Event: **New Message Posted to Channel**
- Channel: `#growth-capture` (use channel ID from above)
- Trigger for Bots?: **No**

*Why not "New File in Channel"?* That trigger fires per file upload but doesn't carry the message text the user types alongside. The "New Message" trigger fires on the message that contains both the file(s) and the metadata text — single event, everything attached.

### 2. Filter — Only Continue If…

Continue only if ALL of:
- `Text` **contains (case insensitive)** → `#shazam`
- `All Files Count` **(exists)** → has file(s)
- `All Files Filetype` **not in** → `png,jpg,jpeg,gif,webp,bmp,svg,heic`

### 3. Code by Zapier (Python) — Parse

- Action: **Run Python**
- Input Data:
  - `message_text` → Step 1 → `Text`
  - `file_name` → Step 1 → `All Files Title` (or `Name`)
  - `file_type` → Step 1 → `All Files Filetype`
- Code: paste `parse.py` verbatim

### 4. Paths by Zapier (optional optimisation)

If you want to skip the Anthropic call when everything is already provided:
- Path A — Needs AI: `needs_ai` (from step 3) **= true** → run step 5
- Path B — Skip AI: `needs_ai` **= false** → go straight to step 6 with empty `ai_response`

If this adds too much complexity, skip Paths and always call Anthropic — the cost is trivial.

### 5. Anthropic — Inference

- App: Anthropic (same connection as your Drive→Notion zaps)
- Action: whichever "Send Prompt" / "Messages" action you already use
- System prompt: see `ai-prompt.md`
- User prompt: see `ai-prompt.md` (with Zapier field mappings)
- Model: match your existing zaps
- Max tokens: 200
- Temperature: 0

### 6. Code by Zapier (Python) — Merge

- Action: **Run Python**
- Input Data:
  - `parsed_intel_type` → step 3 → `intel_type`
  - `parsed_source_type` → step 3 → `source_type`
  - `parsed_source_raw` → step 3 → `source_raw`
  - `parsed_account` → step 3 → `account`
  - `parsed_summary` → step 3 → `summary`
  - `parsed_context` → step 3 → `context`
  - `parsed_media_type` → step 3 → `media_type`
  - `ai_response` → step 5 → raw text output (or empty if skipped)
- Code: paste `merge.py` verbatim

### 7. Paths — Route by source_type × media_type

Create a **Paths** action with 9 paths. Each path has:
- A filter (`source_type` + `media_type` match)
- An action (Drive upload OR Slack alert)

| Path | Filter                                             | Action                                                                    |
|------|----------------------------------------------------|---------------------------------------------------------------------------|
| A    | source_type = agency AND media_type = audio        | Drive upload → folder `1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz`                 |
| B    | source_type = agency AND media_type = video        | Drive upload → folder `10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA`                 |
| C    | source_type = agency AND media_type = transcript   | Drive upload → folder `1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1`                 |
| D    | source_type = publisher AND media_type = audio     | Drive upload → folder `1dsJVpjwSPmlObgww_wKpG200kcooB_m2`                 |
| E    | source_type = publisher AND media_type = video     | Drive upload → folder `1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c`                 |
| F    | source_type = publisher AND media_type = transcript| Slack alert: "Publisher transcript — no Drive folder configured"          |
| G    | source_type = internal AND media_type = audio      | Drive upload → folder `1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm`                 |
| H    | source_type = internal AND media_type = video      | Drive upload → folder `1sSh0Ubg3X-qvcydXmPRZcIwhgLiPGgph`                 |
| I    | source_type = internal AND media_type = transcript | Slack alert: "Internal transcript — no Drive folder configured"           |
| J    | source_type = unknown OR media_type = unknown      | Slack alert: "Could not classify — manual review needed"                  |

### Drive Upload action config (used in A, B, C, D, E, G, H)

- App: Google Drive
- Event: **Upload File**
- Drive: *(default / My Drive)*
- Folder: *(use the folder ID from table above)*
- File: Step 1 → `All Files URL Private Download` (first file)
- File Name: Step 6 → `file_name_base`
- File Extension: Step 1 → `All Files Filetype`
- Convert to Document?: **No**

### Slack Alert action config (used in F, I, J)

- App: Slack
- Event: **Send Channel Message**
- Channel: `#growth-capture` (or dedicated alerts channel)
- Message text:
  ```
  ⚠️ <@U03LVEFBFHA> — intake routing needs attention
  Intel Type: {{intel_type}}
  Source: {{source_type}} ({{source_raw}})
  Account: {{account}}
  Media Type: {{media_type}}
  Summary: {{summary}}
  File: {{file_name_base}}.{{file_type}}
  ```
- Send as Bot: **Yes**
- Include link to original Slack message: **Yes**

## Migration

Once this zap is tested and live in `#growth-capture`:

1. **Turn OFF** Zap `357417048` ("Slack Message Router - Multi-Path Webhook Dispatcher")
2. **Turn OFF** Zap `358676494` ("Slack | File Upload")
3. Optionally clean up Zapier Storage keys prefixed `upload_*` (no longer used)

Keep them OFF for a week before deleting, in case rollback is needed.

## Test plan

1. Post in `#growth-capture` with a test audio file:
   ```
   #shazam
   Source: Agency — Design Partner
   Account: WPP
   Summary: Test of new intake
   ```
2. Verify it lands in Agency–Audio folder (`1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz`) with filename `Uncategorised — WPP — Test of new intake.mp3`
3. Post a second test with only `#shazam` + attached video → verify AI fallback fires and routes correctly (check Zap run history)
4. Post a third test with unreadable content → verify Slack alert path J fires

## Open questions

- [ ] Confirm channel ID for `#growth-capture`
- [ ] Confirm alert channel (same as intake, or separate)
- [ ] Confirm Publisher-Transcript and Internal-Transcript should stay alert-only or get new folders created
