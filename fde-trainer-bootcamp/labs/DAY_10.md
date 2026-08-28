# Day 10 — Memory and Context Engineering

**Wed Sep 9, 2026** · Week 2 · Maps to: **Module 04 — Memory and Context** · Backend: **local** + `[PAID]` · Est. cost: **$2–4**

> **Before you start — read `learn/DAY_10_LEARN.md` (1:15).**
> Four memory types, the context budget, compaction loss. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** "Context engineering" has quietly replaced "prompt engineering" as the real
job. A model with a 200k context window does not mean you should use 200k tokens — it
means you now have to *decide* what goes in, and that decision determines quality, cost,
and latency more than any other single lever. Clients feel this as "it forgot what I told
it" and "why is it so expensive." Same root cause.

**Trainer lens.** Memory is where students build the most elaborate, least necessary
machinery. Teaching the *hierarchy* — what actually needs to persist, and for how long —
saves a cohort weeks of misdirected effort.

---

## Objectives

1. Implement the four memory types: working, episodic, semantic, procedural.
2. Build a context budget allocator and defend every token in the window.
3. Implement three compaction strategies and measure the information loss of each.
4. Explain — with your own experiment — why "just use a bigger context window" is wrong.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_10_LEARN.md` |
| 2 | 2:30 | Lab: memory layer + budget allocator + the needle experiment |
| 3 | 0:30 | Teach-back #10 |
| 4 | 0:15 | Ship |

---

## Block 0 — Warm-up (0:30)

<!--cards-->
> **Cards first — 5 minutes.** Open **Warm-up drill** in the sidebar of `fde-bootcamp.html`.
> It deals you every card that is due from the days you have finished, hardest box first, and
> it is capped at 20 so it stays a drill. Cards you miss come back tomorrow; cards you know
> go 1 → 2 → 4 → 8 → 16 days out. Then do the recall below, closed book.
<!--/cards-->


1. Three multi-agent topologies; when each is right.
2. What is context loss at handoff, and what field prevents the most of it?
3. Did single-agent or multi-agent win your comparison, and on which task?
4. In your deep-research brief, how did you populate the "could not establish" section?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_10_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 The four memory types

Borrowed from cognitive science, and the mapping is genuinely useful:

| Type | Holds | Lifetime | Storage | Freight example |
|---|---|---|---|---|
| **Working** | The current turn's context window | One request | The messages array | Retrieved chunks, current question, tool results so far |
| **Episodic** | What happened in this conversation / session | Session, maybe longer | Message store + summaries | "Earlier you asked about DAL–CHI" |
| **Semantic** | Durable facts about the user/org | Indefinite | Key-value or vector store | "Siva's org uses a 2-hour free-time standard, not 1" |
| **Procedural** | How to do things — learned patterns, skills | Indefinite, versioned | Prompt fragments, tool definitions, "skills" files | "When asked about detention, always state the cap" |

The one people skip is **procedural**, and it's the one with the highest leverage. Every
time you add a rule to a system prompt because you observed a failure, that's procedural
memory being written by hand. Making that loop explicit — observe failure → write rule →
version it → measure — is a genuinely advanced practice and a great capstone feature.

### 1.2 The context budget

Treat the window as a budget you allocate, line by line. For a 32k working budget:

```
system prompt + rules            1,500   fixed
tool schemas (6 tools)           1,200   fixed — grows fast, prune aggressively
procedural memory (learned rules)  600   fixed-ish
semantic memory (user facts)       400   selected by relevance
episodic summary                   800   compacted
recent turns verbatim            3,000   last 3 exchanges
retrieved chunks (k=5)           4,000   the variable you actually tune
                                ------
                                11,500   in
answer                           1,000   out
                                ------
headroom for agent steps        20,500
```

Two rules that follow immediately:

1. **Tool schemas are context.** Six tools with verbose descriptions can eat 2k tokens on
   *every* step of an agent loop. On an 8-step loop that's 16k tokens of pure overhead.
   Prune descriptions ruthlessly, or load tools dynamically by route.
2. **Every fixed cost is paid per step**, not per query. This is why agent costs surprise
   people. Multiply by steps before you quote a number.

Build the allocator today. Then, whenever quality drops, you can ask "what got evicted?"
instead of guessing.

### 1.3 Compaction, and what it costs

| Strategy | How | Loses |
|---|---|---|
| **Truncation (sliding window)** | Keep last N turns | Everything older, silently. Cheap, brutal |
| **Summarisation** | LLM-compress older turns | Specifics — numbers, IDs, exact wording. Costs a call |
| **Extraction** | Pull structured facts into semantic memory, discard prose | Nuance and negations. Best signal-to-token ratio |
| **Hierarchical** | Recent verbatim + mid summarised + old extracted | Complexity |

The failure mode to demonstrate today: **summarisation drops the negations.** "The client
said NOT to use intermodal for reefer lanes" summarises to "discussed intermodal for
reefer lanes." Then the agent recommends exactly the thing it was told not to. Build the
experiment, watch it happen, and you will never forget it — nor will a room you show it to.

---

## Block 2 — Lab (2:30)

### 2.1 `src/fdekit/memory.py` (60 min)

```python
class WorkingMemory:
    """The messages array + a token accountant."""
    def add(self, role, content): ...
    def tokens(self) -> int: ...
    def render(self, budget: int) -> list[Message]:
        """Fit into budget using the configured compaction strategy."""

class EpisodicMemory:
    """Turn history with compaction."""
    def compact(self, strategy: Literal["truncate","summarise","extract","hierarchical"]): ...

class SemanticMemory:
    """Durable facts. Vector-indexed so retrieval is by relevance, not recency."""
    def write(self, fact: Fact): ...          # dedupe on write — check similarity > 0.9
    def recall(self, query: str, k=5) -> list[Fact]: ...

class ProceduralMemory:
    """Learned rules, versioned, each traceable to the failure that produced it."""
    def add_rule(self, rule: str, learned_from: str, added_at: datetime): ...
    def render(self) -> str: ...              # injected into the system prompt

class ContextBudget:
    """Allocates the window. Reports what was included and what was evicted."""
    def allocate(self, components: dict[str, Renderable]) -> tuple[str, BudgetReport]: ...
```

`SemanticMemory.write` deduping on embedding similarity is a small detail with a big
payoff — without it, memory fills with fifteen restatements of the same fact and your
recall gets worse over time, not better. That decay is one of the most common
"our AI got worse" complaints in production.

### 2.2 The needle experiment (45 min)

Prove to yourself that bigger context isn't free. `labs/day10/needle.py`:

```
For context lengths [2k, 8k, 16k, 32k, 64k]:
  For needle positions [0%, 25%, 50%, 75%, 100%]:
    - Build a context of filler freight documents
    - Insert one specific fact: "The detention rate for Ridgeline Freight
      on refrigerated lanes is $88 per hour."
    - Ask for exactly that fact
    - Record: correct?, latency, input tokens, cost
Plot: accuracy heatmap (length × position), and cost vs. length.
```

Run it on local first (cheap, and small models degrade dramatically — good for teaching),
then `[PAID]` on `gpt-4o-mini` for contrast. **Two models, two heatmaps, side by side, is
one of the best single slides you will produce in this entire bootcamp.**

Then answer: at what context length does *your* stack stop being reliable? That number is
a real engineering constraint you can quote to a client.

### 2.3 The negation-loss experiment (25 min)

```
1. Build a 15-turn conversation that includes three constraints, one phrased
   as a negation: "Don't recommend intermodal for our reefer lanes — we tried
   it in 2024 and the claims rate was unacceptable."
2. Compact with each of your four strategies down to 800 tokens.
3. Ask: "What should we do with the Dallas–Chicago reefer volume?"
4. Record which strategies preserved the constraint and which recommended the
   forbidden thing.
```

Write the result in `evals/day10_compaction_loss.md`. Then fix your summariser: add
"preserve all negative constraints, prohibitions, and things explicitly ruled out,
verbatim" to the summarisation prompt and re-run. Measure the improvement.

That fix — one sentence in a summarisation prompt — is exactly the kind of thing that
separates a working system from a demo, and it's the kind of specific, earned advice
that makes a training session valuable.

### 2.4 Wire it into the agent (20 min)

Give your Day 9 supervisor real memory. Run a 3-turn conversation:
1. "What's our detention policy?"
2. "What about for reefer?"          ← needs episodic memory to resolve "what about"
3. "Apply that to Ridgeline's Q3."   ← needs episodic + semantic + data

Then start a *new session* and ask #3 cold. The difference is what memory bought you.
Record both traces — the contrast is the demo.

---

## Block 3 — Teach-back #10 (0:30)

Record 10 min: **"Bigger context windows made context engineering more important, not less."**
`teaching/recordings/day_10.mov`

Open with the needle heatmap. Then the budget table — show that tool schemas cost you 2k
per step. Close with the negation-loss demo, because it's visceral: the system confidently
recommends the one thing it was told not to.

---

## Block 4 — Ship (0:15)

```bash
git add -A && git commit -m "Day 10: four memory types, context budget allocator, needle + negation-loss experiments" && git push
```

---

## Done when

- [ ] All four memory classes implemented, with dedupe on semantic writes
- [ ] `ContextBudget` reports inclusions and evictions per request
- [ ] Needle heatmaps for two models, with your reliability ceiling identified
- [ ] Negation-loss demonstrated, then mitigated, with before/after numbers
- [ ] Multi-turn conversation working with memory; cold-start contrast recorded

---

## Trap list

- Storing every turn in semantic memory. It's a fact store, not a log.
- Summarising on every turn. Summarise on a threshold, and cache the summary.
- Forgetting tool schemas count against the window, on every step.
- No eviction reporting. When quality drops you'll have no idea what got dropped.
- Semantic memory without dedupe → slow decay that looks like model regression.
- Assuming the model reads the middle of a long context as well as the ends. You now
  have a heatmap proving otherwise. Use it.

---

## Stretch

Implement **procedural memory learning**: after each failed eval case, have a small model
propose one rule that would have prevented it. Add proposed rules to a staging file.
Re-run the full golden set with each candidate rule and keep only rules that improve the
score without regressing others. You've just built a self-improving prompt with a
regression gate — which is, essentially, what a good AI team does by hand every week.
