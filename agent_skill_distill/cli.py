"""CLI for agent-skill-distill."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .check import check_skill
from .demo import write_demo
from .distill import distill, render_skill
from .transcript import load_jsonl
from .verify import verify

VERSION = "0.1.0"


def _cmd_distill(args):
    events = load_jsonl(args.session)
    skill = distill(events, args.name, args.student)
    text = render_skill(skill)
    Path(args.output).write_text(text, encoding="utf-8")
    print(
        "wrote "
        + args.output
        + " ("
        + str(len(skill["steps"]))
        + " steps, "
        + str(len(skill["decisions"]))
        + " decisions, "
        + str(len(skill["traps"]))
        + " traps, "
        + str(len(skill["checks"]))
        + " checks)"
    )
    return 0


def _cmd_verify(args):
    events = load_jsonl(args.session)
    text = Path(args.skill).read_text(encoding="utf-8")
    result = verify(text, events)
    print(
        "coverage "
        + str(result["score"])
        + "% ("
        + str(len(result["covered"]))
        + "/"
        + str(result["total"])
        + ")"
    )
    for item in result["uncovered"]:
        print("  UNCOVERED [" + item["kind"] + "] " + item["text"][:100])
    if result["first_divergence"]:
        print(
            "first divergence: ["
            + result["first_divergence"]["kind"]
            + "] "
            + result["first_divergence"]["text"][:120]
        )
    return 0 if result["score"] >= args.min_score else 1


def _cmd_check(args):
    text = Path(args.skill).read_text(encoding="utf-8")
    problems = check_skill(text)
    if problems:
        for problem in problems:
            print("  FAIL " + problem)
        return 1
    print("skill OK")
    return 0


def _cmd_demo(args):
    session_path, skill_path = write_demo(args.out)
    print("wrote " + str(session_path))
    print("wrote " + str(skill_path))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agent-skill-distill",
        description="Distill a good agent session into a reusable skill.",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + VERSION
    )
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("distill", help="distill a session transcript into SKILL.md")
    d.add_argument("session")
    d.add_argument("--name", required=True)
    d.add_argument("--student", default="any agent harness")
    d.add_argument("-o", "--output", default="SKILL.md")
    d.set_defaults(func=_cmd_distill)

    v = sub.add_parser(
        "verify", help="check a skill covers the session's decisions, traps and checks"
    )
    v.add_argument("skill")
    v.add_argument("session")
    v.add_argument("--min-score", type=int, default=100)
    v.set_defaults(func=_cmd_verify)

    c = sub.add_parser("check", help="CI gate for a skill file")
    c.add_argument("skill")
    c.set_defaults(func=_cmd_check)

    m = sub.add_parser("demo", help="write a demo session + distilled skill")
    m.add_argument("--out", default="examples/demo")
    m.set_defaults(func=_cmd_demo)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
