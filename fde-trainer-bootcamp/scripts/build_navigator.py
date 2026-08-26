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
    return MD.convert(path.read_text(encoding="utf-8"))


# ── the 24 dates, Sundays excluded ──────────────────────────────────────────
def course_dates() -> list[str]:
    out, d = [], date(2026, 8, 25)
    while len(out) < 24:
        if d.weekday() != 6:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


DATES = course_dates()

DAY_TITLES = {}
for n in range(1, 25):
    first = (ROOT / "labs" / f"DAY_{n:02d}.md").read_text(encoding="utf-8").split("\n")[0]
    DAY_TITLES[n] = re.sub(r"^#\s*Day \d+\s*[—-]\s*", "", first).strip()

WEEKS = [
    (1, "Foundations", "Aug 25 – 31", range(1, 7)),
    (2, "Agents", "Sep 1 – 7", range(7, 13)),
    (3, "Production", "Sep 8 – 14", range(13, 19)),
    (4, "The craft", "Sep 15 – 21", range(19, 25)),
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
                "html": render(ROOT / "learn" / f"DAY_{n:02d}_LEARN.md"),
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
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
  --f-mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --rail-w:320px;
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
.brand .sub{font-family:var(--f-mono);font-size:10px;color:var(--ink-3);letter-spacing:.1em;text-transform:uppercase}

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
.pane{max-width:820px;margin:0 auto;padding:44px 40px 140px}

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

/* ── document typography ───────────────────────────────── */
.doc h1{
  font-family:var(--f-display);font-weight:700;font-size:2.05rem;line-height:1.1;
  letter-spacing:-.025em;margin:0 0 16px;text-wrap:balance;
}
.doc h2{
  font-family:var(--f-display);font-weight:700;font-size:1.38rem;letter-spacing:-.018em;
  margin:44px 0 12px;padding-top:8px;
}
.doc h3{font-family:var(--f-display);font-weight:600;font-size:1.08rem;margin:30px 0 9px;letter-spacing:-.008em}
.doc h4{font-family:var(--f-display);font-weight:600;font-size:.96rem;margin:22px 0 7px}
.doc p{margin:0 0 15px;max-width:70ch}
.doc ul,.doc ol{margin:0 0 16px;padding-left:22px;max-width:70ch}
.doc li{margin-bottom:6px}
.doc li>ul,.doc li>ol{margin-top:6px;margin-bottom:6px}
.doc strong{color:#FFF;font-weight:600}
.doc em{color:var(--ink)}
.doc a{color:var(--signal-2);text-decoration:none;border-bottom:1px solid rgba(240,169,59,.3)}
.doc a:hover{border-bottom-color:var(--signal)}
.doc hr{border:0;border-top:1px solid var(--rail);margin:34px 0}

.doc blockquote{
  margin:0 0 18px;padding:13px 17px;background:var(--surface-2);
  border-left:3px solid var(--signal);border-radius:0 4px 4px 0;color:var(--ink-2);
}
.doc blockquote p:last-child{margin-bottom:0}
.doc blockquote strong{color:var(--signal-2)}

.doc code{
  font-family:var(--f-mono);font-size:.85em;background:var(--surface-3);
  padding:1.5px 5px;border-radius:3px;color:var(--signal-2);
  border:1px solid var(--rail-soft);
}
.doc pre{
  background:var(--surface-2);border:1px solid var(--rail);border-left:3px solid var(--signal);
  border-radius:0 4px 4px 0;padding:15px 17px;overflow-x:auto;margin:0 0 18px;position:relative;
}
.doc pre code{
  background:none;border:0;padding:0;color:var(--ink-2);
  font-size:.79rem;line-height:1.72;display:block;
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

.tablewrap{overflow-x:auto;margin:0 0 20px;border:1px solid var(--rail);border-radius:4px}
.doc table{border-collapse:collapse;width:100%;font-size:.87rem;min-width:440px}
.doc th,.doc td{text-align:left;padding:9px 13px;border-bottom:1px solid var(--rail-soft);vertical-align:top}
.doc thead th{
  font-family:var(--f-mono);font-size:9.5px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--ink-3);background:var(--surface-2);border-bottom:1px solid var(--rail);white-space:nowrap;
}
.doc tbody tr:last-child td{border-bottom:0}
.doc tbody tr:hover{background:var(--surface-2)}

.doc details{
  margin:0 0 18px;border:1px solid var(--rail);border-radius:4px;background:var(--surface-2);
  overflow:hidden;
}
.doc details summary{
  cursor:pointer;padding:12px 16px;font-family:var(--f-display);font-weight:600;font-size:.93rem;
  color:var(--signal-2);list-style:none;user-select:none;
}
.doc details summary::-webkit-details-marker{display:none}
.doc details summary::before{content:"▸ ";color:var(--ink-3)}
.doc details[open] summary::before{content:"▾ "}
.doc details summary:hover{background:var(--surface-3)}
.doc details[open]{background:var(--surface)}
.doc details>*:not(summary){padding-left:16px;padding-right:16px}
.doc details>*:last-child{padding-bottom:14px}

.doc input[type=checkbox]{accent-color:var(--signal);margin-right:6px}

mark{background:rgba(240,169,59,.28);color:var(--ink);border-radius:2px;padding:0 2px}

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
@media (max-width:940px){
  #rail{position:fixed;left:0;top:0;z-index:40;transform:translateX(-100%);transition:transform .22s}
  body.railopen #rail{transform:none}
  .railtoggle{display:block}
  .pane{padding:28px 20px 120px}
  .doc h1{font-size:1.6rem}
}
@media print{
  #rail,.railtoggle,.jump,.copybtn{display:none}
  body{display:block;background:#fff;color:#000}
  .pane{max-width:none;padding:0}
  .doc a{color:#000}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function(){
"use strict";
var D = JSON.parse(document.getElementById('course-data').textContent);
var DOCS = D.docs, NAV = D.nav, DATES = D.dates;
var KEY = 'fde-nav-v1';
var state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch(e){ state = {}; }
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(state)); }catch(e){} }

var today = new Date().toISOString().slice(0,10);
var todayDay = DATES.indexOf(today) + 1;              // 0 if not a course day
if (!todayDay) { for (var i=0;i<DATES.length;i++){ if (DATES[i] >= today){ todayDay = i+1; break; } } }
if (!todayDay) todayDay = 24;

var railEl = document.getElementById('nav');
var mainEl = document.getElementById('main');
var paneEl = document.getElementById('pane');

function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

function fmtDate(iso){
  var p = iso.split('-'), m = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return m[+p[1]-1] + ' ' + (+p[2]);
}

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
           +     '<span class="daydate">'+fmtDate(d.date)+'</span>'
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
  var n = 0; for (var k in state){ if (k.indexOf('day')===0 && state[k]) n++; }
  document.getElementById('pf').style.width = (n/24*100)+'%';
  document.getElementById('pt').textContent = n + ' / 24 days';
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
    jump += '<button data-mark="'+n2+'">'+(state['day'+n2]?'✓ done':'mark day done')+'</button>';
  } else {
    jump += '<a href="#readme">README</a><a href="#progress">Progress</a><a href="#aws-lane">AWS lane</a>';
  }
  jump += '</div>';

  paneEl.innerHTML = crumb + jump + '<div class="doc">' + doc.html + '</div>';
  decorate(paneEl);
  mainEl.scrollTop = 0;
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

/* ── wiring ─────────────────────────────────────────────── */
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

window.addEventListener('hashchange', function(){
  box.value=''; meta.textContent='';
  show(location.hash.slice(1) || 'readme', false);
});

show(location.hash.slice(1) || 'readme', false);
})();
"""


def main() -> int:
    docs, nav = build_docs()
    data = {"docs": docs, "nav": nav, "dates": DATES}

    body = """
<aside id="rail">
  <div class="brand">
    <h1>FDE Trainer Bootcamp</h1>
    <div class="sub">24 days · 120 hours · Aug 25 – Sep 21</div>
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
  </div>
  <nav id="nav"></nav>
</aside>

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
    print(f"  wrote {OUT.name}")
    print(f"  {n_docs} documents · {OUT.stat().st_size / 1024 / 1024:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
