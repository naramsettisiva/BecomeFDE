#!/usr/bin/env python3
"""Build fde-bootcamp.html — the whole course as one self-contained dark-theme page.

Everything is embedded: 24 learn modules, 24 labs, the AWS lane, and the guides.
No server, no internet, no relative paths. Double-click it anywhere.

    python scripts/build_navigator.py
"""

from __future__ import annotations

import html
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fde-bootcamp.html"

MD = markdown.Markdown(
    extensions=["tables", "fenced_code", "attr_list", "sane_lists", "md_in_html", "toc"],
    extension_configs={"toc": {"permalink": False}},
)


def render(path: Path) -> str:
    MD.reset()
    return reading_blocks(MD.convert(path.read_text(encoding="utf-8")))


def reading_blocks(h: str) -> str:
    """Turn the <!--reading:NN--> ... <!--/reading--> markers into a styled section."""
    h = re.sub(r"<!--reading:\d\d-->", '<div class="readinglist">', h)
    return h.replace("<!--/reading-->", "</div>")


CHAPTER_META = json.loads((ROOT / "learn" / "_chapter_meta.json").read_text(encoding="utf-8"))
CARDS = json.loads((ROOT / "learn" / "_flashcards.json").read_text(encoding="utf-8"))

WEEK_OF = {n: (1 if n < 7 else 2 if n < 13 else 3 if n < 19 else 4) for n in range(1, 25)}


def budget_of(md: str) -> str:
    """Pull '1:15' out of the module's 'Budget 1:15.' line."""
    m = re.search(r"Budget\s+(\d:\d\d)", md)
    return m.group(1) if m else "1:15"


def opener(n: int, title: str, md: str) -> str:
    """The chapter opener card: what this is, what it takes, what you'll be able to do."""
    meta = CHAPTER_META[str(n)]
    li = "".join(f"<li>{html.escape(o)}</li>" for o in meta["objectives"])
    terms = "".join(f"<span>{html.escape(t)}</span>" for t in meta["terms"])
    return (
        '<header class="opener">'
        f'<p class="ch">Chapter {n} &middot; Week {WEEK_OF[n]}</p>'
        f'<h1 class="chtitle">{html.escape(title)}</h1>'
        f'<p class="hook">{html.escape(meta["hook"])}</p>'
        '<div class="ometa">'
        f'<div><h4>Reading time</h4><p>{budget_of(md)}, before the lab</p></div>'
        f'<div><h4>You need first</h4><p>{html.escape(meta["needs"])}</p></div>'
        "</div>"
        f'<div class="objectives"><h4>By the end you will be able to</h4><ol>{li}</ol></div>'
        f'<div class="terms"><h4>Key terms</h4><p>{terms}</p></div>'
        "</header>"
    )


def render_learn(n: int) -> str:
    """A learn module, with its H1 + 'read before' line replaced by a chapter opener."""
    md = (ROOT / "learn" / f"DAY_{n:02d}_LEARN.md").read_text(encoding="utf-8")
    MD.reset()
    h = reading_blocks(MD.convert(md))

    title = re.sub(r"^#\s*Day \d+\s*·\s*Learn\s*[—-]\s*", "", md.split("\n")[0]).strip()

    # drop the rendered <h1> and the bold "Read before ..." paragraph and its <hr>
    h2, cut = re.subn(r"^\s*<h1[^>]*>.*?</h1>\s*", "", h, count=1, flags=re.S)
    if cut != 1:
        raise RuntimeError(f"Day {n:02d}: learn module has no leading <h1>")
    h2 = re.sub(r"^\s*<p>\s*<strong>\s*Read before.*?</p>\s*(<hr\s*/?>)?\s*", "", h2, count=1, flags=re.S)
    return opener(n, title, md) + h2


# ── the 24 working dates (see scripts/schedule.py) ──────────────────────────────────────────
def course_dates() -> list[str]:
    """Baked by scripts/schedule.py — re-run that to change the schedule."""
    return [
        "2026-08-27",
        "2026-08-28",
        "2026-08-31",
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
        "2026-09-04",
        "2026-09-07",
        "2026-09-08",
        "2026-09-09",
        "2026-09-10",
        "2026-09-11",
        "2026-09-14",
        "2026-09-15",
        "2026-09-16",
        "2026-09-17",
        "2026-09-18",
        "2026-09-21",
        "2026-09-22",
        "2026-09-23",
        "2026-09-24",
        "2026-09-25",
        "2026-09-28",
        "2026-09-29",
    ]
DATES = course_dates()

DAY_TITLES = {}
for n in range(1, 25):
    first = (ROOT / "labs" / f"DAY_{n:02d}.md").read_text(encoding="utf-8").split("\n")[0]
    DAY_TITLES[n] = re.sub(r"^#\s*Day \d+\s*[—-]\s*", "", first).strip()

WEEKS = [
    (1, "Foundations", "Aug 27 – Sep 3", range(1, 7)),
    (2, "Agents", "Sep 4 – Sep 11", range(7, 13)),
    (3, "Production", "Sep 14 – Sep 21", range(13, 19)),
    (4, "The craft", "Sep 22 – Sep 29", range(19, 25)),
]


def build_docs() -> tuple[dict, list]:
    """docs: id -> {title, kind, html}. nav: ordered sidebar structure."""
    docs, nav = {}, []

    # ---- start here ----
    start = [
        ("readme", "Start here — README", ROOT / "README.md"),
        ("learn-how", "How the learn modules work", ROOT / "learn" / "README.md"),
        ("git", "Git Field Guide", ROOT / "GIT_GUIDE.md"),
        ("progress", "Progress tracker", ROOT / "PROGRESS.md"),
    ]
    items = []
    for did, title, p in start:
        if p.exists():
            docs[did] = {"title": title, "kind": "guide", "html": render(p)}
            items.append({"id": did, "label": title})
    nav.append({"section": "Start here", "items": items})

    # ---- the 24 days ----
    for wk, theme, span, days in WEEKS:
        items = []
        for n in days:
            lid, bid = f"learn-{n}", f"lab-{n}"
            docs[lid] = {
                "title": f"Day {n:02d} · Learn — {DAY_TITLES[n]}",
                "kind": "learn",
                "html": render_learn(n),
            }
            docs[bid] = {
                "title": f"Day {n:02d} · Lab — {DAY_TITLES[n]}",
                "kind": "lab",
                "html": render(ROOT / "labs" / f"DAY_{n:02d}.md"),
            }
            items.append(
                {
                    "day": n,
                    "date": DATES[n - 1],
                    "title": DAY_TITLES[n],
                    "learn": lid,
                    "lab": bid,
                }
            )
        nav.append({"section": f"Week {wk} — {theme}", "sub": span, "days": items})

    # ---- aws lane ----
    aws_order = [
        ("aws-lane", "The AWS lane — read first", "AWS_LANE.md"),
        ("aws-setup", "AWS setup (macOS)", "AWS_SETUP.md"),
        ("aws-cost", "Cost discipline", "AWS_COST_DISCIPLINE.md"),
        ("aws-w1", "Week 1 — Bedrock, S3 Vectors, KB", "WEEK_1_AWS.md"),
        ("aws-w2", "Week 2 — AgentCore, MCP on Lambda", "WEEK_2_AWS.md"),
        ("aws-w3", "Week 3 — Guardrails, serving, GPU", "WEEK_3_AWS.md"),
        ("aws-w4", "Week 4 — Discovery, capstone, teardown", "WEEK_4_AWS.md"),
    ]
    items = []
    for did, title, fname in aws_order:
        p = ROOT / "labs" / "aws" / fname
        if p.exists():
            docs[did] = {"title": title, "kind": "aws", "html": render(p)}
            items.append({"id": did, "label": title})
    nav.append({"section": "AWS lane", "items": items})

    return docs, nav


def js_json(obj) -> str:
    """JSON safe to embed inside a <script> tag."""
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


TEMPLATE = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FDE Trainer Bootcamp</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;0,7..72,600;0,7..72,700;1,7..72,400;1,7..72,600&display=swap">
<style>
__CSS__
</style>
</head>
<body>
__BODY__
<script id="course-data" type="application/json">__DATA__</script>
<script>
__JS__
</script>
</body>
</html>
"""

CSS = r"""
/* Dark by design — not an inverted light theme. Slate ground, amber signal:
   the palette of freight signage, which is what this course is about. */
:root{
  --ground:#0B1014; --surface:#121A21; --surface-2:#18222B; --surface-3:#1E2A35;
  --rail:#26333F; --rail-soft:#1C2731;
  --ink:#E9EEF3; --ink-2:#AFBCC8; --ink-3:#78889A;
  --signal:#F0A93B; --signal-2:#F5C170; --signal-wash:#221A0B;
  --learn:#7FA8D4; --learn-wash:#111B26;
  --lab:#E0A24E;
  --aws:#8FD4B4;
  --good:#4FBF93; --crit:#E0736D;
  --f-display:"Archivo","Helvetica Neue",Arial,sans-serif;
  --f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --f-read:"Literata",Charter,"Bitstream Charter","Sitka Text",Cambria,Georgia,serif;
  --f-mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --rail-w:320px;
  --toc-w:230px;
  /* reading scale — the S/M/L control writes the -base vars */
  --read-base:18px;
  --measure-base:66ch;
  --read:var(--read-base);
  --measure:var(--measure-base);
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;background:var(--ground);color:var(--ink);
  font-family:var(--f-body);font-size:15.5px;line-height:1.62;
  -webkit-font-smoothing:antialiased;display:flex;
}
::selection{background:var(--signal);color:#12161B}

/* ── sidebar ───────────────────────────────────────────── */
#rail{
  width:var(--rail-w);flex:0 0 var(--rail-w);height:100vh;overflow-y:auto;
  background:var(--surface);border-right:1px solid var(--rail);
  display:flex;flex-direction:column;
}
#rail::-webkit-scrollbar{width:9px}
#rail::-webkit-scrollbar-thumb{background:var(--rail);border-radius:5px}
#rail::-webkit-scrollbar-track{background:transparent}

.brand{padding:18px 18px 14px;border-bottom:1px solid var(--rail)}
.brand h1{
  font-family:var(--f-display);font-size:1.02rem;font-weight:700;margin:0 0 3px;
  letter-spacing:-.01em;
}
.brand .sub{
  font-family:var(--f-mono);font-size:10px;color:var(--ink-3);letter-spacing:.1em;
  text-transform:uppercase;background:none;border:0;padding:0;cursor:pointer;text-align:left;
}
.brand .sub:hover{color:var(--signal)}
.brand .sub::after{content:" ✎";opacity:.55}

/* ── reschedule panel ──────────────────────────────────── */
.sched{padding:14px 16px;border-bottom:1px solid var(--rail);background:var(--surface-2)}
.sched[hidden]{display:none}
.sched h2{
  font-family:var(--f-mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--signal);margin:0 0 10px;
}
.sched label{display:block;font-size:.76rem;color:var(--ink-3);margin:0 0 4px}
.sched .row{margin-bottom:11px}
.sched select,.sched input[type=date]{
  width:100%;background:var(--surface-3);border:1px solid var(--rail);color:var(--ink);
  font-family:var(--f-body);font-size:.83rem;padding:6px 8px;border-radius:3px;outline:none;
}
.sched select:focus,.sched input:focus{border-color:var(--signal)}
.sched .btns{display:flex;gap:7px;margin-top:13px}
.sched button{
  font-family:var(--f-mono);font-size:10px;letter-spacing:.07em;text-transform:uppercase;
  padding:7px 11px;border-radius:3px;cursor:pointer;border:1px solid var(--rail);
  background:none;color:var(--ink-3);
}
.sched button.go{background:var(--signal);color:#12161B;border-color:var(--signal);font-weight:600}
.sched button:hover{color:var(--ink)}
.sched button.go:hover{color:#12161B;opacity:.9}
.sched .preview{
  font-family:var(--f-mono);font-size:9.5px;color:var(--ink-3);margin-top:11px;
  line-height:1.7;border-top:1px solid var(--rail);padding-top:9px;
}
.sched .preview b{color:var(--signal-2);font-weight:500}

.searchbox{padding:12px 14px;border-bottom:1px solid var(--rail);position:sticky;top:0;background:var(--surface);z-index:5}
.searchbox input{
  width:100%;background:var(--surface-2);border:1px solid var(--rail);color:var(--ink);
  font-family:var(--f-body);font-size:.86rem;padding:8px 11px;border-radius:4px;outline:none;
}
.searchbox input:focus{border-color:var(--signal)}
.searchbox input::placeholder{color:var(--ink-3)}
.searchmeta{font-family:var(--f-mono);font-size:9.5px;color:var(--ink-3);margin-top:6px;letter-spacing:.05em}

.progwrap{padding:11px 14px;border-bottom:1px solid var(--rail)}
.progbar{height:5px;background:var(--surface-3);border-radius:3px;overflow:hidden}
.progfill{height:100%;width:0;background:var(--signal);transition:width .3s}
.progtxt{font-family:var(--f-mono);font-size:9.5px;color:var(--ink-3);margin-top:6px;display:flex;justify-content:space-between}
.progtxt button{background:none;border:0;color:var(--ink-3);font-family:var(--f-mono);font-size:9.5px;cursor:pointer;padding:0}
.progtxt button:hover{color:var(--signal)}

nav{padding:8px 0 40px;flex:1}
.sec{
  font-family:var(--f-mono);font-size:9.5px;letter-spacing:.15em;text-transform:uppercase;
  color:var(--ink-3);padding:16px 18px 7px;
}
.sec.wk{color:var(--signal);display:flex;justify-content:space-between;align-items:baseline}
.sec.wk em{font-style:normal;color:var(--ink-3);letter-spacing:.05em;font-size:9px}

a.item{
  display:block;padding:6px 18px;color:var(--ink-2);text-decoration:none;font-size:.86rem;
  border-left:2px solid transparent;
}
a.item:hover{background:var(--surface-2);color:var(--ink)}
a.item.on{background:var(--surface-3);color:var(--ink);border-left-color:var(--signal)}

.day{border-left:2px solid transparent}
.day.today{border-left-color:var(--signal);background:var(--signal-wash)}
.dayhead{
  display:flex;gap:9px;align-items:center;padding:7px 18px 3px;cursor:pointer;user-select:none;
}
.dayhead:hover{background:var(--surface-2)}
.dayno{
  font-family:var(--f-mono);font-size:10.5px;color:var(--ink-3);width:20px;flex:0 0 20px;
  font-variant-numeric:tabular-nums;
}
.day.today .dayno{color:var(--signal)}
.daytitle{font-size:.85rem;color:var(--ink-2);line-height:1.35;flex:1;min-width:0}
.day.done .daytitle{color:var(--ink-3);text-decoration:line-through;text-decoration-thickness:1px}
.daydate{font-family:var(--f-mono);font-size:9px;color:var(--ink-3);flex:0 0 auto}

.daylinks{display:flex;gap:6px;padding:2px 18px 8px 47px}
.daylinks a{
  font-family:var(--f-mono);font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;
  text-decoration:none;padding:3px 8px;border-radius:3px;border:1px solid var(--rail);
  color:var(--ink-3);
}
.daylinks a.l{border-color:#2C4257;color:var(--learn)}
.daylinks a.b{border-color:#4A3A1C;color:var(--lab)}
.daylinks a:hover{background:var(--surface-3);color:var(--ink)}
.daylinks a.on{background:var(--surface-3);color:var(--ink);border-color:var(--signal)}
.daylinks .tick{margin-left:auto;display:flex;align-items:center;gap:5px;font-family:var(--f-mono);font-size:9px;color:var(--ink-3);cursor:pointer}
.daylinks .tick input{accent-color:var(--signal);width:13px;height:13px;cursor:pointer}

/* ── main pane ─────────────────────────────────────────── */
#main{flex:1;height:100vh;overflow-y:auto;scroll-behavior:smooth}
#main::-webkit-scrollbar{width:11px}
#main::-webkit-scrollbar-thumb{background:var(--rail);border-radius:6px}
.pane{max-width:1210px;margin:0 auto;padding:38px 44px 160px 76px;display:grid;
  grid-template-columns:minmax(0,1fr) var(--toc-w);column-gap:52px;align-items:start}
.pane>.crumb,.pane>.jump,.pane>.doc{grid-column:1}
.pane>.tocrail{grid-column:2;grid-row:1 / span 99}
body.notoc .pane{grid-template-columns:minmax(0,1fr);max-width:940px;padding-left:44px}

/* reading progress — a hairline, not a chrome bar */
#readbar{position:fixed;top:0;left:var(--rail-w);right:0;height:2px;z-index:30;
  background:transparent;pointer-events:none}
#readbar i{display:block;height:100%;width:0;background:var(--signal);opacity:.85}

.crumb{
  font-family:var(--f-mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;
  margin:0 0 16px;display:flex;gap:10px;align-items:center;
}
.crumb .k{padding:2px 8px;border-radius:3px;border:1px solid var(--rail)}
.crumb .k.learn{color:var(--learn);border-color:#2C4257}
.crumb .k.lab{color:var(--lab);border-color:#4A3A1C}
.crumb .k.aws{color:var(--aws);border-color:#245040}
.crumb .k.guide{color:var(--ink-3)}
.crumb .d{color:var(--ink-3)}

.jump{
  display:flex;gap:8px;margin:0 0 30px;padding-bottom:22px;border-bottom:1px solid var(--rail-soft);
  flex-wrap:wrap;
}
.jump a,.jump button{
  font-family:var(--f-mono);font-size:10px;letter-spacing:.07em;text-transform:uppercase;
  text-decoration:none;padding:6px 11px;border-radius:3px;border:1px solid var(--rail);
  color:var(--ink-3);background:none;cursor:pointer;
}
.jump a:hover,.jump button:hover{color:var(--ink);border-color:var(--ink-3)}
.jump a.pri{border-color:var(--signal);color:var(--signal)}

/* ── the page: set like a book, not like a README ───────── */
.doc{
  font-family:var(--f-read);font-size:var(--read);line-height:1.75;
  color:#DCE4EC;font-variant-numeric:oldstyle-nums proportional-nums;
  text-rendering:optimizeLegibility;
}
.doc h1{
  font-family:var(--f-display);font-weight:700;font-size:2.1em;line-height:1.08;
  letter-spacing:-.025em;margin:0 0 .5em;text-wrap:balance;color:var(--ink);
}
/* numbered sections get the numeral hung in the margin, book-style */
.doc h2{
  font-family:var(--f-display);font-weight:700;font-size:1.42em;letter-spacing:-.018em;
  line-height:1.22;margin:2.4em 0 .5em;color:var(--ink);position:relative;text-wrap:balance;
}
.doc h2 .secno{
  font-family:var(--f-mono);font-size:.55em;font-weight:500;color:var(--signal);
  letter-spacing:.06em;display:block;margin-bottom:.5em;
}
@media (min-width:1100px){
  .doc h2 .secno{position:absolute;left:-2.9em;top:.62em;margin:0;text-align:right;width:2.2em}
}
.doc h3{
  font-family:var(--f-display);font-weight:600;font-size:1.09em;margin:2em 0 .45em;
  letter-spacing:-.008em;color:var(--ink);line-height:1.3;
}
.doc h4{font-family:var(--f-display);font-weight:600;font-size:.97em;margin:1.5em 0 .35em;color:var(--ink)}
.doc p{margin:0 0 1.05em;max-width:var(--measure)}
/* the opening paragraph of a section reads as a lede */
.doc h2 + p{font-size:1.06em;line-height:1.68;color:#E6ECF2}
.doc ul,.doc ol{margin:0 0 1.1em;padding-left:1.5em;max-width:var(--measure)}
.doc li{margin-bottom:.4em;padding-left:.15em}
.doc li::marker{color:var(--ink-3)}
.doc li>ul,.doc li>ol{margin-top:.4em;margin-bottom:.4em}
.doc strong{color:#FFF;font-weight:600}
.doc em{color:var(--ink)}
.doc a{color:var(--signal-2);text-decoration:none;border-bottom:1px solid rgba(240,169,59,.32)}
.doc a:hover{border-bottom-color:var(--signal)}
.doc hr{border:0;border-top:1px solid var(--rail-soft);margin:2.4em 0;max-width:var(--measure)}
/* an <hr> immediately before a heading is a markdown separator, not a rule — hide it */
.doc hr + h2{margin-top:0}

/* quotations: the default is a quiet indent, not a coloured box */
.doc blockquote{
  margin:0 0 1.2em;padding:.1em 0 .1em 1.4em;max-width:var(--measure);
  border-left:2px solid var(--rail);color:var(--ink-2);font-style:italic;
}
.doc blockquote p:last-child{margin-bottom:0}
.doc blockquote strong{color:var(--signal-2);font-style:normal}

/* a one-line bolded aphorism becomes a pull quote */
.doc blockquote.pull{
  border-left:0;padding:.7em 0 .8em;margin:1.9em 0;font-style:normal;
  border-top:1px solid var(--rail);border-bottom:1px solid var(--rail);
}
.doc blockquote.pull p{
  font-size:1.24em;line-height:1.45;color:var(--signal-2);font-weight:600;
  letter-spacing:-.012em;text-wrap:balance;margin:0;
}
.doc blockquote.pull strong{color:inherit;font-weight:inherit}

/* Setup. / Scenario. / Task. — the framed premise of a worked example */
.doc blockquote.setup{
  border-left:0;background:var(--surface-2);border:1px solid var(--rail);
  border-radius:4px;padding:.85em 1.15em;font-style:normal;color:var(--ink-2);
}
.doc blockquote.setup>p:first-child>strong:first-child{
  font-family:var(--f-mono);font-size:.72em;letter-spacing:.12em;text-transform:uppercase;
  color:var(--signal);display:block;margin-bottom:.45em;
}

.doc code{
  font-family:var(--f-mono);font-size:.85em;background:var(--surface-3);
  padding:1.5px 5px;border-radius:3px;color:var(--signal-2);
  border:1px solid var(--rail-soft);
}
.doc pre{
  background:var(--surface-2);border:1px solid var(--rail);border-left:3px solid var(--signal);
  border-radius:0 4px 4px 0;padding:15px 17px;overflow-x:auto;margin:0 0 1.3em;position:relative;
}
.doc pre code{
  background:none;border:0;padding:0;color:var(--ink-2);
  font-size:.8em;line-height:1.7;display:block;
}
.doc pre::-webkit-scrollbar{height:8px}
.doc pre::-webkit-scrollbar-thumb{background:var(--rail);border-radius:4px}
.copybtn{
  position:absolute;top:7px;right:7px;font-family:var(--f-mono);font-size:9px;
  letter-spacing:.08em;text-transform:uppercase;background:var(--surface-3);
  border:1px solid var(--rail);color:var(--ink-3);padding:3px 7px;border-radius:3px;cursor:pointer;
  opacity:0;transition:opacity .15s;
}
.doc pre:hover .copybtn{opacity:1}
.copybtn:hover{color:var(--ink)}
.copybtn.done{color:var(--good);border-color:var(--good);opacity:1}

.tablewrap{overflow-x:auto;margin:0 0 1.5em;border:1px solid var(--rail);border-radius:4px}
.doc table{border-collapse:collapse;width:100%;font-family:var(--f-body);font-size:.86em;min-width:440px;line-height:1.55}
.doc th,.doc td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--rail-soft);vertical-align:top}
.doc thead th{
  font-family:var(--f-mono);font-size:10px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--ink-3);background:var(--surface-2);border-bottom:1px solid var(--rail);white-space:nowrap;
}
.doc tbody tr:last-child td{border-bottom:0}
.doc tbody tr:hover{background:var(--surface-2)}

.doc details{
  margin:0 0 1.3em;border:1px solid var(--rail);border-radius:4px;background:var(--surface-2);
  overflow:hidden;
}
.doc details summary{
  cursor:pointer;padding:13px 17px;font-family:var(--f-display);font-weight:600;font-size:.95em;
  color:var(--signal-2);list-style:none;user-select:none;
}
.doc details summary::-webkit-details-marker{display:none}
.doc details summary::before{content:"▸ ";color:var(--ink-3)}
.doc details[open] summary::before{content:"▾ "}
.doc details summary:hover{background:var(--surface-3)}
.doc details[open]{background:var(--surface)}
.doc details>*:not(summary){padding-left:17px;padding-right:17px}
.doc details>*:not(summary){max-width:none}
.doc details>*:last-child{padding-bottom:14px}

.doc input[type=checkbox]{accent-color:var(--signal);margin-right:6px}

mark{background:rgba(240,169,59,.28);color:var(--ink);border-radius:2px;padding:0 2px}

.doc .dateline{
  font-family:var(--f-body);font-size:.85em;line-height:1.6;color:var(--ink-3);
  margin:-.3em 0 1.4em;padding-bottom:1.1em;border-bottom:1px solid var(--rail-soft);
}
.doc .dateline strong{color:var(--ink-2);font-weight:600}

/* ── chapter opener ────────────────────────────────────── */
.doc .opener{margin:0 0 2.6em;padding:0 0 1.9em;border-bottom:1px solid var(--rail);max-width:var(--measure)}
.doc .opener .ch{
  font-family:var(--f-mono);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--signal);margin:0 0 .9em;
}
.doc .opener .chtitle{
  font-family:var(--f-display);font-weight:700;font-size:2.15em;line-height:1.06;
  letter-spacing:-.03em;margin:0 0 .5em;text-wrap:balance;color:var(--ink);
}
.doc .opener .hook{
  font-size:1.16em;line-height:1.6;color:var(--ink-2);font-style:italic;
  margin:0 0 1.5em;max-width:58ch;
}
.doc .opener h4{
  font-family:var(--f-mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 .55em;font-weight:500;
}
.doc .opener .ometa{display:flex;gap:34px;flex-wrap:wrap;margin:0 0 1.6em}
.doc .opener .ometa>div{flex:1 1 210px;min-width:0}
.doc .opener .ometa p{margin:0;font-size:.9em;color:var(--ink-2);line-height:1.55;max-width:none}
.doc .opener .objectives{
  background:var(--learn-wash);border:1px solid #22344A;border-radius:5px;
  padding:16px 20px 14px;margin:0 0 1.3em;
}
.doc .opener .objectives h4{color:var(--learn)}
.doc .opener .objectives ol{margin:0;padding-left:1.35em;max-width:none}
.doc .opener .objectives li{font-size:.94em;line-height:1.55;margin-bottom:.42em;color:var(--ink-2)}
.doc .opener .objectives li::marker{color:var(--learn)}
.doc .opener .terms p{margin:0;display:flex;flex-wrap:wrap;gap:6px;max-width:none}
.doc .opener .terms span{
  font-family:var(--f-mono);font-size:11px;letter-spacing:.02em;color:var(--ink-2);
  background:var(--surface-2);border:1px solid var(--rail);border-radius:3px;padding:3px 8px;
}

/* ── section colouring: the seven parts read differently ── */
.doc .sec-3{--acc:var(--signal)}      /* worked example */
.doc .sec-4{--acc:var(--crit)}        /* what people get wrong */
.doc .sec-5{--acc:var(--good)}        /* the trainer's angle */
.doc .sec-6{--acc:var(--learn)}       /* self-check */
.doc .sec-3 h2 .secno,.doc .sec-4 h2 .secno,
.doc .sec-5 h2 .secno,.doc .sec-6 h2 .secno{color:var(--acc)}
.doc .sec-3 h2::after,.doc .sec-4 h2::after,
.doc .sec-5 h2::after,.doc .sec-6 h2::after{
  content:"";display:block;width:38px;height:2px;background:var(--acc);
  margin-top:.55em;opacity:.8;
}
/* §3 is a worked example — frame it like one */
.doc .sec-3{
  background:var(--surface);border:1px solid var(--rail);border-radius:6px;
  padding:2px 26px 20px;margin:2.6em 0;
}
.doc .sec-3 h2{margin-top:1.2em}
.doc .sec-3 h2 .secno{position:static;display:block;margin-bottom:.5em;width:auto;text-align:left}

/* ── reading list ──────────────────────────────────────── */
.doc .readinglist{margin:1.2em 0 1.6em;max-width:var(--measure)}
.doc .readinglist h3{
  font-family:var(--f-mono);font-size:10px;letter-spacing:.15em;text-transform:uppercase;
  color:var(--ink-3);margin:1.9em 0 .9em;font-weight:500;
}
.doc .readinglist h3:first-child{margin-top:.6em}
.doc .readinglist>p{
  background:var(--signal-wash);border:1px solid #3A2C11;border-left:3px solid var(--signal);
  border-radius:0 5px 5px 0;padding:14px 18px;margin:0 0 .5em;font-size:.97em;max-width:none;
}
.doc .readinglist>p + p{
  background:none;border:0;border-left:3px solid transparent;padding:0 18px 0 21px;
  color:var(--ink-2);font-size:.94em;margin-bottom:1.2em;
}
.doc .readinglist ul{list-style:none;padding:0;max-width:none}
.doc .readinglist li{
  margin:0 0 .85em;padding:0 0 .85em 0;border-bottom:1px solid var(--rail-soft);
  font-size:.94em;line-height:1.6;color:var(--ink-2);
}
.doc .readinglist li:last-child{border-bottom:0}
.doc .readinglist li strong{display:block;margin-bottom:.15em}

/* ── table of contents rail ────────────────────────────── */
.tocrail{position:sticky;top:26px;max-height:calc(100vh - 60px);overflow-y:auto;
  padding:2px 0 30px;font-family:var(--f-body)}
.tocrail::-webkit-scrollbar{width:6px}
.tocrail::-webkit-scrollbar-thumb{background:var(--rail);border-radius:3px}
.tocrail h5{
  font-family:var(--f-mono);font-size:9px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 11px;font-weight:500;
}
.tocrail a{
  display:block;font-size:12.5px;line-height:1.4;color:var(--ink-3);text-decoration:none;
  padding:4px 0 4px 12px;border-left:2px solid var(--rail-soft);
}
.tocrail a.l3{padding-left:22px;font-size:11.5px;color:#61707F}
.tocrail a:hover{color:var(--ink)}
.tocrail a.on{color:var(--signal);border-left-color:var(--signal)}
.tocrail .sizer{display:flex;gap:5px;margin:16px 0 0;padding-top:14px;border-top:1px solid var(--rail)}
.tocrail .sizer button{
  font-family:var(--f-mono);font-size:10px;background:none;border:1px solid var(--rail);
  color:var(--ink-3);border-radius:3px;padding:4px 8px;cursor:pointer;flex:1;
}
.tocrail .sizer button:hover{color:var(--ink);border-color:var(--ink-3)}
.tocrail .sizer button.on{color:var(--signal);border-color:var(--signal)}

/* ── flashcards ────────────────────────────────────────── */
.warmup{padding:0 14px 12px}
.warmup a{
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  font-family:var(--f-mono);font-size:10px;letter-spacing:.09em;text-transform:uppercase;
  text-decoration:none;color:var(--ink-3);border:1px solid var(--rail);border-radius:3px;
  padding:7px 10px;
}
.warmup a:hover{color:var(--signal);border-color:var(--signal)}
.warmup a em{font-style:normal;color:var(--signal);letter-spacing:.04em}
.warmup a em:empty{display:none}

.study{max-width:720px;margin:0 auto}
.study .shead{
  display:flex;align-items:baseline;justify-content:space-between;gap:14px;flex-wrap:wrap;
  border-bottom:1px solid var(--rail);padding-bottom:16px;margin-bottom:30px;
}
.study .shead h2{
  font-family:var(--f-display);font-weight:700;font-size:1.5rem;letter-spacing:-.02em;margin:0;
}
.study .shead .count{font-family:var(--f-mono);font-size:11px;color:var(--ink-3);letter-spacing:.08em}
.study .srcbar{height:3px;background:var(--surface-3);border-radius:2px;margin-bottom:34px;overflow:hidden}
.study .srcbar i{display:block;height:100%;width:0;background:var(--signal);transition:width .25s}

.card{
  background:var(--surface);border:1px solid var(--rail);border-radius:8px;
  padding:38px 40px;min-height:260px;display:flex;flex-direction:column;justify-content:center;
}
.card .qq{
  font-family:var(--f-read);font-size:1.32rem;line-height:1.5;color:var(--ink);
  text-wrap:balance;margin:0;
}
.card .aa{
  font-family:var(--f-read);font-size:1.02rem;line-height:1.68;color:var(--ink-2);
  margin:26px 0 0;padding-top:24px;border-top:1px solid var(--rail);
}
.card .aa code,.card .qq code{
  font-family:var(--f-mono);font-size:.85em;background:var(--surface-3);padding:1.5px 5px;
  border-radius:3px;color:var(--signal-2);border:1px solid var(--rail-soft);
}
.card .src{
  font-family:var(--f-mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 18px;
}
.study .acts{display:flex;gap:10px;margin-top:22px;flex-wrap:wrap}
.study .acts button{
  font-family:var(--f-mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  padding:11px 20px;border-radius:4px;cursor:pointer;border:1px solid var(--rail);
  background:none;color:var(--ink-2);flex:1;min-width:130px;
}
.study .acts button:hover{color:var(--ink);border-color:var(--ink-3)}
.study .acts button.flip{background:var(--signal);color:#12161B;border-color:var(--signal);font-weight:600}
.study .acts button.again{border-color:#5A2F2C;color:var(--crit)}
.study .acts button.again:hover{background:#231716}
.study .acts button.good{border-color:#1F4E3D;color:var(--good)}
.study .acts button.good:hover{background:#14231E}
.study .keys{
  font-family:var(--f-mono);font-size:9.5px;letter-spacing:.09em;color:var(--ink-3);
  margin-top:18px;text-align:center;
}
.study .done{text-align:center;padding:50px 20px}
.study .done h3{font-family:var(--f-display);font-size:1.5rem;margin:0 0 12px;color:var(--signal)}
.study .done p{font-family:var(--f-read);color:var(--ink-2);margin:0 0 22px;font-size:1.02rem}
.study .done .tally{
  font-family:var(--f-mono);font-size:11px;color:var(--ink-3);letter-spacing:.06em;
  margin-bottom:26px;line-height:1.9;
}
.study .done a,.study .done button{
  font-family:var(--f-mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  text-decoration:none;padding:10px 18px;border-radius:4px;border:1px solid var(--rail);
  color:var(--ink-2);background:none;cursor:pointer;margin:0 5px;display:inline-block;
}
.study .done a:hover,.study .done button:hover{color:var(--ink);border-color:var(--ink-3)}

/* ── search results ────────────────────────────────────── */
.hits{max-width:820px}
.hit{
  display:block;padding:14px 16px;margin-bottom:9px;background:var(--surface);
  border:1px solid var(--rail);border-radius:4px;text-decoration:none;color:inherit;
}
.hit:hover{border-color:var(--signal)}
.hit .t{font-family:var(--f-display);font-weight:600;font-size:.95rem;color:var(--ink);margin-bottom:4px}
.hit .s{font-size:.82rem;color:var(--ink-3);line-height:1.5}

/* ── responsive ────────────────────────────────────────── */
.railtoggle{
  display:none;position:fixed;bottom:18px;right:18px;z-index:50;
  background:var(--signal);color:#12161B;border:0;border-radius:50%;
  width:50px;height:50px;font-size:20px;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.5);
}
@media (max-width:1240px){
  .pane{grid-template-columns:minmax(0,1fr);max-width:900px}
  .tocrail{display:none}
}
@media (max-width:940px){
  #rail{position:fixed;left:0;top:0;z-index:40;transform:translateX(-100%);transition:transform .22s}
  body.railopen #rail{transform:none}
  .railtoggle{display:block}
  #readbar{left:0}
  .pane{padding:26px 20px 120px}
  .doc h2 .secno{position:static}
  :root{--read:min(var(--read-base),17px);--measure:100%}
  .doc .opener .chtitle{font-size:1.72em}
  .doc .sec-3{padding:2px 16px 14px;margin-left:-4px;margin-right:-4px}
}
@media print{
  #rail,.railtoggle,.jump,.copybtn,.tocrail,#readbar{display:none}
  body{display:block;background:#fff;color:#000}
  .pane{max-width:none;padding:0;display:block}
  .doc{color:#000;font-size:11pt}
  .doc a{color:#000}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function(){
"use strict";
var D = JSON.parse(document.getElementById('course-data').textContent);
var DOCS = D.docs, NAV = D.nav;
var BAKED = D.dates.slice();          // the schedule shipped in the file
var DATES = BAKED.slice();            // the live one — may be re-anchored below
var KEY = 'fde-nav-v1', SKEY = 'fde-sched-v1';
var state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch(e){ state = {}; }
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(state)); }catch(e){} }

/* ── schedule maths ─────────────────────────────────────────
   Life happens: you miss a day, a client call eats Tuesday. Rather than the
   dates quietly going wrong, you tell it which day you're actually on and it
   recomputes all 24 — backwards for what's done, forwards for what's left. */
var SKIP = { 'mon-fri': [0,6], 'mon-sat': [0], 'all': [] };   // JS: 0=Sun, 6=Sat

function iso(d){
  return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0')
       + '-' + String(d.getDate()).padStart(2,'0');
}
function parseISO(s){ var p = s.split('-'); return new Date(+p[0], +p[1]-1, +p[2]); }
function isWorking(d, skip){ return skip.indexOf(d.getDay()) === -1; }
function stepDay(d, skip, fwd){
  var n = new Date(d);
  do { n.setDate(n.getDate() + (fwd ? 1 : -1)); } while (!isWorking(n, skip));
  return n;
}
function computeDates(anchorDay, anchorISO, policy){
  var skip = SKIP[policy] || SKIP['mon-fri'];
  var a = parseISO(anchorISO);
  if (!isWorking(a, skip)) { a.setDate(a.getDate()-1); a = stepDay(a, skip, true); }
  var out = new Array(24);
  out[anchorDay-1] = iso(a);
  var d = new Date(a);
  for (var n = anchorDay-1; n >= 1; n--){ d = stepDay(d, skip, false); out[n-1] = iso(d); }
  d = new Date(a);
  for (var m = anchorDay+1; m <= 24; m++){ d = stepDay(d, skip, true); out[m-1] = iso(d); }
  return out;
}

var sched = null;
try { sched = JSON.parse(localStorage.getItem(SKEY) || 'null'); } catch(e){ sched = null; }
if (sched && sched.anchorDay && sched.anchorDate){
  try { DATES = computeDates(sched.anchorDay, sched.anchorDate, sched.policy || 'mon-fri'); }
  catch(e){ DATES = BAKED.slice(); }
}

var today = iso(new Date());
function currentDay(){
  var i = DATES.indexOf(today);
  if (i >= 0) return i+1;
  for (var j=0;j<DATES.length;j++){ if (DATES[j] >= today) return j+1; }
  return 24;
}
var todayDay = currentDay();

var railEl = document.getElementById('nav');
var mainEl = document.getElementById('main');
var paneEl = document.getElementById('pane');

function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
var DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
function fmtDate(s){ var p = s.split('-'); return MON[+p[1]-1] + ' ' + (+p[2]); }
function fmtLong(s){
  var d = parseISO(s);
  return DOW[d.getDay()] + ' ' + MON[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
}
function fmtDow(s){ var d = parseISO(s); return DOW[d.getDay()] + ' ' + MON[d.getMonth()] + ' ' + d.getDate(); }

/* ── sidebar ────────────────────────────────────────────── */
function buildNav(){
  var h = '';
  NAV.forEach(function(sec){
    if (sec.days){
      h += '<div class="sec wk">'+esc(sec.section)+'<em>'+esc(sec.sub||'')+'</em></div>';
      sec.days.forEach(function(d){
        var done = state['day'+d.day];
        h += '<div class="day'+(done?' done':'')+(d.day===todayDay?' today':'')+'" data-day="'+d.day+'">'
           +   '<div class="dayhead">'
           +     '<span class="dayno">'+(d.day<10?'0':'')+d.day+'</span>'
           +     '<span class="daytitle">'+esc(d.title)+'</span>'
           +     '<span class="daydate">'+fmtDate(DATES[d.day-1])+'</span>'
           +   '</div>'
           +   '<div class="daylinks">'
           +     '<a class="l" href="#'+d.learn+'">Learn</a>'
           +     '<a class="b" href="#'+d.lab+'">Lab</a>'
           +     '<label class="tick"><input type="checkbox" data-day="'+d.day+'"'+(done?' checked':'')+'> done</label>'
           +   '</div>'
           + '</div>';
      });
    } else {
      h += '<div class="sec">'+esc(sec.section)+'</div>';
      sec.items.forEach(function(it){
        h += '<a class="item" href="#'+it.id+'">'+esc(it.label)+'</a>';
      });
    }
  });
  railEl.innerHTML = h;
  updateProgress();
}

function updateProgress(){
  setTimeout(updateDue, 0);
  var n = 0; for (var k in state){ if (k.indexOf('day')===0 && state[k]) n++; }
  document.getElementById('pf').style.width = (n/24*100)+'%';
  document.getElementById('pt').textContent = n + ' / 24 days';
}

/* The lab markdown carries a baked date in its metadata line. If the schedule
   has been re-anchored, rewrite it so the page never shows two different dates
   for the same day. */
function restampHeader(root, n){
  var want = fmtLong(DATES[n-1]);
  var ps = root.querySelectorAll('.doc > p');
  for (var i = 0; i < Math.min(ps.length, 3); i++){
    var s = ps[i].querySelector('strong');
    if (s && /^\w{3} \w{3} \d{1,2}, \d{4}$/.test(s.textContent.trim())){
      if (s.textContent.trim() !== want) s.textContent = want;
      return;
    }
  }
}

/* ── reading comfort ────────────────────────────────────── */
var SIZES = [[16,'62ch','S'],[18,'66ch','M'],[20,'70ch','L']];
function applySize(i){
  var s = SIZES[i] || SIZES[1];
  document.documentElement.style.setProperty('--read-base', s[0]+'px');
  document.documentElement.style.setProperty('--measure-base', s[1]);
  state.size = i; save();
  var b = document.querySelectorAll('.tocrail .sizer button');
  for (var k=0;k<b.length;k++) b[k].classList.toggle('on', k===i);
}

/* ── book furniture: section numbers, framed parts, pull quotes ── */
var SETUP = /^(setup|scenario|task|query|given|premise|example)\b/i;

function bookify(root){
  var doc = root.querySelector('.doc');
  if (!doc) return;

  // 1. pull the leading "N." off each h2 into a margin numeral
  var h2s = doc.querySelectorAll('h2');
  for (var i=0;i<h2s.length;i++){
    var h = h2s[i], t = h.textContent, m = t.match(/^\s*(\d+)\.\s+/);
    if (!m) continue;
    h.dataset.n = m[1];
    // rewrite only the first text node so inline markup in the heading survives
    var walker = document.createTreeWalker(h, NodeFilter.SHOW_TEXT, null, false), first = walker.nextNode();
    if (first) first.nodeValue = first.nodeValue.replace(/^\s*\d+\.\s+/, '');
    var sp = document.createElement('span');
    sp.className = 'secno'; sp.textContent = '§ ' + m[1];
    h.insertBefore(sp, h.firstChild);
  }

  // 2. a markdown "---" separator before a heading is noise once sections are boxed
  [].slice.call(doc.children).forEach(function(el){
    if (el.tagName === 'HR' && el.nextElementSibling && el.nextElementSibling.tagName === 'H2') el.remove();
  });

  // 2b. the lab metadata line reads as a dateline, not body copy
  var h1 = doc.querySelector(':scope > h1');
  if (h1 && h1.nextElementSibling && h1.nextElementSibling.tagName === 'P')
    h1.nextElementSibling.classList.add('dateline');

  // 3. group each h2..next-h2 run into a <section> so parts can be styled as parts
  var kids = [].slice.call(doc.children), cur = null;
  for (var j=0;j<kids.length;j++){
    var el = kids[j];
    if (el.tagName === 'H2'){
      cur = document.createElement('section');
      cur.className = 'part' + (el.dataset.n ? ' sec-' + el.dataset.n : '');
      doc.insertBefore(cur, el);
      cur.appendChild(el);
    } else if (cur && el.tagName !== 'HEADER'){
      // a bare <hr> right before the next h2 is a markdown separator — drop it
      if (el.tagName === 'HR' && kids[j+1] && kids[j+1].tagName === 'H2'){ el.remove(); continue; }
      cur.appendChild(el);
    }
  }

  // 4. classify blockquotes
  doc.querySelectorAll('blockquote').forEach(function(q){
    var ps = q.querySelectorAll(':scope > p');
    var lead = q.querySelector('strong');
    if (lead && SETUP.test(lead.textContent.trim())){ q.classList.add('setup'); return; }
    if (ps.length === 1){
      var p = ps[0], s = p.querySelector('strong');
      // one paragraph that IS a bold sentence → pull quote
      if (s && s.textContent.trim().length === p.textContent.trim().length
            && p.textContent.trim().length < 220){
        q.classList.add('pull');
      }
    }
  });
}

function buildToc(root){
  var doc = root.querySelector('.doc');
  var rail = document.createElement('aside');
  rail.className = 'tocrail';
  var heads = doc ? doc.querySelectorAll('h2, h3') : [];
  var out = '';
  var seen = 0;
  for (var i=0;i<heads.length;i++){
    var h = heads[i];
    if (!h.id) h.id = 'h-' + i;
    var label = h.textContent.replace(/^§\s*\d+\s*/, '').trim();
    if (!label) continue;
    // only show h3s when there aren't too many, or the rail becomes a wall
    if (h.tagName === 'H3' && heads.length > 34) continue;
    out += '<a href="#'+h.id+'" data-h="'+h.id+'" class="'+(h.tagName==='H3'?'l3':'l2')+'">'
         + esc(label) + '</a>';
    seen++;
  }
  if (seen < 2) return null;
  rail.innerHTML = '<h5>On this page</h5>' + out
    + '<div class="sizer">'
    + SIZES.map(function(s,i){ return '<button type="button" data-size="'+i+'">'+s[2]+'</button>'; }).join('')
    + '</div>';
  return rail;
}

var spyTargets = [];
function wireSpy(root){
  var links = {}, rail = root.querySelector('.tocrail');
  spyTargets = [];
  if (!rail) return;
  rail.querySelectorAll('a[data-h]').forEach(function(a){
    links[a.dataset.h] = a;
    var t = document.getElementById(a.dataset.h);
    if (t) spyTargets.push({el:t, a:a});
  });
  rail.addEventListener('click', function(ev){
    var a = ev.target.closest('a[data-h]');
    if (a){
      ev.preventDefault();
      var t = document.getElementById(a.dataset.h);
      if (t) mainEl.scrollTo({top: t.offsetTop - 26, behavior:'smooth'});
      return;
    }
    var b = ev.target.closest('button[data-size]');
    if (b) applySize(+b.dataset.size);
  });
}

function onScroll(){
  var top = mainEl.scrollTop, h = mainEl.scrollHeight - mainEl.clientHeight;
  var bar = document.getElementById('readbar');
  if (bar) bar.firstChild.style.width = (h > 40 ? Math.min(100, top / h * 100) : 0) + '%';
  var best = null;
  for (var i=0;i<spyTargets.length;i++){
    if (spyTargets[i].el.offsetTop - 90 <= top) best = spyTargets[i]; else break;
  }
  for (var j=0;j<spyTargets.length;j++) spyTargets[j].a.classList.toggle('on', spyTargets[j]===best);
}

/* ── rendering ──────────────────────────────────────────── */
function decorate(root){
  // wrap tables so wide ones scroll inside their own box
  root.querySelectorAll('table').forEach(function(t){
    if (t.parentNode.classList.contains('tablewrap')) return;
    var w = document.createElement('div'); w.className = 'tablewrap';
    t.parentNode.insertBefore(w, t); w.appendChild(t);
  });
  // copy buttons on code blocks
  root.querySelectorAll('pre').forEach(function(pre){
    if (pre.querySelector('.copybtn')) return;
    var b = document.createElement('button');
    b.className = 'copybtn'; b.type = 'button'; b.textContent = 'copy';
    b.addEventListener('click', function(ev){
      ev.stopPropagation();
      var txt = pre.querySelector('code') ? pre.querySelector('code').textContent : pre.textContent;
      try {
        navigator.clipboard.writeText(txt).then(function(){
          b.textContent='copied'; b.classList.add('done');
          setTimeout(function(){ b.textContent='copy'; b.classList.remove('done'); },1300);
        });
      } catch(e){ b.textContent='select it'; setTimeout(function(){b.textContent='copy';},1300); }
    });
    pre.appendChild(b);
  });
}

function show(id, push){
  if (/^cards-(warmup|\d+)$/.test(id)){
    showStudy(id);
    if (push !== false && location.hash !== '#'+id) history.replaceState(null,'','#'+id);
    return;
  }
  var doc = DOCS[id];
  if (!doc){ id = 'readme'; doc = DOCS[id]; }

  var m = id.match(/^(learn|lab)-(\d+)$/);
  var kind = doc.kind;
  var crumb = '<div class="crumb"><span class="k '+kind+'">'+kind+'</span>';
  if (m){
    var n = +m[2];
    crumb += '<span class="d">Day '+(n<10?'0':'')+n+' · '+fmtDate(DATES[n-1])+'</span>';
  }
  crumb += '</div>';

  var jump = '<div class="jump">';
  if (m){
    var n2 = +m[2];
    jump += '<a class="'+(m[1]==='lab'?'pri':'')+'" href="#learn-'+n2+'">Learn module</a>';
    jump += '<a class="'+(m[1]==='learn'?'pri':'')+'" href="#lab-'+n2+'">Hands-on lab</a>';
    if (n2>1) jump += '<a href="#learn-'+(n2-1)+'">&larr; Day '+(n2-1)+'</a>';
    if (n2<24) jump += '<a href="#learn-'+(n2+1)+'">Day '+(n2+1)+' &rarr;</a>';
    jump += '<a href="#cards-'+n2+'">Flashcards ('+((D.cards[String(n2)]||[]).length)+')</a>';
    jump += '<button data-mark="'+n2+'">'+(state['day'+n2]?'✓ done':'mark day done')+'</button>';
  } else {
    jump += '<a href="#readme">README</a><a href="#progress">Progress</a><a href="#aws-lane">AWS lane</a>';
  }
  jump += '</div>';

  paneEl.innerHTML = crumb + jump + '<div class="doc">' + doc.html + '</div>';
  if (m) restampHeader(paneEl, +m[2]);
  bookify(paneEl);
  decorate(paneEl);
  var toc = buildToc(paneEl);
  document.body.classList.toggle('notoc', !toc);
  if (toc) paneEl.appendChild(toc);
  wireSpy(paneEl);
  applySize(typeof state.size === 'number' ? state.size : 1);
  mainEl.scrollTop = 0;
  onScroll();
  document.title = doc.title + ' — FDE Bootcamp';

  railEl.querySelectorAll('a').forEach(function(a){
    a.classList.toggle('on', a.getAttribute('href') === '#'+id);
  });
  document.body.classList.remove('railopen');

  var active = railEl.querySelector('a[href="#'+id+'"]');
  if (active) {
    var r = active.getBoundingClientRect(), rr = railEl.parentNode.getBoundingClientRect();
    if (r.top < rr.top || r.bottom > rr.bottom) active.scrollIntoView({block:'center'});
  }
  if (push !== false && location.hash !== '#'+id) history.replaceState(null,'','#'+id);
}

/* ── flashcards ─────────────────────────────────────────── */
/* Leitner boxes. A card you got right moves up a box and comes back later;
   a card you missed goes straight back to box 1 and returns tomorrow. */
var CARDS = D.cards || {};
var CKEY = 'fde-cards-v1';
var GAP  = [0, 1, 2, 4, 8, 16];      // days until a card in box 1..5 is due again
var cstate = {};
try { cstate = JSON.parse(localStorage.getItem(CKEY) || '{}') || {}; } catch(e){ cstate = {}; }
function csave(){ try{ localStorage.setItem(CKEY, JSON.stringify(cstate)); }catch(e){} }

function today0(){ var d = new Date(); d.setHours(0,0,0,0); return d.getTime(); }
function cardKey(c){ return c.day + '.' + c.n; }
function boxOf(c){ var s = cstate[cardKey(c)]; return s && s.b ? s.b : 1; }
function dueAt(c){
  var s = cstate[cardKey(c)];
  if (!s || !s.t) return 0;                      // never seen — due now
  return s.t + GAP[Math.min(s.b || 1, 5)] * 86400000;
}
function isDue(c){ return dueAt(c) <= today0(); }

function grade(c, ok){
  var k = cardKey(c), s = cstate[k] || {b:1, n:0, miss:0};
  s.b = ok ? Math.min((s.b || 1) + 1, 5) : 1;
  s.n = (s.n || 0) + 1;
  if (!ok) s.miss = (s.miss || 0) + 1;
  s.t = today0();
  cstate[k] = s; csave();
}

function deckFor(n){ return (CARDS[String(n)] || []).slice(); }

/* the 0:20 warm-up: everything due from the days you have already worked,
   oldest box first, capped so it stays a drill and not an afternoon. */
function warmupDeck(){
  var upto = 0;
  for (var i = 1; i <= 24; i++) if (state['day'+i]) upto = i;
  if (!upto) upto = Math.max(1, currentDay() - 1);
  var pool = [];
  for (var d = 1; d <= upto; d++) pool = pool.concat(deckFor(d));
  var due = pool.filter(isDue);
  due.sort(function(a,b){
    var ba = boxOf(a) - boxOf(b);
    return ba !== 0 ? ba : dueAt(a) - dueAt(b);
  });
  return due.slice(0, 20);
}

function dueCount(){
  var upto = 0;
  for (var i = 1; i <= 24; i++) if (state['day'+i]) upto = i;
  if (!upto) upto = Math.max(1, currentDay() - 1);
  var n = 0;
  for (var d = 1; d <= upto; d++) deckFor(d).forEach(function(c){ if (isDue(c)) n++; });
  return n;
}

function updateDue(){
  var el = document.getElementById('duecount');
  if (!el) return;
  var n = dueCount();
  el.textContent = n ? n + ' due' : '';
}

var deck = null, pos = 0, shown = false, tally = {good:0, again:0};

function studyRender(){
  var host = paneEl.querySelector('.study');
  if (!host) return;
  var titleEl = host.querySelector('.shead h2');

  if (pos >= deck.length){
    host.querySelector('.body').innerHTML =
      '<div class="done"><h3>Deck clear</h3>'
      + '<p>' + (tally.again
          ? 'The ' + tally.again + ' you missed come back tomorrow. That is the point of them.'
          : 'Every card first try. Push the interval out and trust it.') + '</p>'
      + '<div class="tally">' + tally.good + ' right &nbsp;·&nbsp; ' + tally.again + ' to repeat</div>'
      + '<button data-restart="1">Run it again</button>'
      + (deck.length && deck[0] ? '<a href="#learn-' + deck[0].day + '">Back to the chapter</a>' : '')
      + '</div>';
    host.querySelector('.count').textContent = 'done';
    host.querySelector('.srcbar i').style.width = '100%';
    updateDue();
    return;
  }

  var c = deck[pos];
  host.querySelector('.count').textContent = (pos + 1) + ' / ' + deck.length
    + '  ·  box ' + boxOf(c) + '/5';
  host.querySelector('.srcbar i').style.width = (pos / deck.length * 100) + '%';

  var html = '<div class="card">'
    + '<p class="src">Day ' + (c.day < 10 ? '0' : '') + c.day + ' &middot; self-check ' + c.n + '</p>'
    + '<p class="qq">' + inl(c.q) + '</p>'
    + (shown ? '<p class="aa">' + inl(c.a) + '</p>' : '')
    + '</div>'
    + '<div class="acts">'
    + (shown
        ? '<button class="again" data-g="0">Again &nbsp;<b>1</b></button>'
          + '<button class="good" data-g="1">Got it &nbsp;<b>2</b></button>'
        : '<button class="flip" data-flip="1">Show answer &nbsp;<b>space</b></button>')
    + '</div>'
    + '<div class="keys">space to flip &nbsp;·&nbsp; 1 missed &nbsp;·&nbsp; 2 got it &nbsp;·&nbsp; esc to leave</div>';

  host.querySelector('.body').innerHTML = html;
  if (titleEl) titleEl.textContent = titleEl.textContent;  // no-op, keeps the header stable
}

/* the self-checks contain `code`, *emphasis* and **bold** — render just those */
function inl(s){
  return esc(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[\s(])\*([^*]+)\*/g, '$1<em>$2</em>');
}

function studyAdvance(ok){
  if (pos >= deck.length) return;
  grade(deck[pos], ok);
  tally[ok ? 'good' : 'again']++;
  pos++; shown = false;
  studyRender();
}

function showStudy(id){
  var m = id.match(/^cards-(warmup|\d+)$/);
  var isWarm = m[1] === 'warmup';
  var n = isWarm ? null : +m[1];

  deck = isWarm ? warmupDeck() : deckFor(n);
  pos = 0; shown = false; tally = {good:0, again:0};

  var title = isWarm ? 'Warm-up drill' : 'Day ' + (n < 10 ? '0' : '') + n + ' — flashcards';
  var sub = isWarm
    ? '<span class="d">everything due from the days you have finished</span>'
    : '<span class="d">Day ' + (n<10?'0':'') + n + ' &middot; ' + fmtDate(DATES[n-1]) + '</span>';

  var jump = '<div class="jump">';
  if (!isWarm){
    jump += '<a href="#learn-' + n + '">Learn module</a><a href="#lab-' + n + '">Hands-on lab</a>';
    if (n > 1) jump += '<a href="#cards-' + (n-1) + '">&larr; Day ' + (n-1) + ' cards</a>';
    if (n < 24) jump += '<a href="#cards-' + (n+1) + '">Day ' + (n+1) + ' cards &rarr;</a>';
  }
  jump += '<a href="#readme">Leave</a></div>';

  paneEl.innerHTML =
    '<div class="crumb"><span class="k learn">cards</span>' + sub + '</div>'
    + jump
    + '<div class="study"><div class="shead"><h2>' + esc(title) + '</h2>'
    + '<span class="count"></span></div>'
    + '<div class="srcbar"><i></i></div><div class="body"></div></div>';

  document.body.classList.add('notoc');
  mainEl.scrollTop = 0;
  document.title = title + ' — FDE Bootcamp';
  railEl.querySelectorAll('a').forEach(function(a){
    a.classList.toggle('on', a.getAttribute('href') === '#' + id);
  });
  document.body.classList.remove('railopen');

  if (!deck.length){
    paneEl.querySelector('.body').innerHTML =
      '<div class="done"><h3>Nothing due</h3>'
      + '<p>Every card from the days you have finished is scheduled for a later date. '
      + 'Mark another day done, or drill a specific day from its page.</p>'
      + '<a href="#cards-1">Day 01 cards</a></div>';
    return;
  }
  studyRender();
}

paneEl.addEventListener('click', function(ev){
  var t = ev.target.closest('button');
  if (!t || !paneEl.querySelector('.study')) return;
  if (t.dataset.flip){ shown = true; studyRender(); }
  else if (t.dataset.g !== undefined){ studyAdvance(t.dataset.g === '1'); }
  else if (t.dataset.restart){ pos = 0; shown = false; tally = {good:0, again:0}; studyRender(); }
});

document.addEventListener('keydown', function(e){
  if (!paneEl.querySelector('.study')) return;
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.key === ' '){ e.preventDefault(); if (!shown){ shown = true; studyRender(); } }
  else if (e.key === '1' && shown){ e.preventDefault(); studyAdvance(false); }
  else if (e.key === '2' && shown){ e.preventDefault(); studyAdvance(true); }
  else if (e.key === 'Escape'){ location.hash = '#readme'; }
});

/* ── search ─────────────────────────────────────────────── */
var INDEX = null;
function buildIndex(){
  if (INDEX) return INDEX;
  INDEX = [];
  var tmp = document.createElement('div');
  for (var id in DOCS){
    tmp.innerHTML = DOCS[id].html;
    INDEX.push({ id:id, title:DOCS[id].title, kind:DOCS[id].kind,
                 text:(tmp.textContent||'').replace(/\s+/g,' ') });
  }
  return INDEX;
}

function search(q){
  var idx = buildIndex(), lq = q.toLowerCase(), hits = [];
  idx.forEach(function(d){
    var lt = d.text.toLowerCase(), pos = lt.indexOf(lq);
    var tpos = d.title.toLowerCase().indexOf(lq);
    if (pos < 0 && tpos < 0) return;
    var snip = '';
    if (pos >= 0){
      var s = Math.max(0, pos-90), e = Math.min(d.text.length, pos+lq.length+130);
      snip = (s>0?'…':'') + d.text.slice(s,e) + (e<d.text.length?'…':'');
    } else { snip = d.text.slice(0,200)+'…'; }
    var count = lt.split(lq).length - 1;
    hits.push({ id:d.id, title:d.title, kind:d.kind, snip:snip,
                score:(tpos>=0?1000:0) + count });
  });
  hits.sort(function(a,b){ return b.score - a.score; });

  var h = '<div class="crumb"><span class="k guide">search</span><span class="d">'
        + hits.length + ' result' + (hits.length===1?'':'s') + ' for “'+esc(q)+'”</span></div><div class="hits">';
  if (!hits.length) h += '<p style="color:var(--ink-3)">Nothing found. Try a shorter term.</p>';
  hits.slice(0,60).forEach(function(x){
    var re = new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','ig');
    h += '<a class="hit" href="#'+x.id+'"><div class="t">'+esc(x.title)+'</div>'
       + '<div class="s">'+esc(x.snip).replace(re,'<mark>$1</mark>')+'</div></a>';
  });
  h += '</div>';
  paneEl.innerHTML = h;
  mainEl.scrollTop = 0;
}

/* ── reschedule panel ───────────────────────────────────── */
var schedEl = document.getElementById('sched');
var sdEl = document.getElementById('sd');
var sdateEl = document.getElementById('sdate');
var spolEl = document.getElementById('spol');
var sprevEl = document.getElementById('spreview');

for (var i = 1; i <= 24; i++){
  var o = document.createElement('option');
  o.value = i; o.textContent = 'Day ' + (i<10?'0':'') + i;
  sdEl.appendChild(o);
}

function spanLabel(){
  document.getElementById('spanlabel').textContent =
    '24 days · ' + fmtDate(DATES[0]) + ' – ' + fmtDate(DATES[23]);
}

function fillPanel(){
  sdEl.value = sched ? sched.anchorDay : todayDay;
  sdateEl.value = sched ? sched.anchorDate : today;
  spolEl.value = sched ? (sched.policy || 'mon-fri') : 'mon-fri';
  previewPanel();
}

function previewPanel(){
  try {
    var d = computeDates(+sdEl.value, sdateEl.value, spolEl.value);
    sprevEl.innerHTML = 'Day 01 &nbsp;<b>' + fmtDow(d[0]) + '</b><br>'
                      + 'Day 24 &nbsp;<b>' + fmtDow(d[23]) + '</b>';
  } catch(e){ sprevEl.textContent = 'Pick a valid date.'; }
}

function applySchedule(newSched){
  sched = newSched;
  try {
    if (sched) localStorage.setItem(SKEY, JSON.stringify(sched));
    else localStorage.removeItem(SKEY);
  } catch(e){}
  DATES = sched ? computeDates(sched.anchorDay, sched.anchorDate, sched.policy) : BAKED.slice();
  todayDay = currentDay();
  spanLabel(); buildNav();
  var cur = location.hash.slice(1);
  show(cur && DOCS[cur] ? cur : 'readme', false);
  schedEl.hidden = true;
}

document.getElementById('schedbtn').addEventListener('click', function(){
  schedEl.hidden = !schedEl.hidden;
  if (!schedEl.hidden) fillPanel();
});
sdEl.addEventListener('change', previewPanel);
sdateEl.addEventListener('change', previewPanel);
spolEl.addEventListener('change', previewPanel);
document.getElementById('sapply').addEventListener('click', function(){
  if (!sdateEl.value) { sprevEl.textContent = 'Pick a date first.'; return; }
  applySchedule({ anchorDay: +sdEl.value, anchorDate: sdateEl.value, policy: spolEl.value });
});
document.getElementById('sreset').addEventListener('click', function(){ applySchedule(null); });
document.getElementById('scancel').addEventListener('click', function(){ schedEl.hidden = true; });

/* ── wiring ─────────────────────────────────────────────── */
spanLabel();
buildNav();

var box = document.getElementById('q');
var meta = document.getElementById('qm');
var t = null;
box.addEventListener('input', function(){
  clearTimeout(t);
  var q = box.value.trim();
  meta.textContent = q ? 'searching…' : '';
  t = setTimeout(function(){
    if (q.length < 2){ meta.textContent=''; if(!q) show(location.hash.slice(1)||'readme',false); return; }
    search(q);
    meta.textContent = 'press Esc to clear';
  }, 180);
});
box.addEventListener('keydown', function(e){
  if (e.key === 'Escape'){ box.value=''; meta.textContent=''; box.blur(); show(location.hash.slice(1)||'readme',false); }
});

document.addEventListener('keydown', function(e){
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if (e.key === '/'){ e.preventDefault(); box.focus(); }
  var m = (location.hash.slice(1)||'').match(/^(learn|lab)-(\d+)$/);
  if (!m) return;
  var n = +m[2];
  if (e.key === 'ArrowRight' && n < 24) location.hash = '#'+m[1]+'-'+(n+1);
  if (e.key === 'ArrowLeft'  && n > 1)  location.hash = '#'+m[1]+'-'+(n-1);
  if (e.key === 'l') location.hash = '#learn-'+n;
  if (e.key === 'b') location.hash = '#lab-'+n;
});

document.addEventListener('change', function(e){
  var cb = e.target.closest ? e.target.closest('input[type=checkbox][data-day]') : null;
  if (!cb) return;
  state['day'+cb.getAttribute('data-day')] = cb.checked;
  save(); buildNav();
  var cur = location.hash.slice(1); if (cur && DOCS[cur]) show(cur, false);
});

document.addEventListener('click', function(e){
  var b = e.target.closest ? e.target.closest('button[data-mark]') : null;
  if (!b) return;
  var n = b.getAttribute('data-mark');
  state['day'+n] = !state['day'+n];
  save(); buildNav(); show(location.hash.slice(1), false);
});

document.getElementById('reset').addEventListener('click', function(){
  if (confirm('Clear all progress?')){ state = {}; save(); buildNav();
    var cur = location.hash.slice(1); if (cur && DOCS[cur]) show(cur, false); }
});

document.querySelector('.railtoggle').addEventListener('click', function(){
  document.body.classList.toggle('railopen');
});

document.getElementById('gotoday').addEventListener('click', function(){
  location.hash = '#learn-' + todayDay;
});

mainEl.addEventListener('scroll', onScroll, {passive:true});

window.addEventListener('hashchange', function(){
  box.value=''; meta.textContent='';
  show(location.hash.slice(1) || 'readme', false);
});

show(location.hash.slice(1) || 'readme', false);
updateDue();
})();
"""


def main() -> int:
    docs, nav = build_docs()
    data = {"docs": docs, "nav": nav, "dates": DATES, "cards": CARDS}

    body = """
<aside id="rail">
  <div class="brand">
    <h1>FDE Trainer Bootcamp</h1>
    <button class="sub" id="schedbtn" title="Re-anchor the schedule">
      <span id="spanlabel">24 days · 120 hours</span>
    </button>
  </div>

  <div class="sched" id="sched" hidden>
    <h2>Re-anchor the schedule</h2>
    <div class="row">
      <label for="sd">Which day are you on?</label>
      <select id="sd"></select>
    </div>
    <div class="row">
      <label for="sdate">And that day is…</label>
      <input type="date" id="sdate">
    </div>
    <div class="row">
      <label for="spol">Working days</label>
      <select id="spol">
        <option value="mon-fri">Mon – Fri (weekends off)</option>
        <option value="mon-sat">Mon – Sat (Sundays off)</option>
        <option value="all">Every day</option>
      </select>
    </div>
    <div class="preview" id="spreview"></div>
    <div class="btns">
      <button class="go" id="sapply">Apply</button>
      <button id="sreset">Reset</button>
      <button id="scancel">Cancel</button>
    </div>
  </div>
  <div class="searchbox">
    <input id="q" type="search" placeholder="Search everything…  (press /)" aria-label="Search the course">
    <div class="searchmeta" id="qm"></div>
  </div>
  <div class="progwrap">
    <div class="progbar"><div class="progfill" id="pf"></div></div>
    <div class="progtxt">
      <span id="pt">0 / 24 days</span>
      <span><button id="gotoday">today</button> · <button id="reset">reset</button></span>
    </div>
    <div class="warmup">
      <a href="#cards-warmup" id="warmup">Warm-up drill<em id="duecount"></em></a>
    </div>
  </div>
  <nav id="nav"></nav>
</aside>

<div id="readbar"><i></i></div>
<div id="main"><div class="pane" id="pane"></div></div>
<button class="railtoggle" aria-label="Toggle navigation">☰</button>
""".strip()

    page = (
        TEMPLATE.replace("__CSS__", CSS)
        .replace("__BODY__", body)
        .replace("__DATA__", js_json(data))
        .replace("__JS__", JS)
    )
    OUT.write_text(page, encoding="utf-8")

    n_docs = len(docs)
    n_cards = sum(len(v) for v in CARDS.values())
    print(f"  wrote {OUT.name}")
    print(f"  {n_cards} flashcards across 24 decks")
    print(f"  {n_docs} documents · {OUT.stat().st_size / 1024 / 1024:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
