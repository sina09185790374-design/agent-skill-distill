# coverage-gate

Distilled from a session that went well. Student: any agent harness.

## Triggers

Use this skill when the task mentions: `add`, `check`, `fails`, `build`, `test`, `coverage`, `drops`, `below`.

## Steps

1. run coverage report: python3 -m coverage run -m unittest discover
2. write check script: scripts/coverage_gate.py reads the per-module report and exits 1 below 80%

## Decisions

- Measure coverage per module, not repo-wide — one untested module hides inside a repo-wide average.
- Fail open on a missing coverage file: warn instead of failing the build, so a broken reporter never blocks a release.

## Traps

- When: The check fails on a generated file that has no tests by design.
  Fix: Exclude generated files via a marker comment: files starting with '# generated' are skipped by the gate.

## Checks

- The check script passes on the reference commit (coverage 87%).
- Re-ran the gate after the fix: all modules pass, generated files skipped.

## Notes

- Output shape: 9 lines, 478 characters — full output NOT copied (see the rules below).

## Rules

- The skill teaches steps, decisions, traps and checks. It never contains the reference session's finished output — short snippets only.
- Three trials per skill version. One lucky run proves nothing.
- Checks are tested on the reference first. A check that fails on the reference is a broken check.
- Fix the skill at the first place the student goes wrong, then run again.
- A human accepts the final skill. The skill counts as done only when accepted.
