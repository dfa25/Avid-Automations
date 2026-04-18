"""
Zap 2 — Route step (Code by Zapier: Run Python)

Input Data keys (map in Zapier UI):
  message_text  — full text of the Slack Workflow form response message
  file_url      — Slack private download URL (optional — script extracts from message if blank)
  file_type     — file extension, e.g. "mp3", "mp4", "pdf" (optional — extracted from message)

Output keys used downstream:
  source_type    — agency | publisher | internal | unknown
  media_type     — audio | video | transcript | unknown
  intel_type     — from form
  account        — from form
  category       — from form
  product_area   — from form
  summary        — from form
  folder_id      — Drive folder ID (empty string = no folder → alert path)
  file_name_base — constructed filename without extension
  alert_reason   — human-readable reason when folder_id is empty
  original_ts    — Slack message timestamp of user's original upload (for ✅ reaction)
  notion_record  — "yes" for agency/publisher files; "no" for internal (Drive only)
"""

import re

# ---------------------------------------------------------------------------
# 1. Parse structured form response from Slack Workflow message
#    Slack Workflow posts fields line-by-line: "Label: value"
# ---------------------------------------------------------------------------

def extract_field(text, label):
    pattern = rf"(?i){re.escape(label)}[:\s]+(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

msg = input_data.get("message_text", "")

raw_source       = extract_field(msg, "source")
raw_intel_type   = extract_field(msg, "Intel Type")
raw_account      = extract_field(msg, "Account")
raw_category     = extract_field(msg, "Category")
raw_product_area = extract_field(msg, "Product Area")
raw_summary      = extract_field(msg, "Summary")
raw_original_ts  = extract_field(msg, "original_ts")

# file_url / file_type are embedded in Zap 1's bot message, which the Workflow
# captures and re-posts as part of its form response.
file_url  = input_data.get("file_url", "") or extract_field(msg, "file_url")
file_type = (input_data.get("file_type", "") or extract_field(msg, "file_type")).lower().strip(".")

# ---------------------------------------------------------------------------
# 2. Normalise source_type
#    Three Slack Workflows embed "source: agency / publisher / internal" directly.
#    Fuzzy matching is retained as a fallback for edge cases.
# ---------------------------------------------------------------------------

src = raw_source.lower()
if any(k in src for k in ["agency", "design partner", "partner"]):
    source_type = "agency"
elif "publisher" in src:
    source_type = "publisher"
elif any(k in src for k in ["internal", "ip ", "internal ip"]):
    source_type = "internal"
else:
    source_type = "unknown"

# ---------------------------------------------------------------------------
# 3. Normalise media_type from file extension
# ---------------------------------------------------------------------------

AUDIO_EXTS      = {"mp3", "wav", "m4a", "aac", "ogg", "flac", "aiff"}
VIDEO_EXTS      = {"mp4", "mov", "avi", "mkv", "webm", "m4v"}
TRANSCRIPT_EXTS = {"pdf", "doc", "docx", "txt", "vtt", "srt"}

if file_type in AUDIO_EXTS:
    media_type = "audio"
elif file_type in VIDEO_EXTS:
    media_type = "video"
elif file_type in TRANSCRIPT_EXTS:
    media_type = "transcript"
else:
    media_type = "unknown"

# ---------------------------------------------------------------------------
# 4. Routing table: source_type × media_type → Drive folder ID
#    All 9 combinations are now populated.
#    Note: publisher/audio was previously "wKpG" — correct ID has "wKpE".
# ---------------------------------------------------------------------------

FOLDER_IDS = {
    ("agency",    "audio"):      "1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz",
    ("agency",    "video"):      "10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA",
    ("agency",    "transcript"): "1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1",
    ("publisher", "audio"):      "1dsJVpjwSPmlObgww_wKpE200kcooB_m2",
    ("publisher", "video"):      "1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c",
    ("publisher", "transcript"): "1C6QC9gZ3dHx1FZfTNF6L6cw298KudCOD",
    ("internal",  "audio"):      "1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm",
    ("internal",  "video"):      "1sSh0Ubg3X-qvcydXmPRZcIwhgLiPGgph",
    ("internal",  "transcript"): "1rbPJNA_1YQRwHJoLBIzdZMVcoc1hqqa4",
}

folder_id = FOLDER_IDS.get((source_type, media_type), "")

# ---------------------------------------------------------------------------
# 5. Alert reason — shown in Slack alert message when routing fails
# ---------------------------------------------------------------------------

if source_type == "unknown":
    alert_reason = f"Could not classify source from: '{raw_source}'"
elif media_type == "unknown":
    alert_reason = f"Unrecognised file type: .{file_type}"
else:
    alert_reason = ""

# Internal files go to Drive only — existing Notion zaps should be filtered
# to skip record creation when notion_record = "no".
notion_record = "no" if source_type == "internal" else "yes"

# ---------------------------------------------------------------------------
# 6. Build filename
#    Format: [Intel Type] — [Account] — [Summary]
#    Zapier appends the file extension separately.
# ---------------------------------------------------------------------------

def slugify_part(s):
    s = s.strip()
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s[:60].strip()

intel_part   = slugify_part(raw_intel_type) or "Uncategorised"
account_part = slugify_part(raw_account)    or "Unknown Account"
summary_part = slugify_part(raw_summary)    or "No Summary"

file_name_base = f"{intel_part} — {account_part} — {summary_part}"

# ---------------------------------------------------------------------------
# 7. Output
# ---------------------------------------------------------------------------

output = {
    "source_type":    source_type,
    "media_type":     media_type,
    "intel_type":     raw_intel_type,
    "account":        raw_account,
    "category":       raw_category,
    "product_area":   raw_product_area,
    "summary":        raw_summary,
    "folder_id":      folder_id,
    "file_name_base": file_name_base,
    "alert_reason":   alert_reason,
    "original_ts":    raw_original_ts,
    "notion_record":  notion_record,
}
