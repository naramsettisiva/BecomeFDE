#!/usr/bin/env python3
"""Render learn/_reading_*.json into §7 of every learn module.

Idempotent: the block is delimited by <!--reading:NN--> / <!--/reading-->, so
re-running replaces it rather than stacking copies. Any prose that was already
in §7 is preserved below the block under "Referenced in this module".

    python scripts/inject_reading.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARN = ROOT / "learn"

START = "<!--reading:{n:02d}-->"
END = "<!--/reading-->"

KIND = {"paper": "paper", "docs": "docs", "blog": "essay", "video": "video", "book": "book"}


def load() -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for f in ("_reading_01_08.json", "_reading_09_16.json", "_reading_17_24.json"):
        p = LEARN / f
        if not p.exists():
            sys.exit(f"missing {p}")
        for k, v in json.loads(p.read_text(encoding="utf-8")).items():
            out[int(k)] = v
    missing = [n for n in range(1, 25) if n not in out]
    if missing:
        sys.exit(f"no reading list for days: {missing}")
    return out


def mins(m: int) -> str:
    return f"{m} min" if m < 60 else (f"{m // 60}h" if m % 60 == 0 else f"{m // 60}h{m % 60:02d}")


def split_bullets(body: str) -> list[str]:
    """Split a markdown bullet list into whole bullets (continuation lines attached)."""
    out: list[str] = []
    for line in body.split("\n"):
        if re.match(r"^[-*] ", line):
            out.append(line)
        elif out and line.strip():
            out[-1] += "\n" + line
        elif out and not line.strip():
            pass
    return out


_STOP = {"the", "a", "an", "of", "and", "for", "with", "in", "on", "to", "how", "why", "what"}


def _key(title: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in _STOP and len(w) > 3}


def covered(bullet: str, items: list[dict]) -> bool:
    """True if a legacy bullet is already represented by a curated entry."""
    btext = set(re.findall(r"[a-z0-9]+", bullet.lower()))
    for it in items:
        k = _key(it["title"])
        if not k:
            continue
        if len(k & btext) / len(k) >= 0.6:
            return True
    return False


def render(n: int, items: list[dict]) -> str:
    pick = next((i for i in items if i.get("pick")), items[0])
    rest = [i for i in items if i is not pick]

    L = [START.format(n=n), ""]
    L.append("### If you read one thing this week")
    L.append("")
    L.append(
        f"**[{pick['title']}]({pick['url']})** — {pick['author']} · "
        f"{KIND.get(pick['type'], pick['type'])} · ~{mins(pick['minutes'])}"
    )
    L.append("")
    L.append(pick["why"])
    if rest:
        L.append("")
        L.append("### Then, in the order I'd take them")
        L.append("")
        for it in rest:
            L.append(
                f"- **[{it['title']}]({it['url']})** — {it['author']} · "
                f"{KIND.get(it['type'], it['type'])} · ~{mins(it['minutes'])}  "
            )
            L.append(f"  {it['why']}")
    L.append("")
    L.append(END)
    return "\n".join(L)


def main() -> int:
    reading = load()
    changed = 0

    for n in range(1, 25):
        p = LEARN / f"DAY_{n:02d}_LEARN.md"
        text = p.read_text(encoding="utf-8")
        block = render(n, reading[n])

        s, e = START.format(n=n), END
        if s in text and e in text:
            new = re.sub(
                re.escape(s) + r".*?" + re.escape(e), lambda _: block, text, count=1, flags=re.S
            )
        else:
            # first run: find "## 7. Going deeper ..." and split its body out
            m = re.search(r"^## 7\..*$", text, flags=re.M)
            if not m:
                sys.exit(f"Day {n:02d}: no '## 7.' heading — refusing to guess")
            head_end = m.end()
            # §7 runs to the closing "---" separator before the final "Now go to" line, or EOF
            tail_m = re.search(r"\n---\n", text[head_end:])
            body_end = head_end + tail_m.start() if tail_m else len(text)
            body = text[head_end:body_end].strip()
            rest_of_file = text[body_end:]

            legacy = ""
            kept = [b for b in split_bullets(body) if not covered(b, reading[n])]
            if kept:
                legacy = "\n\n### Also mentioned in this module\n\n" + "\n".join(kept)

            new = (
                text[: m.start()]
                + "## 7. Going deeper\n\n"
                + block
                + legacy
                + "\n"
                + rest_of_file
            )

        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1

    print(f"injected reading lists into {changed} learn modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
