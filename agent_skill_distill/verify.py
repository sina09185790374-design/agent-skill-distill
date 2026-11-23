"""Verify a skill still covers what its session taught.

The check is the offline half of the teacher loop: every decision, trap
and check in the session has key words, and the skill must still contain
them. The first uncovered item is the *first divergence* — the place
where a student following this skill would first go wrong. Fix the skill
there, then run again.
"""

from __future__ import annotations

from .transcript import content_words

MIN_WORDS_TO_COVER = 3


def _key_words(text, limit=4):
    return content_words(text, limit=limit)


def _covered(key_words, haystack_lower):
    if not key_words:
        return True
    found = sum(1 for word in key_words if word in haystack_lower)
    return found >= min(MIN_WORDS_TO_COVER, len(key_words))


def verify(skill_text, events):
    """Score *skill_text* against *events*; return coverage + first divergence."""
    haystack = skill_text.lower()
    items = []
    for event in events:
        if event["kind"] in ("decision", "check"):
            items.append((event["kind"], event["text"]))
    for index, event in enumerate(events):
        if event["kind"] != "error":
            continue
        fix = next(
            (f for f in events[index + 1 :] if f["kind"] == "fix"), None
        )
        combined = event["text"] + " " + (fix["text"] if fix else "")
        items.append(("trap", combined))

    covered, uncovered = [], []
    for kind, text in items:
        words = _key_words(text, limit=4)
        entry = {"kind": kind, "text": text, "key_words": words}
        (covered if _covered(words, haystack) else uncovered).append(entry)

    total = len(items)
    score = round(100 * len(covered) / total) if total else 100
    return {
        "score": score,
        "total": total,
        "covered": covered,
        "uncovered": uncovered,
        "first_divergence": uncovered[0] if uncovered else None,
    }
