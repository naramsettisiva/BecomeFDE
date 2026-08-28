#!/usr/bin/env python3
"""Build the flashcard decks from each learn module's §6 Self-check.

The self-checks are already question/answer pairs written against the module.
This turns them into a deck per day, which the navigator's study mode and the
0:20 warm-up block both draw from — plus an Anki-importable CSV.

    python scripts/build_flashcards.py

Writes:
    learn/_flashcards.json     the decks (consumed by build_navigator.py)
    learn/FLASHCARDS.csv       Anki / Quizlet import — question, answer, day tag
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARN = ROOT / "learn"


def unwrap(lines: list[str]) -> str:
    """Join a hanging-indented markdown item back into one line."""
    return re.sub(r"\s+", " ", " ".join(x.strip() for x in lines)).strip()


def numbered(block: str) -> dict[int, str]:
    """Parse a markdown ordered list into {n: text}, keeping continuation lines."""
    out: dict[int, str] = {}
    cur: int | None = None
    buf: list[str] = []
    for line in block.split("\n"):
        m = re.match(r"^\s{0,3}(\d+)\.\s+(.*)$", line)
        if m:
            if cur is not None:
                out[cur] = unwrap(buf)
            cur, buf = int(m.group(1)), [m.group(2)]
        elif cur is not None and line.strip() and line.startswith((" ", "\t")):
            buf.append(line)
        elif cur is not None and not line.strip():
            out[cur] = unwrap(buf)
            cur, buf = None, []
    if cur is not None:
        out[cur] = unwrap(buf)
    return out


def section6(md: str) -> str:
    m = re.search(r"^## 6\..*?$(.*?)^## 7\.", md, flags=re.M | re.S)
    if not m:
        raise ValueError("no §6 … §7 span")
    return m.group(1)


def cards_for(n: int) -> list[dict]:
    md = (LEARN / f"DAY_{n:02d}_LEARN.md").read_text(encoding="utf-8")
    body = section6(md)

    det = re.search(r"<details>(.*?)</details>", body, flags=re.S)
    if not det:
        raise ValueError(f"Day {n:02d}: §6 has no <details> answer block")

    q_src = body[: det.start()]
    a_src = re.sub(r"<summary>.*?</summary>", "", det.group(1), flags=re.S)

    qs, as_ = numbered(q_src), numbered(a_src)

    missing = sorted(set(qs) - set(as_))
    orphan = sorted(set(as_) - set(qs))
    if missing or orphan:
        raise ValueError(
            f"Day {n:02d}: question/answer numbers do not line up "
            f"(no answer for {missing}, no question for {orphan})"
        )
    if not qs:
        raise ValueError(f"Day {n:02d}: no questions parsed from §6")

    return [
        {"n": i, "q": qs[i], "a": as_[i], "day": n}
        for i in sorted(qs)
        if qs[i] and as_[i]
    ]


def main() -> int:
    decks: dict[str, list[dict]] = {}
    errors: list[str] = []

    for n in range(1, 25):
        try:
            decks[str(n)] = cards_for(n)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        for e in errors:
            print("  !!", e, file=sys.stderr)
        return 1

    (LEARN / "_flashcards.json").write_text(
        json.dumps(decks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    titles = {}
    for n in range(1, 25):
        first = (ROOT / "labs" / f"DAY_{n:02d}.md").read_text(encoding="utf-8").split("\n")[0]
        titles[n] = re.sub(r"^#\s*Day \d+\s*[—-]\s*", "", first).strip()

    with (LEARN / "FLASHCARDS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["question", "answer", "tags"])
        for n in range(1, 25):
            for c in decks[str(n)]:
                w.writerow([c["q"], c["a"], f"fde day{n:02d}"])

    total = sum(len(v) for v in decks.values())
    lo = min((len(v), k) for k, v in decks.items())
    print(f"  {total} cards across 24 decks (thinnest: day {lo[1]}, {lo[0]} cards)")
    print("  wrote learn/_flashcards.json and learn/FLASHCARDS.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
