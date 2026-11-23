"""Session transcript parsing and scrubbing (stdlib only).

A transcript is JSONL: one event per line.

    {"turn": 1, "role": "user", "kind": "prompt",
     "text": "Add a CI check that fails when coverage drops below 80%."}

Roles: ``user`` | ``agent`` | ``tool``.
Kinds: ``prompt`` | ``message`` | ``tool_call`` | ``tool_result`` |
``decision`` | ``check`` | ``error`` | ``fix`` | ``note``.

Raw transcripts contain machine paths and sometimes secrets. Everything
the distiller emits goes through :func:`scrub` first, and long tool
output is never copied verbatim — see :mod:`agent_skill_distill.distill`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

KINDS = {
    "prompt",
    "message",
    "tool_call",
    "tool_result",
    "decision",
    "check",
    "error",
    "fix",
    "note",
}
ROLES = {"user", "agent", "tool"}

SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{8,}"), "[redacted-secret]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[redacted-secret]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[redacted-secret]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{8,}"), "[redacted-secret]"),
    (re.compile(r"Bearer\s+\S+"), "Bearer [redacted-secret]"),
    (
        re.compile(r"(?i)(api[_-]?key|password|passwd|token)\s*[:=]\s*\S+"),
        r"\1=[redacted-secret]",
    ),
]

PATH_PATTERNS = [
    (re.compile(r"/home/[^\s\"']+"), "[redacted-path]"),
    (re.compile(r"/Users/[^\s\"']+"), "[redacted-path]"),
    (re.compile(r"C:\\Users\\[^\s\"']+"), "[redacted-path]"),
]

EN_STOP = set(
    "a an the and or of to in on for with is are was were be been it its this that "
    "these those you your we our they he she i me my do does did not no yes at by "
    "from as but if then so than too very just also only when where which who what "
    "how can could should would will".split()
)
FA_STOP = set("و یا که در به از با برای این آن ها هست است بود شود می را".split())
STOPWORDS = EN_STOP | FA_STOP

WORD_RE = re.compile(r"[^\W\d_]+|\d+", re.UNICODE)


def scrub(text):
    """Redact secret-like tokens and machine-local paths from *text*."""
    out = text
    for pattern, repl in SECRET_PATTERNS + PATH_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def content_words(text, limit=8):
    """Distinct content words of *text*, in order, stopwords removed."""
    words = []
    seen = set()
    for match in WORD_RE.finditer(text.lower()):
        word = match.group(0)
        if len(word) < 3 or word in STOPWORDS or word in seen:
            continue
        seen.add(word)
        words.append(word)
        if len(words) >= limit:
            break
    return words


def load_jsonl(path):
    """Load and validate a transcript file; events come back in turn order."""
    events = []
    for lineno, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"{path}:{lineno}: event must be an object")
        for field in ("turn", "role", "kind", "text"):
            if field not in event:
                raise ValueError(f"{path}:{lineno}: missing field {field!r}")
        if event["kind"] not in KINDS:
            raise ValueError(f"{path}:{lineno}: unknown kind {event['kind']!r}")
        if event["role"] not in ROLES:
            raise ValueError(f"{path}:{lineno}: unknown role {event['role']!r}")
        if not isinstance(event["text"], str):
            raise ValueError(f"{path}:{lineno}: text must be a string")
        events.append(event)
    events.sort(key=lambda e: e["turn"])
    return events


def first_line(text):
    """First non-empty line of *text*, or ""."""
    stripped = text.strip()
    return stripped.splitlines()[0] if stripped else ""
