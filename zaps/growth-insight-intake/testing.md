# Growth Insight Intake — Test Matrix

Run through all 11 rows before switching from `#debugging` to `#growth-insight`. Check each expected result before moving on.

## Setup

1. Apps Script deployed, `SLACK_BOT_TOKEN` set in Script Properties
2. Zap 1 active, watching `#debugging`, posting three Continue buttons
3. Zap 2 active, watching `#debugging` for Workflow form responses
4. Your Slack user has access to `#debugging`

---

## Test Matrix

| # | Source button clicked | File type | Extension | Expected Drive folder | Expected Notion? | Expected signal |
|---|----------------------|-----------|-----------|----------------------|------------------|-----------------|
| 1 | Continue (Agency) | Audio | `.mp3` | Agency/Audio `1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz` | ✅ Yes | ✅ reaction on upload |
| 2 | Continue (Agency) | Video | `.mp4` | Agency/Video `10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA` | ✅ Yes | ✅ reaction on upload |
| 3 | Continue (Agency) | Transcript | `.pdf` | Agency/Transcript `1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1` | ✅ Yes | ✅ reaction on upload |
| 4 | Continue (Publisher) | Audio | `.mp3` | Publisher/Audio `1dsJVpjwSPmlObgww_wKpE200kcooB_m2` | ✅ Yes | ✅ reaction on upload |
| 5 | Continue (Publisher) | Video | `.mp4` | Publisher/Video `1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c` | ✅ Yes | ✅ reaction on upload |
| 6 | Continue (Publisher) | Transcript | `.pdf` | Publisher/Transcript `1C6QC9gZ3dHx1FZfTNF6L6cw298KudCOD` | ✅ Yes | ✅ reaction on upload |
| 7 | Continue (Internal) | Audio | `.mp3` | Internal/Audio `1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm` | ❌ No (Drive only) | ✅ reaction on upload |
| 8 | Continue (Internal) | Video | `.mp4` | Internal/Video `1sSh0Ubg3X-qvcydXmPRZcIwhgLiPGgph` | ❌ No (Drive only) | ✅ reaction on upload |
| 9 | Continue (Internal) | Transcript | `.pdf` | Internal/Transcript `1rbPJNA_1YQRwHJoLBIzdZMVcoc1hqqa4` | ❌ No (Drive only) | ✅ reaction on upload |
| 10 | *(none — Zap triggers on raw upload, no button click)* | Audio | `.mp3` | N/A — no folder | — | ⚠️ Slack alert to Marwin |
| 11 | Continue (Agency) | Unknown | `.xyz` | N/A — unrecognised extension | — | ⚠️ Slack alert to Marwin |

---

## Common Failure Modes

### 1. Apps Script returns 401 / "SLACK_BOT_TOKEN not set"

**Cause:** Script Properties not configured.
**Fix:** In Apps Script editor → Project Settings → Script Properties → add key `SLACK_BOT_TOKEN` with the Slack bot token value. Redeploy is not required after changing properties.

---

### 2. Drive file shows up in wrong folder (or 404 on folder)

**Cause:** Folder ID typo. The most likely culprit is Publisher/Audio — old ID had `wKpG`, correct is `wKpE`.
**Fix:** Confirm IDs in `zap2-route.py` FOLDER_IDS dict against the Drive folder URLs. Open each folder in Drive and verify the last segment of the URL matches.

---

### 3. Apps Script times out on large video files

**Cause:** Google Apps Script has a 6-minute execution limit. Files above ~2–3 GB may exceed this on slow connections.
**Fix:** For very large files, Marwin should download from Slack manually and upload to Drive directly. The alert path (row 10/11) can be used as the manual fallback. Consider chunked upload via Drive API if this becomes frequent.

---

### 4. Zap 2 doesn't trigger on form response

**Cause:** Zap 2's filter (Step 2) looks for `Intel Type:` in the message text, but the Workflow posts a different label.
**Fix:** Open the Workflow in Slack → check the exact text of the label in the form response message → update Zap 2's filter string to match.

---

### 5. Wrong workflow form opens (e.g., Agency form when user clicks Publisher)

**Cause:** Button URLs are mapped incorrectly in Zap 1's bot message.
**Fix:** In Zap 1 → Step 3 → check each button's Workflow URL against the correct workflow in Slack's Workflow Builder. Republish Zap 1 after fixing.

---

### 6. ✅ reaction appears on the wrong message

**Cause:** `original_ts` is capturing the Zap 1 bot message timestamp instead of the user's original upload.
**Fix:** Confirm that Zap 1 embeds `original_ts: {{step1.ts}}` (the trigger message timestamp, not the bot's own message). The routing code extracts this from the message body.

---

### 7. Internal file triggers a Notion record

**Cause:** Existing Drive→Notion zaps don't filter on `notion_record = "no"`.
**Fix:** Add a Filter step at the start of each existing Drive→Notion zap: only continue if the `notion_record` field ≠ `"no"`. (These zaps trigger from Drive folder additions, not from Zap 2 directly — so the filter needs to read the filename or a Drive file property.)

> **Alternative:** tag internal Drive folders differently so the existing zaps' folder-watch triggers don't fire for them.
