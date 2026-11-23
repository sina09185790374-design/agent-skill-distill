"""Demo session + distilled skill (deterministic, no network, no secrets).

The session is a good run of a small task: add a coverage gate to a
repo. It contains one error/fix trap (a generated file), two decisions,
two checks, and one long tool result — the long result carries a unique
marker so tests can prove it is never copied into the skill.
"""

from __future__ import annotations

import json
from pathlib import Path

from .distill import distill, render_skill

MARKER = "ZEBRA-9Q2X-UNIQUE"

LONG_TOOL_RESULT = "\n".join(
    [
        "coverage report — trace-id " + MARKER,
        "module auth: 91% covered (212 statements, 19 missed)",
        "module billing: 84% covered (340 statements, 54 missed)",
        "module reports: 79% covered (188 statements, 40 missed)",
        "module search: 93% covered (156 statements, 11 missed)",
        "module export: 88% covered (274 statements, 33 missed)",
        "module import: 82% covered (301 statements, 55 missed)",
        "module notify: 90% covered (143 statements, 14 missed)",
        "TOTAL: 87% covered (1614 statements, 226 missed)",
    ]
)


def demo_events():
    """Return a fresh copy of the demo session events."""
    return [
        {
            "turn": 1,
            "role": "user",
            "kind": "prompt",
            "text": "Add a CI check that fails the build when test coverage drops below 80%.",
        },
        {
            "turn": 2,
            "role": "agent",
            "kind": "message",
            "text": "First I will read the test layout to see how coverage is measured today.",
        },
        {
            "turn": 3,
            "role": "agent",
            "kind": "tool_call",
            "text": "run coverage report: python3 -m coverage run -m unittest discover",
        },
        {"turn": 4, "role": "tool", "kind": "tool_result", "text": LONG_TOOL_RESULT},
        {
            "turn": 5,
            "role": "agent",
            "kind": "decision",
            "text": "Measure coverage per module, not repo-wide — one untested module hides inside a repo-wide average.",
        },
        {
            "turn": 6,
            "role": "agent",
            "kind": "tool_call",
            "text": "write check script: scripts/coverage_gate.py reads the per-module report and exits 1 below 80%",
        },
        {
            "turn": 7,
            "role": "agent",
            "kind": "check",
            "text": "The check script passes on the reference commit (coverage 87%).",
        },
        {
            "turn": 8,
            "role": "agent",
            "kind": "error",
            "text": "The check fails on a generated file that has no tests by design.",
        },
        {
            "turn": 9,
            "role": "agent",
            "kind": "fix",
            "text": "Exclude generated files via a marker comment: files starting with '# generated' are skipped by the gate.",
        },
        {
            "turn": 10,
            "role": "agent",
            "kind": "check",
            "text": "Re-ran the gate after the fix: all modules pass, generated files skipped.",
        },
        {
            "turn": 11,
            "role": "agent",
            "kind": "decision",
            "text": "Fail open on a missing coverage file: warn instead of failing the build, so a broken reporter never blocks a release.",
        },
        {
            "turn": 12,
            "role": "agent",
            "kind": "message",
            "text": "Done: coverage gate added, 87% on the reference commit, generated files excluded.",
        },
    ]


def write_demo(outdir):
    """Write the demo session + distilled skill; return both paths."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    session_path = outdir / "session.jsonl"
    skill_path = outdir / "SKILL.md"
    events = demo_events()
    session_path.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n",
        encoding="utf-8",
    )
    skill = distill(events, "coverage-gate", "any agent harness")
    skill_path.write_text(render_skill(skill), encoding="utf-8")
    return session_path, skill_path
