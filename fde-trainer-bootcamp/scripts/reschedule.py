#!/usr/bin/env python3
"""Re-date the whole course. Weekdays only, starting Thu 27 Aug 2026.

Touches every place a date appears: lab headers, PROGRESS.md, README.md,
the AWS lane week files, course_hub.html, and the navigator builder.
Idempotent — it rewrites from the computed schedule, not by patching text.

    python scripts/reschedule.py
"""

from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

START = date(2026, 8, 27)
SKIP_WEEKDAYS = {5, 6}          # Sat, Sun


def schedule() -> list[date]:
    out, d = [], START
    while len(out) < 24:
        if d.weekday() not in SKIP_WEEKDAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


DATES = schedule()
LONG = [d.strftime("%a %b %-d, %Y") for d in DATES]     # "Thu Aug 27, 2026"
SHORT = [d.strftime("%b %-d") for d in DATES]           # "Aug 27"
ISO = [d.isoformat() for d in DATES]

WEEK_OF = {n: (n - 1) // 6 + 1 for n in range(1, 25)}
WEEK_SPAN = {
    w: f"{SHORT[(w - 1) * 6]} – {SHORT[w * 6 - 1]}" for w in (1, 2, 3, 4)
}
WEEK_THEME = {1: "Foundations", 2: "Agents", 3: "Production", 4: "The craft"}

changed: list[str] = []


def write(p: Path, new: str, old: str) -> None:
    if new != old:
        p.write_text(new, encoding="utf-8")
        changed.append(str(p.relative_to(ROOT)))


# ── 1. lab headers ──────────────────────────────────────────────────────────
def fix_labs() -> None:
    for n in range(1, 25):
        p = ROOT / "labs" / f"DAY_{n:02d}.md"
        t = old = p.read_text(encoding="utf-8")
        # **Tue Aug 25, 2026** · Week 1 · ...
        t = re.sub(
            r"^\*\*\w{3} \w{3} \d{1,2}, 2026\*\*( · Week \d)?",
            f"**{LONG[n-1]}** · Week {WEEK_OF[n]}",
            t,
            count=1,
            flags=re.M,
        )
        write(p, t, old)


# ── 2. PROGRESS.md ──────────────────────────────────────────────────────────
def fix_progress() -> None:
    p = ROOT / "PROGRESS.md"
    t = old = p.read_text(encoding="utf-8")

    t = t.replace(
        "Tick as you go. Five hours a day, 24 days, Sundays off.",
        "Tick as you go. Five hours a day, 24 working days, **weekends off**.\n"
        f"Runs {SHORT[0]} → {SHORT[-1]} 2026.",
    )

    # day lines:  - [ ] **Day 01** · Tue Aug 25 · Title
    def day_line(m: re.Match) -> str:
        n = int(m.group(1))
        return f"- [ ] **Day {n:02d}** · {DATES[n-1].strftime('%a %b %-d')} · {m.group(3)}"

    t = re.sub(r"^- \[ \] \*\*Day (\d\d)\*\* · ([^·]+) · (.*)$", day_line, t, flags=re.M)

    # week headers
    for w in (1, 2, 3, 4):
        t = re.sub(
            rf"^## Week {w} — {re.escape(WEEK_THEME[w])} \([^)]*\)$",
            f"## Week {w} — {WEEK_THEME[w]} ({WEEK_SPAN[w]})",
            t,
            flags=re.M,
        )

    # scorecard history dates -> the day they belong to
    for dayn, note in [(5, "first baseline"), (8, "agentic patterns"), (12, "integrated"),
                       (13, "250-case suite"), (14, "200-doc corpus"),
                       (18, "post-optimisation"), (21, "capstone final")]:
        t = re.sub(
            rf"^\| \w{{3}} \d{{1,2}} \| {dayn:02d} \|",
            f"| {SHORT[dayn-1]} | {dayn:02d} |",
            t,
            flags=re.M,
        )

    write(p, t, old)


# ── 3. README.md ────────────────────────────────────────────────────────────
def fix_readme() -> None:
    p = ROOT / "README.md"
    t = old = p.read_text(encoding="utf-8")

    t = re.sub(
        r"\*\*Dates:\*\* .*",
        f"**Dates:** {DATES[0].strftime('%a %b %-d')} → {DATES[-1].strftime('%a %b %-d, %Y')} "
        f"(weekdays only — weekends off)",
        t,
        count=1,
    )
    for w in (1, 2, 3, 4):
        t = re.sub(
            rf"^\| \*\*{w}\*\* \| [^|]+ \|",
            f"| **{w}** | {WEEK_SPAN[w]} |",
            t,
            flags=re.M,
        )
    write(p, t, old)


# ── 4. AWS lane week files ──────────────────────────────────────────────────
def fix_aws() -> None:
    for w in (1, 2, 3, 4):
        p = ROOT / "labs" / "aws" / f"WEEK_{w}_AWS.md"
        if not p.exists():
            continue
        t = old = p.read_text(encoding="utf-8")
        t = re.sub(
            rf"^# AWS Lane — Week {w} \([^)]*\)$",
            f"# AWS Lane — Week {w} ({WEEK_SPAN[w]})",
            t,
            count=1,
            flags=re.M,
        )
        # per-day headings inside:  ## Day 07 — title · 45 min · ~$0.30
        def day_head(m: re.Match) -> str:
            n = int(m.group(1))
            return f"## Day {n:02d} — {m.group(2)}"

        t = re.sub(r"^## Day (\d\d) — (.*)$", day_head, t, flags=re.M)
        write(p, t, old)


# ── 5. course_hub.html ──────────────────────────────────────────────────────
def fix_hub() -> None:
    p = ROOT / "course_hub.html"
    if not p.exists():
        return
    t = old = p.read_text(encoding="utf-8")

    # the DATES array
    arr = ",\n               ".join(
        ", ".join(f'"{ISO[i]}"' for i in range(s, min(s + 6, 24))) for s in range(0, 24, 6)
    )
    t = re.sub(r"var DATES = \[.*?\];", f"var DATES = [{arr}];", t, flags=re.S)

    # per-day date: fields inside the DAYS array
    def day_date(m: re.Match) -> str:
        n = int(m.group(1))
        return f'{{ n:{n}, w:{m.group(2)}, date:"{DATES[n-1].strftime("%a %b %-d")}"'

    t = re.sub(r'\{ n:(\d+), w:(\d), date:"[^"]*"', day_date, t)

    # week strip metadata
    for w in (1, 2, 3, 4):
        t = re.sub(
            rf'(\{{ n: {w}, t: "[^"]*",\s*d: )"[^"]*"',
            rf'\g<1>"{WEEK_SPAN[w]}"',
            t,
        )

    # header vitals
    t = re.sub(r"(<dt>Starts</dt><dd>)[^<]*", rf"\g<1>{DATES[0].strftime('%a %b %-d')}", t)
    t = re.sub(r"(<dt>Ends</dt><dd>)[^<]*", rf"\g<1>{DATES[-1].strftime('%a %b %-d')}", t)
    t = t.replace("24 days · 120 hours · Sundays off",
                  "24 weekdays · 120 hours · weekends off")

    write(p, t, old)


# ── 6. navigator builder ────────────────────────────────────────────────────
def fix_builder() -> None:
    p = ROOT / "scripts" / "build_navigator.py"
    t = old = p.read_text(encoding="utf-8")
    t = re.sub(
        r"out, d = \[\], date\(\d{4}, \d{1,2}, \d{1,2}\)\n    while len\(out\) < 24:\n"
        r"        if d\.weekday\(\) != 6:",
        "out, d = [], date(2026, 8, 27)\n    while len(out) < 24:\n"
        "        if d.weekday() < 5:                 # Mon-Fri only",
        t,
    )
    t = t.replace(
        '"""Build fde-bootcamp.html',
        '"""Build fde-bootcamp.html',
    )
    write(p, t, old)


def main() -> int:
    print(f"  Start: {LONG[0]}   End: {LONG[-1]}   (weekdays only)\n")
    fix_labs(); fix_progress(); fix_readme(); fix_aws(); fix_hub(); fix_builder()
    for c in sorted(set(changed)):
        print(f"    updated  {c}")
    print(f"\n  {len(set(changed))} file(s) changed")
    print("\n  Now run:  python scripts/build_navigator.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
