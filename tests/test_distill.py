"""Tests for the distiller (unittest, no deps)."""

import unittest

from agent_skill_distill.demo import MARKER, demo_events
from agent_skill_distill.distill import distill, render_skill


class TestDistill(unittest.TestCase):
    def setUp(self):
        self.events = demo_events()
        self.skill = distill(self.events, "coverage-gate", "any agent harness")
        self.text = render_skill(self.skill)

    def test_triggers_come_from_first_prompt(self):
        self.assertIn("coverage", self.skill["triggers"])
        self.assertIn("check", self.skill["triggers"])

    def test_steps_are_the_tool_calls_in_order(self):
        self.assertEqual(len(self.skill["steps"]), 2)
        self.assertTrue(self.skill["steps"][0].startswith("run coverage report"))
        self.assertTrue(self.skill["steps"][1].startswith("write check script"))

    def test_consecutive_duplicate_tool_calls_dedupe(self):
        events = self.events + [
            {
                "turn": 13,
                "role": "agent",
                "kind": "tool_call",
                "text": "write check script: scripts/coverage_gate.py reads the per-module report and exits 1 below 80%",
            }
        ]
        skill = distill(events, "coverage-gate", "any agent harness")
        self.assertEqual(len(skill["steps"]), 2)

    def test_trap_pairs_error_with_following_fix(self):
        self.assertEqual(len(self.skill["traps"]), 1)
        trap = self.skill["traps"][0]
        self.assertIn("generated file", trap["when"])
        self.assertIn("marker comment", trap["fix"])

    def test_unresolved_error_is_flagged_not_hidden(self):
        events = [
            {"turn": 1, "role": "user", "kind": "prompt", "text": "Do the thing."},
            {"turn": 2, "role": "agent", "kind": "error", "text": "The build broke."},
        ]
        skill = distill(events, "x", "y")
        self.assertEqual(len(skill["traps"]), 1)
        self.assertIn("Unresolved", skill["traps"][0]["fix"])

    def test_long_tool_output_is_never_copied_verbatim(self):
        # The marker lives only in the long tool result; the skill must not
        # contain it — only an "output shape" note may mention the output.
        self.assertNotIn(MARKER, self.text)
        self.assertIn("Output shape", self.text)
        self.assertNotIn("module billing: 84%", self.text)

    def test_decisions_and_checks_land_in_the_skill(self):
        self.assertIn("per module, not repo-wide", self.text)
        self.assertIn("Fail open on a missing coverage file", self.text)
        self.assertIn("passes on the reference commit", self.text)

    def test_secrets_in_session_are_scrubbed_from_skill(self):
        events = demo_events() + [
            {
                "turn": 13,
                "role": "agent",
                "kind": "decision",
                "text": "Store the key sk-abc123XYZ in the config.",
            }
        ]
        text = render_skill(distill(events, "x", "y"))
        self.assertNotIn("sk-abc123XYZ", text)
        self.assertIn("[redacted-secret]", text)

    def test_all_four_sections_rendered(self):
        for section in ("## Triggers", "## Steps", "## Decisions", "## Traps", "## Checks", "## Rules"):
            self.assertIn(section, self.text)


if __name__ == "__main__":
    unittest.main()
