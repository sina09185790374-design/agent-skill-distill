# agent-skill-distill

Turn a good agent session into a reusable skill — as a small stdlib-only
Python CLI. Feed it a session transcript (JSONL) and it extracts what made
the session work: the **triggers**, the **steps**, the **decisions**, the
**traps** (each error paired with the fix that followed it) and the
**checks** — then renders them as a `SKILL.md`. `verify` scores whether a
skill still covers every decision, trap and check the session taught, and
names the first divergence. `check` is the CI gate a skill must pass
before it ships. No dependencies, no network, no keys.

**Pattern** (original code; pattern only, learned from today's radar):
sybil-solutions/skill-distill distills a good Claude Code / Codex session
into a skill an open-weight model can follow: the teacher reads the
session, writes the skill, then starts the student on a fresh copy of the
starting state with the original prompt and the skill, compares the
student's output with the reference, finds the first place the student
went wrong, fixes the skill there, and runs again — three trials per
version, checks tested on the reference first, and the skill counts as
done only when a human accepts it. This tool is that idea as a small local
CLI for the *offline half* of the loop: `distill` writes the skill,
`verify` finds the first divergence, `check` gates the skill. Running the
student is deliberately out of scope — hand the skill to whatever harness
you use.

## How it works

1. **Read.** A transcript is JSONL, one event per line:
   `{"turn": 1, "role": "user", "kind": "prompt", "text": "..."}`.
   Roles are `user` | `agent` | `tool`; kinds are `prompt` | `message` |
   `tool_call` | `tool_result` | `decision` | `check` | `error` |
   `fix` | `note`. Bad JSON, unknown kinds and missing fields are rejected
   with the line number.
2. **Distill.** Triggers come from the first user prompt (content words,
   stopwords removed, English + Persian). Steps are the tool calls in
   order, consecutive duplicates removed. Decisions and checks are kept
   as written. Each error pairs with the next fix to become a trap; an
   error with no fix is flagged *unresolved*, never hidden. Long tool
   output (over 200 characters) is never copied — the skill records only
   its shape (line count + first line). Secrets and machine-local paths
   are scrubbed before anything is written.
3. **Verify.** Every decision, trap and check has key words; the skill
   must still contain them. The score is the share covered; the first
   uncovered item is the first divergence — fix the skill there, then run
   again.
4. **Gate.** `check` requires all four sections (Triggers, Steps, Traps,
   Checks), no empty section, no fenced block over 12 lines (embedded
   output smell), no secret-like token, no machine-local path, and at
   least two steps. Exit 1 on any problem.

## Usage

```bash
# Distill a session into a skill
python3 -m agent_skill_distill distill session.jsonl --name coverage-gate \
    --student "omp with deepseek-v4.1-flash" -o SKILL.md

# Does the skill still cover everything the session taught?
python3 -m agent_skill_distill verify SKILL.md session.jsonl
# coverage 100% (5/5)

# CI gate for the skill file
python3 -m agent_skill_distill check SKILL.md
# skill OK

# Demo: a good session (coverage gate) + its distilled skill
python3 -m agent_skill_distill demo --out examples/demo
```

## Rules the skill carries

- The skill teaches steps, decisions, traps and checks. It never contains
  the reference session's finished output — short snippets only.
- Three trials per skill version. One lucky run proves nothing.
- Checks are tested on the reference first. A check that fails on the
  reference is a broken check.
- Fix the skill at the first place the student goes wrong, then run again.
- A human accepts the final skill. The skill counts as done only when
  accepted.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## خلاصه فارسی

«جلسه‌ی خوب را به مهارت تبدیل کن»: این ابزار یک فایل JSONL از جلسه‌ی
موفق یک ایجنت را می‌خواند و از آن یک `SKILL.md` می‌سازد — محرک‌ها،
مراحل، تصمیم‌ها، تله‌ها (هر خطا با اصلاحیه‌ی بعدش) و بررسی‌ها. خروجی
طولانی ابزار هرگز عیناً کپی نمی‌شود (فقط شکل آن ثبت می‌شود) و
توکن‌ها و مسیرهای محلی دستگاه پاک می‌شوند. دستور `verify` می‌سنجد که
مهارت هنوز همه‌ی تصمیم‌ها و تله‌ها را پوشش می‌دهد یا نه و اولین انحراف
را نام می‌برد؛ دستور `check` هم دروازه‌ی CI است: مهارت فقط وقتی منتشر
می‌شود که هر چهار بخش را داشته باشد، بخشی خالی نباشد، بلوک کد طولانی
(خروجی جاسازی‌شده) نداشته باشد و هیچ رازی در آن نباشد. بدون وابستگی،
بدون شبکه، فقط با کتابخانه‌ی استاندارد پایتون.

## License

MIT
