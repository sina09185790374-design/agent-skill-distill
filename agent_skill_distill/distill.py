"""Distill a session transcript into a skill (pattern only, original code).

The pattern, learned from sybil-solutions/skill-distill: a good session is
worth more than a good prompt. The teacher reads the session, writes a
skill for a named student, and the skill teaches the *steps, decisions,
traps and checks* — never the reference session's finished output. This
module is the offline half of that loop: it extracts those four lists from
a transcript and renders them as a SKILL.md. Running the student against
the skill (trials, first-divergence fix, human accept) is a human loop
around this output; :mod:`agent_skill_distill.verify` checks the skill
still covers every decision, trap and check the session taught.
"""

from __future__ import annotations

from .transcript import content_words, first_line, scrub

SNIPPET_LIMIT = 120
OUTPUT_SUMMARY_LIMIT = 200


def _short(text, limit=160):
    """One scrubbed line: collapse whitespace, truncate with an ellipsis."""
    text = " ".join(scrub(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def distill(events, name, student):
    """Extract triggers, steps, decisions, traps and checks from *events*."""
    prompts = [e for e in events if e["kind"] == "prompt"]
    triggers = content_words(prompts[0]["text"], limit=8) if prompts else []

    steps = []
    for event in events:
        if event["kind"] != "tool_call":
            continue
        step = _short(first_line(event["text"]), 100)
        if step and (not steps or steps[-1] != step):
            steps.append(step)

    decisions = [_short(e["text"]) for e in events if e["kind"] == "decision"]

    traps = []
    for index, event in enumerate(events):
        if event["kind"] != "error":
            continue
        fix = next(
            (f for f in events[index + 1 :] if f["kind"] == "fix"), None
        )
        traps.append(
            {
                "when": _short(event["text"]),
                "fix": _short(fix["text"])
                if fix
                else "Unresolved in this session — do not ship the skill until this is fixed.",
            }
        )

    checks = [_short(e["text"]) for e in events if e["kind"] == "check"]

    notes = []
    for event in events:
        if event["kind"] == "tool_result" and len(event["text"]) > OUTPUT_SUMMARY_LIMIT:
            # Shape only — never quote the output, not even its first line:
            # the first line can carry ids, paths or secrets of its own.
            lines = event["text"].strip().splitlines()
            notes.append(
                "Output shape: "
                + str(len(lines))
                + " lines, "
                + str(len(event["text"]))
                + " characters — full output NOT copied (see the rules below)."
            )
    return {
        "name": name,
        "student": student,
        "triggers": triggers,
        "steps": steps,
        "decisions": decisions,
        "traps": traps,
        "checks": checks,
        "notes": notes,
    }


def render_skill(skill):
    """Render a distilled skill dict as SKILL.md Markdown."""
    lines = ["# " + skill["name"], ""]
    lines.append(
        "Distilled from a session that went well. Student: "
        + skill["student"]
        + "."
    )
    lines.append("")
    lines.append("## Triggers")
    lines.append("")
    if skill["triggers"]:
        lines.append(
            "Use this skill when the task mentions: "
            + ", ".join("`" + t + "`" for t in skill["triggers"])
            + "."
        )
    else:
        lines.append("No trigger words found in the session prompt.")
    lines.append("")
    lines.append("## Steps")
    lines.append("")
    for index, step in enumerate(skill["steps"], 1):
        lines.append(str(index) + ". " + step)
    if not skill["steps"]:
        lines.append("No tool calls recorded in the session.")
    lines.append("")
    lines.append("## Decisions")
    lines.append("")
    for decision in skill["decisions"]:
        lines.append("- " + decision)
    if not skill["decisions"]:
        lines.append("No explicit decisions recorded in the session.")
    lines.append("")
    lines.append("## Traps")
    lines.append("")
    for trap in skill["traps"]:
        lines.append("- When: " + trap["when"])
        lines.append("  Fix: " + trap["fix"])
    if not skill["traps"]:
        lines.append("No error in the session — nothing to warn the student about.")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    for check in skill["checks"]:
        lines.append("- " + check)
    if not skill["checks"]:
        lines.append("No checks recorded in the session.")
    lines.append("")
    if skill["notes"]:
        lines.append("## Notes")
        lines.append("")
        for note in skill["notes"]:
            lines.append("- " + note)
        lines.append("")
    lines.append("## Rules")
    lines.append("")
    lines.append(
        "- The skill teaches steps, decisions, traps and checks. It never "
        "contains the reference session's finished output — short snippets only."
    )
    lines.append(
        "- Three trials per skill version. One lucky run proves nothing."
    )
    lines.append(
        "- Checks are tested on the reference first. A check that fails on "
        "the reference is a broken check."
    )
    lines.append(
        "- Fix the skill at the first place the student goes wrong, then run again."
    )
    lines.append(
        "- A human accepts the final skill. The skill counts as done only "
        "when accepted."
    )
    lines.append("")
    return "\n".join(lines)
