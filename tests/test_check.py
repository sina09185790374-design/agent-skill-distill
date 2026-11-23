"""Tests for the skill CI gate (unittest, no deps)."""

import unittest

from agent_skill_distill.check import check_skill
from agent_skill_distill.demo import demo_events
from agent_skill_distill.distill import distill, render_skill


def _demo_skill():
    return render_skill(distill(demo_events(), "coverage-gate", "any agent harness"))


class TestCheck(unittest.TestCase):
    def test_demo_skill_passes(self):
        self.assertEqual(check_skill(_demo_skill()), [])

    def test_missing_section_fails(self):
        text = _demo_skill().replace("## Traps\n", "")
        problems = check_skill(text)
        self.assertTrue(any("missing section" in p and "Traps" in p for p in problems))

    def test_empty_section_fails(self):
        text = _demo_skill().replace(
            "## Notes\n", "## Notes\n\n## Empty\n\n"
        )
        problems = check_skill(text)
        self.assertTrue(any("empty section" in p for p in problems))

    def test_long_fenced_block_fails(self):
        block = "```\n" + "\n".join("line %d" % i for i in range(20)) + "\n```\n"
        problems = check_skill(_demo_skill() + "\n" + block)
        self.assertTrue(any("fenced block" in p for p in problems))

    def test_secret_in_skill_fails(self):
        problems = check_skill(_demo_skill() + "\nkey: sk-abc123XYZ\n")
        self.assertTrue(any("forbidden pattern" in p for p in problems))

    def test_home_path_in_skill_fails(self):
        problems = check_skill(_demo_skill() + "\nsee /home/sina/x\n")
        self.assertTrue(any("forbidden pattern" in p for p in problems))

    def test_fewer_than_two_steps_fails(self):
        text = _demo_skill()
        lines = [line for line in text.splitlines() if not line.startswith("1. ") and not line.startswith("2. ")]
        problems = check_skill("\n".join(lines))
        self.assertTrue(any("step" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
