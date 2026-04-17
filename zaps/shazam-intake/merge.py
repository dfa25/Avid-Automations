"""
Zapier Code step 2: merge fields parsed from the message (step 1)
with any fields the Anthropic step inferred.

Anthropic returns JSON like:
  {"intel_type": "...", "source_type": "...", "account": "..."}

Input fields (map in Zapier UI):
  parsed_intel_type, parsed_source_type, parsed_account, parsed_summary,
  parsed_media_type, parsed_context, parsed_source_raw,
  ai_response  → raw text output from the Anthropic step (may be empty
                 if AI was skipped because needs_ai was false)

Output: final classification used by downstream routing + file rename.
"""
import json
import re

parsed = {
    'intel_type': input_data.get('parsed_intel_type', '') or '',
    'source_type': input_data.get('parsed_source_type', '') or '',
    'account': input_data.get('parsed_account', '') or '',
    'summary': input_data.get('parsed_summary', '') or '',
    'context': input_data.get('parsed_context', '') or '',
    'media_type': input_data.get('parsed_media_type', '') or '',
    'source_raw': input_data.get('parsed_source_raw', '') or '',
}

ai_raw = input_data.get('ai_response', '') or ''
ai = {}
if ai_raw.strip():
    match = re.search(r'\{.*\}', ai_raw, re.DOTALL)
    if match:
        try:
            ai = json.loads(match.group(0))
        except json.JSONDecodeError:
            ai = {}


def pick(field, default='unknown'):
    value = parsed.get(field) or ai.get(field) or default
    return str(value).strip() or default


intel_type = pick('intel_type', default='Uncategorised')
source_type = pick('source_type', default='unknown').lower()
account = pick('account', default='Unknown')
summary = parsed['summary'] or ai.get('summary') or 'Untitled'
media_type = parsed['media_type'] or 'unknown'

if source_type not in {'agency', 'publisher', 'internal'}:
    source_type = 'unknown'

file_name_base = f'{intel_type} — {account} — {summary}'

output = {
    'intel_type': intel_type,
    'source_type': source_type,
    'account': account,
    'summary': summary,
    'context': parsed['context'],
    'media_type': media_type,
    'source_raw': parsed['source_raw'],
    'file_name_base': file_name_base,
}
