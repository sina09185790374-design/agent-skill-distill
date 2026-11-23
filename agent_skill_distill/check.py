"""CI gate for a distilled skill file.

A skill ships only if it has all four sections, no section is empty, no
fenced block is long enough to be embedded reference output, and no
secret-like token or machine-local path slipped in. Exit 1 on any problem.
"""

from __future__ import annotations

import re

from .transcript import PATH_PATTERNS, SECRET_PATTERNS

REQUIRED_SECTIONS = ["## Triggers", "## Steps", "## Traps", "## Checks"]
MAX_FENCE_LINES = 12
MIN_STEPS = 2

STEP_RE = re.compile(r"^\d+\.\s+\S")


def check_skill(text):
    """Return a list of problems (empty means the skill passes the gate)."""
    problems = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            problems.append("missing section: " + section)

    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        rest = [rest for rest in lines[index + 1 :] if rest.strip()]
        if not rest or rest[0].startswith("#"):
            problems.append("empty section: " + line[3:].strip())

    in_fence = False
    fence_start = 0
    fence_len = 0
    for lineno, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            if not in_fence:
                in_fence = True
                fence_start = lineno
                fence_len = 0
            else:
                in_fence = False
                if fence_len > MAX_FENCE_LINES:
                    problems.append(
                        "fenced block at line "
                        + str(fence_start)
                        + " has "
                        + str(fence_len)
                        + " lines (> "
                        + str(MAX_FENCE_LINES)
                        + ") — looks like embedded output"
                    )
        elif in_fence:
            fence_len += 1
    if in_fence:
        problems.append("unclosed fenced block")

    for pattern, _ in SECRET_PATTERNS + PATH_PATTERNS:
        if pattern.search(text):
            problems.append(
                "forbidden pattern in skill: " + pattern.pattern[:40] + "..."
            )
            break

    steps = [line for line in lines if STEP_RE.match(line)]
    if len(steps) < MIN_STEPS:
        problems.append(
            "only " + str(len(steps)) + " step(s) — a skill needs at least "
            + str(MIN_STEPS)
        )
    return problems
