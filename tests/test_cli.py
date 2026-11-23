"""End-to-end CLI tests on the demo session (unittest, no deps)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = str(Path(__file__).resolve().parent.parent)


def _run(*args, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "agent_skill_distill", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class TestCli(unittest.TestCase):
    def test_demo_distill_verify_check_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            demo = _run("demo", "--out", "demo-out", cwd=tmp)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            session = Path(tmp) / "demo-out" / "session.jsonl"
            skill = Path(tmp) / "demo-out" / "SKILL.md"
            self.assertTrue(session.exists())
            self.assertTrue(skill.exists())

            distilled = _run(
                "distill", str(session), "--name", "coverage-gate", "-o", "out.md", cwd=tmp
            )
            self.assertEqual(distilled.returncode, 0, distilled.stderr)
            self.assertIn("2 steps", distilled.stdout)

            verified = _run("verify", "out.md", str(session), cwd=tmp)
            self.assertEqual(verified.returncode, 0, verified.stdout)
            self.assertIn("coverage 100%", verified.stdout)

            checked = _run("check", "out.md", cwd=tmp)
            self.assertEqual(checked.returncode, 0, checked.stdout)
            self.assertIn("skill OK", checked.stdout)

    def test_verify_fails_below_min_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            _run("demo", "--out", "demo-out", cwd=tmp)
            session = Path(tmp) / "demo-out" / "session.jsonl"
            skill = Path(tmp) / "demo-out" / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            trimmed = "\n".join(
                line
                for line in text.splitlines()
                if "Fail open on a missing coverage file" not in line
            )
            Path(tmp, "trimmed.md").write_text(trimmed, encoding="utf-8")
            result = _run("verify", "trimmed.md", str(session), cwd=tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("first divergence", result.stdout)

    def test_check_fails_on_broken_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "bad.md").write_text(
                "# bad\n\n## Steps\n\n1. do a thing\n", encoding="utf-8"
            )
            result = _run("check", "bad.md", cwd=tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL", result.stdout)

    def test_distill_missing_file_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(
                "distill", "no-such.jsonl", "--name", "x", cwd=tmp
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("error", result.stderr)


if __name__ == "__main__":
    unittest.main()
