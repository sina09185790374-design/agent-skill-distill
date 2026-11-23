"""Tests for skill coverage verification (unittest, no deps)."""

import unittest

from agent_skill_distill.demo import demo_events
from agent_skill_distill.distill import distill, render_skill
from agent_skill_distill.verify import verify


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.events = demo_events()
        self.skill_text = render_skill(
            distill(self.events, "coverage-gate", "any agent harness")
        )

    def test_demo_skill_covers_the_whole_session(self):
        result = verify(self.skill_text, self.events)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["total"], 5)  # 2 decisions + 2 checks + 1 trap
        self.assertIsNone(result["first_divergence"])

    def test_removed_decision_drops_score_and_names_first_divergence(self):
        trimmed = "\n".join(
            line
            for line in self.skill_text.splitlines()
            if "Fail open on a missing coverage file" not in line
        )
        result = verify(trimmed, self.events)
        self.assertLess(result["score"], 100)
        self.assertIsNotNone(result["first_divergence"])
        self.assertEqual(result["first_divergence"]["kind"], "decision")
        self.assertIn("Fail open", result["first_divergence"]["text"])

    def test_removed_trap_is_uncovered(self):
        # Trap words must not echo the prompt, or the triggers line alone
        # would keep the trap "covered" after its own lines are removed.
        events = [
            {"turn": 1, "role": "user", "kind": "prompt", "text": "Deploy the purple widget."},
            {"turn": 2, "role": "agent", "kind": "tool_call", "text": "run deploy script"},
            {"turn": 3, "role": "agent", "kind": "tool_call", "text": "verify deployment health"},
            {"turn": 4, "role": "agent", "kind": "error", "text": "The deploy failed on a chartreuse sprocket."},
            {"turn": 5, "role": "agent", "kind": "fix", "text": "Lubricate the chartreuse sprocket and redeploy."},
        ]
        skill_text = render_skill(distill(events, "deploy-widget", "any agent harness"))
        self.assertEqual(verify(skill_text, events)["score"], 100)
        trimmed = "\n".join(
            line for line in skill_text.splitlines() if "chartreuse" not in line
        )
        result = verify(trimmed, events)
        kinds = [item["kind"] for item in result["uncovered"]]
        self.assertIn("trap", kinds)

    def test_empty_session_scores_100(self):
        result = verify(self.skill_text, [])
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["total"], 0)


if __name__ == "__main__":
    unittest.main()
