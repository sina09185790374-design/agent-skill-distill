"""Tests for transcript parsing and scrubbing (unittest, no deps)."""

import json
import tempfile
import unittest
from pathlib import Path

from agent_skill_distill.demo import demo_events
from agent_skill_distill.transcript import content_words, load_jsonl, scrub


def _write_jsonl(events):
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    )
    with tmp:
        for event in events:
            tmp.write(json.dumps(event, ensure_ascii=False) + "\n")
    return tmp.name


class TestLoadJsonl(unittest.TestCase):
    def test_demo_session_loads_in_turn_order(self):
        events = demo_events()
        path = _write_jsonl(list(reversed(events)))
        loaded = load_jsonl(path)
        self.assertEqual([e["turn"] for e in loaded], sorted(e["turn"] for e in events))
        self.assertEqual(len(loaded), 12)

    def test_unknown_kind_rejected(self):
        path = _write_jsonl(
            [{"turn": 1, "role": "user", "kind": "teleport", "text": "x"}]
        )
        with self.assertRaises(ValueError):
            load_jsonl(path)

    def test_missing_field_rejected(self):
        path = _write_jsonl([{"turn": 1, "role": "user", "kind": "prompt"}])
        with self.assertRaises(ValueError):
            load_jsonl(path)

    def test_invalid_json_rejected(self):
        tmp = tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        with tmp:
            tmp.write("{not json\n")
        with self.assertRaises(ValueError):
            load_jsonl(tmp.name)

    def test_blank_lines_skipped(self):
        path = _write_jsonl(demo_events())
        text = Path(path).read_text(encoding="utf-8")
        Path(path).write_text("\n" + text + "\n\n", encoding="utf-8")
        self.assertEqual(len(load_jsonl(path)), 12)


class TestScrub(unittest.TestCase):
    def test_api_key_redacted(self):
        self.assertNotIn("sk-abc123XYZ", scrub("key is sk-abc123XYZ here"))
        self.assertIn("[redacted-secret]", scrub("key is sk-abc123XYZ here"))

    def test_github_token_redacted(self):
        self.assertIn(
            "[redacted-secret]", scrub("token ghp_0123456789abcdefghij here")
        )

    def test_home_path_redacted(self):
        self.assertIn(
            "[redacted-path]", scrub("read /home/sina/notes/private.md first")
        )

    def test_clean_text_unchanged(self):
        text = "Measure coverage per module, not repo-wide."
        self.assertEqual(scrub(text), text)


class TestContentWords(unittest.TestCase):
    def test_stopwords_dropped_order_kept(self):
        words = content_words("Add a CI check that fails the build when coverage drops")
        self.assertEqual(words, ["add", "check", "fails", "build", "coverage", "drops"])

    def test_limit_respected(self):
        words = content_words("alpha beta gamma delta epsilon zeta", limit=3)
        self.assertEqual(words, ["alpha", "beta", "gamma"])

    def test_persian_words_kept(self):
        words = content_words("پوشش تست ماژول را اندازه بگیر")
        self.assertIn("پوشش", words)
        self.assertIn("ماژول", words)
        self.assertNotIn("را", words)


if __name__ == "__main__":
    unittest.main()
