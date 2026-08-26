# Day 04 — RAG v1, End to End

**Fri Aug 28, 2026** · Week 1 · Maps to: **Module 01 — Retrieval Foundations** · Backend: **local** (+ optional `[PAID]` comparison) · Est. cost: **$0.00–1.00**

> **Before you start — read `learn/DAY_04_LEARN.md` (1:15).**
> The four-clause RAG contract, prompt assembly, verifiable citations. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** RAG is the "hello world" of client engagements — it's what 8 out of 10
prospects ask for by name, usually as "chat with our documents." Your value is not
building it (a competent engineer can in a day). Your value is knowing, on day three,
which of their documents will break it and telling them before they discover it.

**Trainer lens.** Today you build the reference implementation you will teach from for
the rest of your career. Make it clean, make it small enough to read on one screen,
and make every component swappable — because your lesson on Day 22 will be "now change
this one line and watch the answer get worse."

---

## Objectives

1. Ship an end-to-end RAG pipeline: ingest → chunk → embed → index → retrieve → assemble → generate → cite.
2. Make the citation *verifiable*, not decorative.
3. Show three ways the pipeline produces a confidently wrong answer, and instrument for each.
4. Explain "lost in the middle" and demonstrate it on your own system.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_04_LEARN.md` |
| 2 | 2:30 | Lab: build `src/fdekit/rag.py` + CLI, then break it three ways |
| 3 | 0:30 | Teach-back #4 |
| 4 | 0:15 | Ship + retro |

---

## Block 0 — Warm-up (0:30)

Closed book:

1. For unit-normalised vectors, how do cosine and Euclidean rankings relate? Prove it.
2. Which chunker won yesterday's bake-off, on which metric, and by how much?
3. Which query exposed dense retrieval's weakness on rare tokens? What's the fix called?
4. What do `M`, `ef_construction`, and `ef_search` trade against each other?

Re-run yesterday's bake-off script. Same numbers? If not, why not — did you leave
`temperature` non-zero somewhere, or is your index non-deterministic?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_04_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 The RAG contract

RAG is not "give the model some context." It's a contract with four clauses, and every
production failure is one of them being violated:

1. **The answer is in the corpus.** If it isn't, the system must say so. Most RAG demos
   have no refusal path at all — this is the number-one cause of the "it hallucinated"
   complaint. It didn't hallucinate; you never gave it permission to decline.
2. **Retrieval surfaces it.** Recall is the ceiling on everything downstream. A perfect
   generator cannot fix a chunk that wasn't retrieved.
3. **The prompt makes it usable.** Position, ordering, formatting, and token budget all
   change the answer even when the content is identical.
4. **The answer is attributable.** A citation the user can click and verify. Without
   this you have a chatbot, not a system of record.

Write these four on an index card. You will use them as the spine of a client
conversation dozens of times, and as the spine of a lesson on Day 22.

### 1.2 Prompt assembly, and lost-in-the-middle

Given k=6 chunks, the ordering matters. Models attend most reliably to the **beginning**
and **end** of long contexts and least reliably to the middle. So:

- Put the **most relevant** chunk first, the **second most relevant last**, and bury the
  rest. (Sort ascending by score, then reverse alternately — you'll implement it.)
- Or: reduce k. Six mediocre chunks routinely beat by three good ones.

Also decide, explicitly:

- **Delimiters.** XML-ish tags (`<doc id="02" title="...">`) beat markdown fences for
  making boundaries unambiguous to the model.
- **Metadata in-band.** Include `source_doc` and heading path *inside* the context block
  so the model can cite by ID rather than paraphrasing the filename.
- **Refusal instruction.** "If the context does not contain the answer, reply exactly:
  `INSUFFICIENT_CONTEXT`." A machine-checkable refusal token. This is worth more than
  three paragraphs of "be accurate."

### 1.3 Citations that are actually verifiable

Three grades:

| Grade | What it is | Verifiable? |
|---|---|---|
| Bronze | "Source: doc 02" appended by the model | No — the model can and will attach the wrong ID |
| Silver | Model emits `[doc_id]` inline; you check the ID was in the retrieved set | Partly |
| Gold | Model emits a verbatim `evidence_quote` per claim; you assert it's a substring of that chunk | Yes, automatically, with no LLM |

Build Gold. It costs you ~40 output tokens per answer and it gives you a hallucination
detector that runs in microseconds and costs nothing. On Day 13 this becomes a headline
metric on your scorecard.

---

## Block 2 — Lab (2:30)

### 2.1 `src/fdekit/rag.py` (75 min)

Keep it under 200 lines. Readability is a feature — this is teaching material.

```python
@dataclass
class Chunk:
    text: str; doc_id: str; heading_path: str; chunk_index: int

@dataclass
class Retrieved(Chunk):
    score: float

@dataclass
class Answer:
    text: str
    citations: list[Citation]        # doc_id + evidence_quote + verified: bool
    retrieved: list[Retrieved]
    refused: bool
    latency_ms: float
    usage: dict

class RagPipeline:
    def __init__(self, store, k=5, reorder="lost_in_middle", refuse_below=None): ...
    def ingest(self, corpus_dir: Path) -> int: ...
    def retrieve(self, q: str) -> list[Retrieved]: ...
    def assemble(self, q: str, chunks: list[Retrieved]) -> tuple[str, str]:  # (system, user)
        ...
    def generate(self, q: str) -> Answer: ...
    def verify(self, ans: Answer) -> Answer:   # substring-check every evidence_quote
        ...
```

Prompt template to start from (then improve it — improving it *is* Day 5):

```
SYSTEM:
You answer questions about freight transportation operations using ONLY the
provided context. You are precise about numbers and conditions.

Rules:
- If the context does not contain the answer, reply with exactly: INSUFFICIENT_CONTEXT
- Every factual claim must be followed by a citation of the form [doc_id]
- After your answer, output a JSON block:
  {"citations":[{"doc_id":"...","quote":"<verbatim span from context>"}]}
- Never state a number that does not appear verbatim in the context.
- Include the condition attached to a number (e.g. free time) whenever one exists.

USER:
<context>
<doc id="02" title="Detention, Demurrage and Accessorial Charges" section="Detention">
...
</doc>
...
</context>

Question: {question}
```

That last rule — "include the condition attached to a number" — came from Day 3, where
you saw chunking sever `$65/hour` from `after 2 hours free time`. **Prompt rules should
be traceable to observed failures.** A prompt full of generic pieties is a prompt nobody
maintains.

### 2.2 CLI + first real answers (25 min)

```bash
python -m labs.day04.ask "How much detention will I be charged for a 5-hour wait?"
python -m labs.day04.ask "What's our policy on drone deliveries?"     # must refuse
python -m labs.day04.ask "Why did the appointment times shift?"
python -m labs.day04.ask "Should I convert Dallas to Chicago to intermodal?"
```

Output should show: the answer, verified citations (green) vs. unverified (red),
the retrieved chunks with scores, latency, and cost.

### 2.3 Break it three ways (50 min)

Document each in `labs/day04/FAILURE_MODES.md` with the actual output.

**Break 1 — The multi-hop question.**
> "If a carrier's FTA drops to 83% for two quarters, what happens, and how does that
> affect their scorecard band?"

This needs doc 01 (Lane Review at <85%) *and* doc 06 (bands). Watch whether top-k
retrieval gets both. It usually won't — both documents are topically similar, so one
crowds out the other. **Note the fix (query decomposition) and that it's Day 8's lab.**

**Break 2 — The distractor.**
> "How many days of free time do I get?"

Doc 02 has *both* detention free time (2 hours) and demurrage free time (4–5 days).
Ambiguous question, two plausible chunks. Does the model pick one silently or ask?
Add a rule to the prompt that forces disambiguation and re-run. Record before/after.

**Break 3 — Lost in the middle.**
Take a query the system answers correctly at k=3. Re-run at k=12 with the correct
chunk forced into position 6. Does it still answer correctly? Now apply your
`lost_in_middle` reordering and re-run. **This is a demo you will use in front of
clients for years** — record the terminal output.

---

## Block 3 — Teach-back #4 (0:30)

Record 8–10 min: **"The four-clause RAG contract, and which clause your system is
breaking."** `teaching/recordings/day_04.mov`

Structure it as a diagnostic, not a tutorial: "Your RAG is wrong. Here are four
questions to ask, in order, and the experiment that answers each." Use your Break 1/2/3
outputs as the evidence.

This is the first teach-back that could be shown to a client. Treat it that way.

---

## Block 4 — Ship + retro (0:15)

```bash
git add -A && git commit -m "Day 04: RAG v1 with verifiable citations and refusal" && git push
```

---

## Done when

- [ ] `RagPipeline` ingests, retrieves, generates, and cites end to end
- [ ] Refusal path works — the drone question returns `INSUFFICIENT_CONTEXT`
- [ ] Every evidence quote is substring-verified and unverified ones are flagged
- [ ] All three breakages documented with real terminal output
- [ ] Lost-in-the-middle demonstrated *and* fixed by reordering

---

## Trap list

- No refusal path. Then blaming the model.
- Citations the model generates freely, unchecked. It will cite a doc it didn't use.
- k chosen by vibes. Pick it with the Day 5 eval, not today.
- Ingesting on every query. Cache the index; you'll be running hundreds of queries tomorrow.
- Putting the question only at the top of a long prompt. Repeat it after the context too —
  measurably helps, costs 15 tokens.

---

## Stretch `[PAID]`

Run the same 8 queries on `--backend openai` with `gpt-4o-mini`. Build a table: answer
quality (your judgement, 1–5), citation-verification rate, latency, cost per query.
Extrapolate to 40,000 queries/month. **That table is a slide in every client pitch you
will ever give.**
