"""
Zap 2 — Route step (Code by Zapier: Run Python)

Input Data keys (map in Zapier UI):
  message_text  — full text of the Slack Workflow form response message
  file_url      — Slack private download URL (passed via Option A/B/C)
  file_type     — file extension, e.g. "mp3", "mp4", "pdf"

Output keys used downstream:
  source_type   — agency | publisher | internal | unknown
  media_type    — audio | video | transcript | unknown
  intel_type    — from form
  account       — from form
  category      — from form
  product_area  — from form
  summary       — from form
  folder_id     — Drive folder ID (empty string = no folder, use alert path)
  file_name_base — constructed filename without extension
  alert_reason  — human-readable reason when folder_id is empty
"""

import re

# ---------------------------------------------------------------------------
# 1. Parse structured form response from Slack Workflow message
#    Slack Workflow posts fields line-by-line: "Label: value"
#    Adjust the field names below to match exactly what your Workflow posts.
# ---------------------------------------------------------------------------

def extract_field(text, label):
    pattern = rf"(?i){re.escape(label)}[:\s]+(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

msg = input_data.get("message_text", "")

raw_intel_type   = extract_field(msg, "Intel Type")
raw_source       = extract_field(msg, "Source")       # may be "Agency - Design Partner" etc.
raw_account      = extract_field(msg, "Account")
raw_category     = extract_field(msg, "Category")
raw_product_area = extract_field(msg, "Product Area")
raw_summary      = extract_field(msg, "Summary")
file_url         = input_data.get("file_url", "")
file_type        = input_data.get("file_type", "").lower().strip(".")

# ---------------------------------------------------------------------------
# 2. Normalise source_type
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
#    Empty string = no folder (will trigger Slack alert path in Zapier)
# ---------------------------------------------------------------------------

FOLDER_IDS = {
    ("agency",    "audio"):      "1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz",
    ("agency",    "video"):      "10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA",
    ("agency",    "transcript"): "1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1",
    ("publisher", "audio"):      "1dsJVpjwSPmlObgww_wKpG200kcooB_m2",
    ("publisher", "video"):      "1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c",
    ("publisher", "transcript"): "",  # TBC — no folder yet
    ("internal",  "audio"):      "1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm",
    ("internal",  "video"):      "",  # TBC — no folder yet
    ("internal",  "transcript"): "",  # TBC — no folder yet
}

folder_id = FOLDER_IDS.get((source_type, media_type), "")

# Alert reason — shown in Slack alert message when no folder
if source_type == "unknown":
    alert_reason = f"Could not classify source from: '{raw_source}'"
elif media_type == "unknown":
    alert_reason = f"Unrecognised file type: .{file_type}"
elif folder_id == "":
    alert_reason = f"No Drive folder configured for {source_type} / {media_type} (TBC)"
else:
    alert_reason = ""

# ---------------------------------------------------------------------------
# 5. Build filename
#    Format: [Intel Type] — [Account] — [Summary]
#    Zapier appends the file extension separately
# ---------------------------------------------------------------------------

def slugify_part(s):
    s = s.strip()
    s = re.sub(r'[<>:"/\\|?*]', '', s)   # strip illegal filename chars
    s = re.sub(r'\s+', ' ', s)
    return s[:60].strip()                  # cap each part at 60 chars

intel_part   = slugify_part(raw_intel_type) or "Uncategorised"
account_part = slugify_part(raw_account)    or "Unknown Account"
summary_part = slugify_part(raw_summary)    or "No Summary"

file_name_base = f"{intel_part} — {account_part} — {summary_part}"

# ---------------------------------------------------------------------------
# 6. Output
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
}
