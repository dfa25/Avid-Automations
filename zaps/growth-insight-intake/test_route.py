#!/usr/bin/env python3
"""
Standalone test harness for zap2-route.py.
Run with: python test_route.py

Wraps the routing logic by executing the script in an isolated namespace
with a mocked input_data dict (the global Zapier injects at runtime).
"""

import os
import sys

ROUTE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zap2-route.py")


def run_route(input_data_dict: dict) -> dict:
    """Execute zap2-route.py with a mock input_data and return its output dict."""
    with open(ROUTE_SCRIPT) as f:
        code = f.read()
    ns = {"input_data": input_data_dict, "__builtins__": __builtins__}
    exec(compile(code, ROUTE_SCRIPT, "exec"), ns)  # noqa: S102
    return ns["output"]


def make_message(
    source="agency",
    file_url="https://files.slack.com/files-pri/T.../x.mp3",
    file_type="mp3",
    intel_type="Account Manager Interview",
    account="NewsCorp",
    summary="Great insight about buyer frustration with pricing.",
) -> str:
    """Build a Slack Workflow form-response message in the expected format."""
    return (
        f"📎 New file ready for intake.\n"
        f"file_url: {file_url}\n"
        f"file_type: {file_type}\n"
        f"original_ts: 1776392328.966289\n"
        f"source: {source}\n"
        f"Intel Type: {intel_type}\n"
        f"Account: {account}\n"
        f"Category: Positioning\n"
        f"Product Area: Buyer\n"
        f"Type: Sales meeting\n"
        f"Summary: {summary}\n"
        f"Timing: Actionable this fortnight"
    )


# ---------------------------------------------------------------------------
# Folder IDs mirrored from routing table — keeps assertions readable
# ---------------------------------------------------------------------------
FOLDER = {
    ("agency",    "audio"):      "1E15TBvroLSAuZeedRWWM5Q2wVCBO4Exz",
    ("agency",    "video"):      "10k8Aq61XdfWGyZ6_WqFNmRbML1nb12gA",
    ("agency",    "transcript"): "1FkOlFsHsBnYUBbYBVikj9d05c2axq2M1",
    ("publisher", "audio"):      "1dsJVpjwSPmlObgww_wKpG200kcooB_m2",
    ("publisher", "video"):      "1RSY_LDJYhuHYYiTZ0FjPJflhbCThKV9c",
    ("internal",  "audio"):      "1rN6_sVcs0nD8CdJvwSOvz6TnOrVhLulm",
}

# ---------------------------------------------------------------------------
# Test registry
# ---------------------------------------------------------------------------
TESTS = []


def test(name):
    def decorator(fn):
        TESTS.append((name, fn))
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Source × media routing tests
# ---------------------------------------------------------------------------

@test("agency + audio (mp3) → correct folder, no alert")
def _():
    out = run_route({
        "message_text": make_message(source="agency", file_type="mp3"),
        "file_url": "https://slack.com/x.mp3",
        "file_type": "mp3",
    })
    assert out["source_type"] == "agency"
    assert out["media_type"] == "audio"
    assert out["folder_id"] == FOLDER[("agency", "audio")]
    assert out["alert_reason"] == ""


@test("agency + video (mp4) → correct folder, no alert")
def _():
    out = run_route({
        "message_text": make_message(source="agency", file_type="mp4"),
        "file_url": "https://slack.com/x.mp4",
        "file_type": "mp4",
    })
    assert out["source_type"] == "agency"
    assert out["media_type"] == "video"
    assert out["folder_id"] == FOLDER[("agency", "video")]
    assert out["alert_reason"] == ""


@test("agency + transcript (pdf) → correct folder, no alert")
def _():
    out = run_route({
        "message_text": make_message(source="agency", file_type="pdf"),
        "file_url": "https://slack.com/x.pdf",
        "file_type": "pdf",
    })
    assert out["source_type"] == "agency"
    assert out["media_type"] == "transcript"
    assert out["folder_id"] == FOLDER[("agency", "transcript")]
    assert out["alert_reason"] == ""


@test("publisher + audio (wav) → correct folder, no alert")
def _():
    out = run_route({
        "message_text": make_message(source="publisher", file_type="wav"),
        "file_url": "https://slack.com/x.wav",
        "file_type": "wav",
    })
    assert out["source_type"] == "publisher"
    assert out["media_type"] == "audio"
    assert out["folder_id"] == FOLDER[("publisher", "audio")]
    assert out["alert_reason"] == ""


@test("publisher + video (mov) → correct folder, no alert")
def _():
    out = run_route({
        "message_text": make_message(source="publisher", file_type="mov"),
        "file_url": "https://slack.com/x.mov",
        "file_type": "mov",
    })
    assert out["source_type"] == "publisher"
    assert out["media_type"] == "video"
    assert out["folder_id"] == FOLDER[("publisher", "video")]
    assert out["alert_reason"] == ""


@test("publisher + transcript (docx) → TBC: empty folder, alert")
def _():
    out = run_route({
        "message_text": make_message(source="publisher", file_type="docx"),
        "file_url": "https://slack.com/x.docx",
        "file_type": "docx",
    })
    assert out["source_type"] == "publisher"
    assert out["media_type"] == "transcript"
    assert out["folder_id"] == ""
    assert "TBC" in out["alert_reason"]


@test("internal + audio (m4a) → correct folder, no alert")
def _():
    out = run_route({
        "message_text": make_message(source="internal", file_type="m4a"),
        "file_url": "https://slack.com/x.m4a",
        "file_type": "m4a",
    })
    assert out["source_type"] == "internal"
    assert out["media_type"] == "audio"
    assert out["folder_id"] == FOLDER[("internal", "audio")]
    assert out["alert_reason"] == ""


@test("internal + video (mp4) → TBC: empty folder, alert")
def _():
    out = run_route({
        "message_text": make_message(source="internal", file_type="mp4"),
        "file_url": "https://slack.com/x.mp4",
        "file_type": "mp4",
    })
    assert out["source_type"] == "internal"
    assert out["media_type"] == "video"
    assert out["folder_id"] == ""
    assert "TBC" in out["alert_reason"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@test("'Agency - Design Partner' normalises to agency source_type")
def _():
    out = run_route({
        "message_text": make_message(source="Agency - Design Partner", file_type="mp3"),
        "file_url": "https://slack.com/x.mp3",
        "file_type": "mp3",
    })
    assert out["source_type"] == "agency", f"got {out['source_type']!r}"
    assert out["folder_id"] == FOLDER[("agency", "audio")]


@test("unknown source → source_type=unknown, alert includes raw value")
def _():
    out = run_route({
        "message_text": make_message(source="foobar_unknown", file_type="mp3"),
        "file_url": "https://slack.com/x.mp3",
        "file_type": "mp3",
    })
    assert out["source_type"] == "unknown"
    assert out["folder_id"] == ""
    assert "foobar_unknown" in out["alert_reason"]


@test("unknown extension (.xyz) → media_type=unknown, alert includes extension")
def _():
    out = run_route({
        "message_text": make_message(source="agency", file_type="xyz"),
        "file_url": "https://slack.com/x.xyz",
        "file_type": "xyz",
    })
    assert out["media_type"] == "unknown"
    assert out["folder_id"] == ""
    assert "xyz" in out["alert_reason"]


@test("file_url absent from input_data — falls back to message text")
def _():
    msg = make_message(
        source="agency",
        file_url="https://files.slack.com/files-pri/T.../x.mp3",
        file_type="mp3",
    )
    out = run_route({"message_text": msg, "file_url": "", "file_type": "mp3"})
    assert out["source_type"] == "agency"
    assert out["media_type"] == "audio"
    assert out["folder_id"] == FOLDER[("agency", "audio")]


@test("garbled / empty message → all fields unknown, non-empty alert")
def _():
    out = run_route({"message_text": "random garbage text", "file_url": "", "file_type": ""})
    assert out["source_type"] == "unknown"
    assert out["media_type"] == "unknown"
    assert out["folder_id"] == ""
    assert out["alert_reason"] != ""


@test("empty form (all inputs blank) → falls back to placeholder filename parts")
def _():
    out = run_route({"message_text": "", "file_url": "", "file_type": ""})
    assert "Uncategorised" in out["file_name_base"]
    assert "Unknown Account" in out["file_name_base"]
    assert "No Summary" in out["file_name_base"]


@test("filename strips illegal characters from intel_type / account / summary")
def _():
    out = run_route({
        "message_text": make_message(
            source="agency",
            file_type="mp3",
            intel_type='Intel: "Quoted" <test>',
            account="Acme/Corp",
            summary="Insight\\here|there?",
        ),
        "file_url": "https://slack.com/x.mp3",
        "file_type": "mp3",
    })
    illegal = set('<>:"/\\|?*')
    found = illegal & set(out["file_name_base"])
    assert not found, f"Illegal chars in filename: {found!r}  →  {out['file_name_base']!r}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all() -> int:
    passed = failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {name}")
            print(f"        {exc}")
            failed += 1
    total = passed + failed
    print(f"\n{'=' * 60}")
    if failed:
        print(f"Results: {passed}/{total} passed, {failed} FAILED")
    else:
        print(f"Results: {passed}/{total} passed — all OK")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())
