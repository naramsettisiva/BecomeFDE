#!/usr/bin/env python3
"""Re-anchor the whole 24-day schedule around where you actually are.

Life happens. You miss a day, a week runs long, a client call eats Tuesday.
Rather than the schedule quietly becoming wrong, tell it where you are and it
recomputes every date from that point — backwards for days already done,
forwards for days to come.

    python scripts/schedule.py                      # interactive
    python scripts/schedule.py --day 5              # "I'm on Day 5 today"
    python scripts/schedule.py --day 5 --date 2026-09-08
    python scripts/schedule.py --start 2026-08-27   # anchor Day 1 instead
    python scripts/schedule.py --day 5 --days mon-fri
    python scripts/schedule.py --day 5 --days all --holidays 2026-09-07

Weekend policy:
    mon-fri   Mon–Fri only                     (default)
    mon-sat   Mon–Sat, Sundays off
    all       every calendar day

Rewrites: 24 lab headers, PROGRESS.md, README.md, learn/README.md,
the four AWS lane files, course_hub.html — then rebuilds fde-bootcamp.html.
Idempotent: it regenerates from the computed schedule rather than patching text.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".schedule.json"

POLICIES = {
    "mon-fri": {5, 6},
    "mon-sat": {6},
    "all": set(),
}

WEEK_THEME = {1: "Foundations", 2: "Agents", 3: "Production", 4: "The craft"}


# ── schedule maths ──────────────────────────────────────────────────────────
def is_working(d: date, skip: set[int], holidays: set[date]) -> bool:
    return d.weekday() not in skip and d not in holidays


def step(d: date, skip: set[int], holidays: set[date], forward: bool = True) -> date:
    delta = timedelta(days=1 if forward else -1)
    d += delta
    while not is_working(d, skip, holidays):
        d += delta
    return d


def build(anchor_day: int, anchor: date, skip: set[int], holidays: set[date]) -> list[date]:
    """24 working dates such that day `anchor_day` falls on `anchor`."""
    if not is_working(anchor, skip, holidays):
        # nudge to the next working day rather than silently scheduling a day off
        anchor = step(anchor - timedelta(days=1), skip, holidays, forward=True)

    dates: dict[int, date] = {anchor_day: anchor}
    d = anchor
    for n in range(anchor_day - 1, 0, -1):
        d = step(d, skip, holidays, forward=False)
        dates[n] = d
    d = anchor
    for n in range(anchor_day + 1, 25):
        d = step(d, skip, holidays, forward=True)
        dates[n] = d
    return [dates[n] for n in range(1, 25)]


# ── file rewriting ──────────────────────────────────────────────────────────
class Rewriter:
    def __init__(self, dates: list[date]) -> None:
        self.d = dates
        self.long = [x.strftime("%a %b %-d, %Y") for x in dates]
        self.short = [x.strftime("%b %-d") for x in dates]
        self.dow = [x.strftime("%a %b %-d") for x in dates]
        self.iso = [x.isoformat() for x in dates]
        self.span = {w: f"{self.short[(w-1)*6]} – {self.short[w*6-1]}" for w in (1, 2, 3, 4)}
        self.changed: set[str] = set()

    def _w(self, p: Path, new: str, old: str) -> None:
        if new != old:
            p.write_text(new, encoding="utf-8")
            self.changed.add(str(p.relative_to(ROOT)))

    def labs(self) -> None:
        for n in range(1, 25):
            p = ROOT / "labs" / f"DAY_{n:02d}.md"
            t = old = p.read_text(encoding="utf-8")
            t = re.sub(
                r"^\*\*\w{3} \w{3} \d{1,2}, \d{4}\*\*( · Week \d)?",
                f"**{self.long[n-1]}** · Week {(n-1)//6+1}",
                t, count=1, flags=re.M,
            )
            self._w(p, t, old)

    def progress(self) -> None:
        p = ROOT / "PROGRESS.md"
        t = old = p.read_text(encoding="utf-8")
        t = re.sub(
            r"^Tick as you go\..*?$(\nRuns .*?$)?",
            f"Tick as you go. Five hours a day, 24 working days.\n"
            f"Runs {self.dow[0]} → {self.dow[-1]}.",
            t, count=1, flags=re.M,
        )

        def line(m: re.Match) -> str:
            n = int(m.group(1))
            return f"- [ ] **Day {n:02d}** · {self.dow[n-1]} · {m.group(3)}"

        t = re.sub(r"^- \[[ x]\] \*\*Day (\d\d)\*\* · ([^·]+) · (.*)$", line, t, flags=re.M)
        for w in (1, 2, 3, 4):
            t = re.sub(
                rf"^## Week {w} — {re.escape(WEEK_THEME[w])} \([^)]*\)$",
                f"## Week {w} — {WEEK_THEME[w]} ({self.span[w]})",
                t, flags=re.M,
            )
        for dayn in (5, 8, 12, 13, 14, 18, 21):
            t = re.sub(rf"^\| \w{{3}} \d{{1,2}} \| {dayn:02d} \|",
                       f"| {self.short[dayn-1]} | {dayn:02d} |", t, flags=re.M)
        self._w(p, t, old)

    def readme(self) -> None:
        p = ROOT / "README.md"
        t = old = p.read_text(encoding="utf-8")
        t = re.sub(r"\*\*Dates:\*\* .*",
                   f"**Dates:** {self.dow[0]} → {self.long[-1]}", t, count=1)
        for w in (1, 2, 3, 4):
            t = re.sub(rf"^\| \*\*{w}\*\* \| [^|]+ \|",
                       f"| **{w}** | {self.span[w]} |", t, flags=re.M)
        self._w(p, t, old)

        q = ROOT / "learn" / "README.md"
        if q.exists():
            s = o2 = q.read_text(encoding="utf-8")
            s = re.sub(r"^The course runs .*$",
                       f"The course runs {self.dow[0]} – {self.long[-1]}.", s, flags=re.M)
            self._w(q, s, o2)

    def aws(self) -> None:
        for w in (1, 2, 3, 4):
            p = ROOT / "labs" / "aws" / f"WEEK_{w}_AWS.md"
            if not p.exists():
                continue
            t = old = p.read_text(encoding="utf-8")
            t = re.sub(rf"^# AWS Lane — Week {w} \([^)]*\)$",
                       f"# AWS Lane — Week {w} ({self.span[w]})", t, count=1, flags=re.M)
            self._w(p, t, old)

    def hub(self) -> None:
        p = ROOT / "course_hub.html"
        if not p.exists():
            return
        t = old = p.read_text(encoding="utf-8")
        arr = ",\n               ".join(
            ", ".join(f'"{self.iso[i]}"' for i in range(s, min(s + 6, 24)))
            for s in range(0, 24, 6)
        )
        t = re.sub(r"var DATES = \[.*?\];", f"var DATES = [{arr}];", t, flags=re.S)
        t = re.sub(r'\{ n:(\d+), w:(\d), date:"[^"]*"',
                   lambda m: f'{{ n:{m.group(1)}, w:{m.group(2)}, date:"{self.dow[int(m.group(1))-1]}"',
                   t)
        for w in (1, 2, 3, 4):
            t = re.sub(rf'(\{{ n: {w}, t: "[^"]*",\s*d: )"[^"]*"',
                       rf'\g<1>"{self.span[w]}"', t)
        t = re.sub(r"(<dt>Starts</dt><dd>)[^<]*", rf"\g<1>{self.dow[0]}", t)
        t = re.sub(r"(<dt>Ends</dt><dd>)[^<]*", rf"\g<1>{self.dow[-1]}", t)
        self._w(p, t, old)

    def builder(self) -> None:
        """Bake the current schedule into the navigator builder.

        Matches the whole function regardless of what its body currently looks
        like — the first version of this matched only the *original* body, so
        after one bake it silently stopped matching and did nothing. Silent
        no-ops are worse than crashes; hence the assertion at the end.
        """
        p = ROOT / "scripts" / "build_navigator.py"
        t = old = p.read_text(encoding="utf-8")
        lit = "[\n        " + ",\n        ".join(f'"{x}"' for x in self.iso) + ",\n    ]"
        new_fn = (
            "def course_dates() -> list[str]:\n"
            '    """Baked by scripts/schedule.py — re-run that to change the schedule."""\n'
            f"    return {lit}\n"
        )
        # from the def line up to the next top-level (column-0) statement
        t, n = re.subn(
            r"^def course_dates\(\) -> list\[str\]:\n(?:[ \t].*\n|\n)*",
            new_fn,
            t,
            count=1,
            flags=re.M,
        )
        if n != 1:
            raise RuntimeError(
                "could not find course_dates() in build_navigator.py — "
                "the bake would have silently done nothing"
            )

        # the sidebar's week headers carry their own date spans
        weeks = "WEEKS = [\n" + "".join(
            f'    ({w}, "{WEEK_THEME[w]}", "{self.span[w]}", range({(w-1)*6+1}, {w*6+1})),\n'
            for w in (1, 2, 3, 4)
        ) + "]\n"
        t, n2 = re.subn(r"^WEEKS = \[\n(?:.*?\n)*?\]\n", weeks, t, count=1, flags=re.M)
        if n2 != 1:
            raise RuntimeError("could not find WEEKS in build_navigator.py")

        t = t.replace(
            "# ── the 24 dates, Sundays excluded ──",
            "# ── the 24 working dates (see scripts/schedule.py) ──",
        )

        if self.iso[0] not in t or self.iso[-1] not in t or self.span[1] not in t:
            raise RuntimeError("bake produced a file missing the new dates")
        self._w(p, t, old)

    def run_all(self) -> None:
        self.labs(); self.progress(); self.readme(); self.aws(); self.hub(); self.builder()


# ── cli ─────────────────────────────────────────────────────────────────────
def ask(prompt: str, default: str) -> str:
    r = input(f"  {prompt} [{default}]: ").strip()
    return r or default


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--day", type=int, help="which day number you are on (1-24)")
    ap.add_argument("--date", help="the date that day falls on (YYYY-MM-DD, default today)")
    ap.add_argument("--start", help="shorthand for --day 1 --date <this>")
    ap.add_argument("--days", choices=list(POLICIES), help="working days (default mon-fri)")
    ap.add_argument("--holidays", default="", help="comma-separated YYYY-MM-DD to skip")
    ap.add_argument("--no-build", action="store_true", help="skip rebuilding fde-bootcamp.html")
    a = ap.parse_args()

    prev = {}
    if STATE.exists():
        try:
            prev = json.loads(STATE.read_text())
        except Exception:
            prev = {}

    if a.start:
        anchor_day, anchor_s = 1, a.start
        policy = a.days or prev.get("policy", "mon-fri")
        hol_s = a.holidays or ",".join(prev.get("holidays", []))
    elif a.day:
        anchor_day = a.day
        anchor_s = a.date or date.today().isoformat()
        policy = a.days or prev.get("policy", "mon-fri")
        hol_s = a.holidays or ",".join(prev.get("holidays", []))
    else:
        print("\n  Re-anchor the schedule around where you actually are.\n")
        anchor_day = int(ask("Which day are you on? (1-24)", str(prev.get("anchor_day", 1))))
        anchor_s = ask("What date is that?", date.today().isoformat())
        policy = ask("Working days? (mon-fri / mon-sat / all)", prev.get("policy", "mon-fri"))
        hol_s = ask("Days to skip entirely? (comma YYYY-MM-DD, blank for none)",
                    ",".join(prev.get("holidays", [])))
        print()

    if not 1 <= anchor_day <= 24:
        print(f"  Day must be 1-24, got {anchor_day}"); return 1
    if policy not in POLICIES:
        print(f"  --days must be one of {list(POLICIES)}"); return 1
    try:
        anchor = date.fromisoformat(anchor_s)
    except ValueError:
        print(f"  Bad date '{anchor_s}' — use YYYY-MM-DD"); return 1

    holidays = set()
    for h in [x.strip() for x in hol_s.split(",") if x.strip()]:
        try:
            holidays.add(date.fromisoformat(h))
        except ValueError:
            print(f"  Bad holiday '{h}' — skipping it")

    dates = build(anchor_day, anchor, POLICIES[policy], holidays)

    print(f"  Anchor:  Day {anchor_day} = {dates[anchor_day-1].strftime('%a %b %-d, %Y')}")
    print(f"  Span:    {dates[0].strftime('%a %b %-d')} → {dates[-1].strftime('%a %b %-d, %Y')}")
    print(f"  Working: {policy}" + (f"  ·  skipping {len(holidays)} holiday(s)" if holidays else ""))
    print()
    for n in (1, 2, 3, 12, 23, 24):
        print(f"    Day {n:2d}  {dates[n-1].strftime('%a %b %-d')}")
    print("     ...")
    print()

    r = Rewriter(dates)
    r.run_all()
    for c in sorted(r.changed):
        print(f"    updated  {c}")
    print(f"\n  {len(r.changed)} file(s) changed")

    STATE.write_text(json.dumps({
        "anchor_day": anchor_day,
        "anchor_date": anchor.isoformat(),
        "policy": policy,
        "holidays": sorted(x.isoformat() for x in holidays),
        "dates": [x.isoformat() for x in dates],
    }, indent=2))
    print(f"    wrote    .schedule.json")

    if not a.no_build:
        print("\n  Rebuilding fde-bootcamp.html …")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_navigator.py")], check=False)

    print("\n  Done. The HTML navigator can also be re-anchored in-page — "
          "click the date range in its sidebar.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
