"""
Zapier Code step 1: parse user-provided fields from the Slack message
and classify media type from file extension.

Input fields (map from trigger in Zapier UI):
  message_text  → Slack message text
  file_name     → all_files[0].title / name
  file_type     → all_files[0].filetype (extension, lowercase)

Output fields are flat keys Zapier exposes to later steps.
"""
import re

msg = input_data.get('message_text', '') or ''
filename = input_data.get('file_name', '') or ''
filetype = (input_data.get('file_type', '') or '').lower()


def extract_field(text, field):
    pattern = rf'{re.escape(field)}\s*[:\-]\s*(.+?)(?:\n|$)'
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ''


intel_type = extract_field(msg, 'Intel Type')
source_raw = extract_field(msg, 'Source')
account = extract_field(msg, 'Account')
summary = extract_field(msg, 'Summary')
context = extract_field(msg, 'Context') or extract_field(msg, 'Detail')

AUDIO = {'mp3', 'm4a', 'wav', 'aac', 'ogg', 'flac', 'wma', 'aiff', 'opus'}
VIDEO = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'webm', 'm4v', 'flv'}
DOCS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'xlsx', 'xls', 'csv', 'ppt', 'pptx'}

if filetype in AUDIO:
    media_type = 'audio'
elif filetype in VIDEO:
    media_type = 'video'
elif filetype in DOCS:
    media_type = 'transcript'
else:
    media_type = 'unknown'

sl = source_raw.lower()
if 'agency' in sl:
    source_type = 'agency'
elif 'publisher' in sl:
    source_type = 'publisher'
elif 'internal' in sl or 'avid' in sl:
    source_type = 'internal'
else:
    source_type = 'unknown'

needs_ai = (
    not intel_type
    or source_type == 'unknown'
    or not account
)

output = {
    'intel_type': intel_type,
    'source_type': source_type,
    'source_raw': source_raw,
    'account': account,
    'summary': summary,
    'context': context,
    'media_type': media_type,
    'needs_ai': 'true' if needs_ai else 'false',
}
