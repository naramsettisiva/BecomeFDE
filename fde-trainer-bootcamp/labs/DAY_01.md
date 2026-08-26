# Day 01 — Environment, First Tokens, and the Discipline

**Tue Aug 25, 2026** · Week 1 · Maps to: *pre-work* · Backend: **local** · Est. cost: **$0.00**

> **Before you start — read `learn/DAY_01_LEARN.md` (1:15).**
> What a model call is, tokens, the four layers, silent failure. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** On a real engagement your first day is not modelling — it's getting a
laptop, a VPN, a repo, and a model endpoint to all agree with each other, in front
of a client who is watching. The engineer who can stand up a clean, reproducible
environment in an hour buys credibility for the whole engagement. The one who
spends day one fighting Python versions never gets it back.

**Trainer lens.** Environment setup is where you lose 30% of a cohort. If you have
not personally hit and fixed every failure mode — wrong Python, missing key, model
not pulled, venv not activated — you cannot rescue a student in a live session.
Today you deliberately break your own environment three times and fix it.

---

## Objectives

By 5:00 today you can:

1. Explain the difference between a model, a provider, an endpoint, and an SDK, without hand-waving.
2. Run a chat completion against a **local** model and a **hosted** model through one interface.
3. Read a token count and turn it into a dollar figure.
4. Diagnose the five most common "it doesn't work" states from the error message alone.
5. Commit and push to GitHub as a reflex, not a chore.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Setup + doctor |
| 1 | 1:15 | **Learn** — `learn/DAY_01_LEARN.md` |
| 2 | 2:15 | Lab: `hello_llm.py`, three deliberate breakages, cost accounting |
| 3 | 0:30 | Teach-back #1 |
| 4 | 0:30 | Ship + retro |

---

## Block 0 — Setup (0:30)

```bash
cd fde-trainer-bootcamp
bash scripts/setup.sh
source .venv/bin/activate
cp .env.example .env          # then paste your keys
python scripts/doctor.py
```

Everything must be `OK` except possibly the two API-key warnings. If `ollama service`
fails: open a second terminal, run `ollama serve`, then `ollama pull llama3.1:8b` and
`ollama pull nomic-embed-text`.

Then:

```bash
python scripts/build_corpus.py     # writes the 10-doc freight corpus you'll use all month
```

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_01_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 The four layers people conflate

Write these out in `notebooks/day01_notes.md` in your own words before reading mine:

| Layer | Example | What changes when you swap it |
|---|---|---|
| **Model** | `llama3.1:8b`, `gpt-4o-mini`, `claude-sonnet-4-5` | Quality, latency, cost, context window, tool-calling fidelity |
| **Provider** | Ollama, OpenAI, Anthropic, Bedrock, Azure | Auth, rate limits, data residency, SLA, billing |
| **Endpoint/API shape** | `/v1/chat/completions`, Anthropic Messages API | Request/response schema, streaming format, tool-call encoding |
| **SDK** | `openai`, `anthropic`, `langchain` | Ergonomics only — should never leak into your business logic |

The single most valuable habit from today: **one seam**. `src/fdekit/llm.py` is that
seam. Every lab for the next 23 days calls `chat()`, never `client.chat.completions`
directly. When on Day 17 you swap providers to compare cost, it will be one env var.

Open `src/fdekit/llm.py` and read it end to end. Notice the trick: **Ollama speaks the
OpenAI API shape**, so `base_url=http://localhost:11434/v1` lets one SDK drive both
free local models and paid hosted ones. This is the reason you can do 80% of this
bootcamp for $0.

### 1.2 Tokens, context, and money

Run this and stare at the output:

```bash
python - <<'PY'
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
samples = [
    "Detention accrues at $65 per hour after 2 hours of free time.",
    "SHP-202608-0041729",
    "detention",
    "détention",
    "def compute_detention(arrive_ts, appt_ts, free_minutes=120):",
    "電子ログデバイス",
]
for s in samples:
    ids = enc.encode(s)
    print(f"{len(ids):3d} tokens | {s[:60]}")
    print(f"          | {[enc.decode([i]) for i in ids][:14]}")
PY
```

Answer in your notes:

- Why does `SHP-202608-0041729` cost so many tokens? What does that imply about
  putting raw IDs in prompts at scale?
- Why is Japanese more expensive per character?
- If your RAG prompt carries 6,000 tokens of context per query and you serve 40,000
  queries a month on `gpt-4o-mini`, what's the monthly input cost? (Prices are in
  `src/fdekit/cost.py`.) Do this on paper. FDEs get asked this in meetings.

Now read `src/fdekit/cost.py`. Every `chat()` call appends to `.cost_log.jsonl`.
You will have a month of real data by Day 18 — that's the point.

### 1.3 Temperature, determinism, and why demos fail

```bash
python - <<'PY'
import sys; sys.path.insert(0, "src")
from fdekit import chat
q = "In one sentence: what is routing guide depth?"
for t in (0.0, 0.0, 1.0, 1.0):
    print(f"T={t}: {chat(q, temperature=t, max_tokens=60).strip()}\n")
PY
```

Two things to internalise:

1. `temperature=0` is *not* deterministic in practice (batching, GPU nondeterminism,
   provider-side changes). Never promise a client bit-identical output.
2. Your default should be `0.0` for anything extraction- or tool-shaped, and higher
   only for genuinely generative copy. Most beginners leave it at 0.7 and then blame
   the model for being flaky.

---

## Block 2 — Lab (2:15)

### 2.1 Build `labs/day01/hello_llm.py` (45 min)

Create the file yourself — typing it is the point — to this spec:

```python
"""Day 1 — a CLI that answers a freight question against local or hosted models,
and reports tokens, latency, and cost."""
# Requirements:
#  - typer CLI:  python labs/day01/hello_llm.py "question" --backend local
#  - --backend {local,openai,anthropic}
#  - --system to override the system prompt
#  - prints: answer, wall-clock ms, input/output tokens, USD
#  - uses fdekit.chat and fdekit.CostTracker — no direct SDK calls
#  - handles a missing API key with a helpful message, not a stack trace
```

Reference solution is at the bottom of this file. **Do not read it until you've
tried for 30 minutes.** If you peek early you'll learn the code and not the debugging.

### 2.2 Break it on purpose (45 min)

For each of these, cause the failure, capture the exact error text into
`labs/day01/FAILURE_MODES.md`, and write the one-line diagnosis a student needs:

| # | Break it by | You should learn to recognise |
|---|---|---|
| 1 | `deactivate` the venv, run the script | `ModuleNotFoundError` → venv not active |
| 2 | Stop `ollama serve`, run with `--backend local` | `APIConnectionError` → service down, not code broken |
| 3 | Set `OLLAMA_CHAT_MODEL=llama3.1:70b` (not pulled) | 404 model not found → pull it |
| 4 | Blank `OPENAI_API_KEY`, run `--backend openai` | Your own friendly error, not a traceback |
| 5 | `max_tokens=5` on a long question | Silent truncation — no error at all. **This is the dangerous one.** |

Number 5 is the lesson of the day: LLM systems fail *quietly*. A truncated answer
looks like a bad answer, not a bug. Half of production LLM debugging is noticing
that nothing errored.

### 2.3 Prompt sensitivity drill (30 min)

Same question, four framings, `temperature=0`, local backend:

```
A) "What is detention?"
B) "What is detention in freight?"
C) "You are a transportation operations analyst. Define detention as used in
    US truckload contracts. Two sentences. Include how free time works."
D)  C + this appended: "Answer only from the following text:\n<paste doc 02>"
```

Record all four answers in `labs/day01/prompt_drill.md`. Note where the model
invented a number. **D is RAG in its crudest form** — you just did it by hand.
Tomorrow you make it systematic.

---

## Block 3 — Teach-back #1 (0:30)

Record a **5-minute** screen recording (QuickTime → New Screen Recording) titled
"Why your first LLM call needs a seam". Save to `teaching/recordings/day_01.mov`.

Constraints that make this a real rep:

- No slides. Terminal and editor only.
- Start with the audience's problem, not the concept: *"You're going to be asked to
  switch from OpenAI to Bedrock two weeks into a project. Here's why that's a
  one-line change or a two-week refactor."*
- Show one live failure and recover from it on camera. Do not re-record the recovery.
- End with one sentence the listener could repeat to their own manager.

Then **watch it back at 1.5x**. Write your self-grade (1–5) and one specific fix in
`LEARNING_LOG.md`. Most common Day-1 problem: narrating what you're typing instead of
why. "Now I'm importing typer" teaches nothing.

---

## Block 4 — Ship + retro (0:30)

```bash
git add -A
git commit -m "Day 01: environment, provider seam, cost tracking, failure modes"
git push
python -m fdekit.cost      # today's spend, should be ~$0
```

Fill in the Day 01 entry in `LEARNING_LOG.md`. Be specific about confusions.

---

## Done when

- [ ] `python scripts/doctor.py` exits 0
- [ ] `hello_llm.py` works against local **and** at least one hosted backend
- [ ] `FAILURE_MODES.md` has all 5 errors with exact text and diagnosis
- [ ] `prompt_drill.md` shows the four framings and where hallucination appeared
- [ ] `teaching/recordings/day_01.mov` exists and you've graded it
- [ ] Repo pushed to GitHub

---

## Trap list (add to this file all month)

- Forgetting `source .venv/bin/activate` after a new terminal. Add it to your shell.
- Committing `.env`. Check `git status` before every commit for the rest of your life.
- Assuming `temperature=0` means reproducible.
- Not setting `max_tokens` and getting silently truncated output.
- Reading model docs for pricing and trusting your memory a month later. Prices in
  code, refreshed deliberately.

---

## Stretch (only if you finish early)

Add `--compare` to `hello_llm.py`: runs the same prompt across all three backends and
prints a table of answer / latency / cost. You'll want this on Day 18 anyway.

---

<details>
<summary><b>Reference solution — open only after 30 minutes of your own attempt</b></summary>

```python
#!/usr/bin/env python3
"""Day 1 — hello_llm.py"""
from __future__ import annotations

import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import typer
from rich.console import Console
from rich.table import Table

from fdekit import CostTracker, chat, settings

app = typer.Typer(add_completion=False)
console = Console()

DEFAULT_SYSTEM = (
    "You are a transportation operations analyst. Be precise and concise. "
    "If you do not know a contractual number, say so rather than guessing."
)


@app.command()
def ask(
    question: str,
    backend: str = typer.Option(settings.fdekit_backend, help="local|openai|anthropic"),
    system: str = typer.Option(DEFAULT_SYSTEM),
    temperature: float = typer.Option(0.0),
    max_tokens: int = typer.Option(512),
) -> None:
    try:
        t0 = time.perf_counter()
        with CostTracker(f"day01/{backend}") as c:
            answer = chat(
                question,
                system=system,
                backend=backend,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        ms = (time.perf_counter() - t0) * 1000
    except RuntimeError as exc:
        console.print(f"[red]Config problem:[/red] {exc}")
        console.print("Check your .env, then re-run [bold]python scripts/doctor.py[/bold]")
        raise typer.Exit(1)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]{type(exc).__name__}:[/red] {exc}")
        if "Connection" in type(exc).__name__:
            console.print("Is [bold]ollama serve[/bold] running?")
        raise typer.Exit(1)

    console.print(f"\n[bold]{answer.strip()}[/bold]\n")

    t = Table(show_header=False, box=None)
    t.add_row("backend", backend)
    t.add_row("latency", f"{ms:,.0f} ms")
    t.add_row("tokens", f"{c.input_tokens:,} in / {c.output_tokens:,} out")
    t.add_row("cost", f"${c.usd:.6f}")
    console.print(t)


if __name__ == "__main__":
    app()
```

</details>
