# Day 02 — Python for AI Engineers: Structure, Async, and Failure

**Wed Aug 26, 2026** · Week 1 · Maps to: *pre-work* · Backend: **local** · Est. cost: **$0.00–0.20**

> **Before you start — read `learn/DAY_02_LEARN.md` (1:15).**
> Structured output, async fan-out, resilience primitives. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** The gap between "I called an LLM" and "I shipped an LLM system" is
almost entirely ordinary engineering: typed contracts, retries, concurrency, and
graceful degradation. Clients do not pay for prompts. They pay for a service that
holds up when the provider 429s at 2pm on a Tuesday.

**Trainer lens.** Your students will be a mix of strong Python people and strong
domain people. You need to teach `pydantic` + `asyncio` in a way that doesn't lose
the second group. Today you build the explanation, not just the skill.

You said you're rusty. Good — today is deliberately a Python day. It will feel slow.
It is the highest-leverage day of Week 1, because every remaining lab assumes it.

---

## Objectives

1. Get **guaranteed-shape** output from an LLM using pydantic, and explain why
   "just ask it for JSON" fails at scale.
2. Run 50 LLM calls concurrently without melting your laptop or the provider.
3. Wrap any call in retry-with-backoff and a timeout, and say what each protects against.
4. Write a `pytest` test for non-deterministic output — the thing everyone claims is impossible.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up: recall drill from Day 1 |
| 1 | 1:15 | **Learn** — `learn/DAY_02_LEARN.md` |
| 2 | 2:15 | Lab: `extractor.py` — a typed, concurrent, tested extraction pipeline |
| 3 | 0:30 | Teach-back #2 |
| 4 | 0:30 | Ship + retro |

---

## Block 0 — Warm-up (0:30)

Closed-book, in `notebooks/day02_warmup.md`:

1. Draw the four layers from Day 1 and give an example of each.
2. Your RAG prompt is 6,000 input tokens and returns 400 output tokens on `gpt-4o-mini`.
   40,000 queries/month. What's the bill? Now on `gpt-4o`?
3. Name the LLM failure mode that produces no error at all.
4. Why does `SHP-202608-0041729` tokenize badly, and what would you do about it if
   you had to put 200 shipment IDs in a prompt?

Then re-run one command from yesterday from memory, no notes. If you can't, that's
your first spaced-repetition signal.

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_02_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 Structured output done properly

Three escalating techniques. Know all three and when each applies — clients will
have all three in their codebase.

**Level 1 — ask nicely (fragile).**
```
"Return JSON with keys shipment_id, detention_minutes."
```
Fails on: markdown fences, prose preambles, trailing commas, a model that decides to
explain itself. Fine for a demo, never for production.

**Level 2 — schema in the prompt + parse + repair.**
Generate the JSON Schema from a pydantic model, put it in the prompt, parse, and on
`ValidationError` feed the error back to the model once. This works everywhere,
including on local models with no structured-output support. **This is your default**,
because on client sites you often can't choose the model.

**Level 3 — provider-native constrained decoding.**
`response_format={"type": "json_schema", ...}` (OpenAI) or tool-use forcing
(Anthropic). The tokens literally cannot violate the grammar. Best when available.

Write the trade-off table into your notes — you will teach this exact table on Day 22.

```python
from pydantic import BaseModel, Field
from typing import Literal

class DetentionEvent(BaseModel):
    shipment_id: str = Field(pattern=r"^SHP-\d{6}-\d{7}$")
    facility: str
    stop_type: Literal["origin", "destination"]
    free_time_minutes: int = Field(ge=0, le=1440)
    detention_minutes: int = Field(ge=0)
    billable_usd: float = Field(ge=0)
    evidence_quote: str = Field(description="Verbatim span from the source text")
    confidence: float = Field(ge=0, le=1)
```

Note `evidence_quote`. **Always make the model cite the span it used.** It roughly
halves fabrication and it gives you a cheap automated check: is the quote actually a
substring of the input? That check needs no LLM and no human. You'll use it on Day 13.

### 1.2 Async, concurrency, and rate limits

Sequential 50 calls at 1.2s each = 60s. Concurrent with a semaphore of 8 = ~8s.
On Day 13 you'll run 200-case eval suites; sequential is unusable.

The three things people get wrong:

1. **Unbounded concurrency.** `asyncio.gather` over 500 calls will get you rate-limited
   or OOM your local Ollama. Always a `Semaphore`.
2. **Blocking calls inside async.** A sync SDK call inside a coroutine blocks the loop.
   Use the async client, or `asyncio.to_thread`.
3. **No per-task error isolation.** One failure in `gather` kills everything unless you
   pass `return_exceptions=True`. In an eval run you want the other 199 results.

### 1.3 Resilience primitives

| Primitive | Protects against | Wrong use |
|---|---|---|
| **Timeout** | A hung request holding a worker forever | Setting it below P99 latency and creating your own failures |
| **Retry + exponential backoff + jitter** | Transient 429/500 | Retrying a 400 (your bug) or a content filter (never succeeds) |
| **Circuit breaker** | Hammering a provider that's fully down | Opening on a single failure |
| **Fallback model** | Provider outage, context overflow | Silently degrading quality with no telemetry |

Rule: **retry only idempotent, transient failures.** Read the `tenacity` docs section
on `retry_if_exception_type` and write down which OpenAI exceptions are retryable.

---

## Block 2 — Lab (2:15)

Build `labs/day02/extractor.py`. It reads `data/corpus/*.md` and extracts structured
policy facts. Spec:

```python
# 1. Pydantic models
class PolicyRule(BaseModel):
    topic: str                  # e.g. "detention", "demurrage", "OTIF window"
    rule: str                   # one-sentence statement of the rule
    numeric_value: float | None # the number, if the rule has one
    unit: str | None            # "usd_per_hour", "minutes", "days", "percent"
    source_doc: str
    evidence_quote: str
    confidence: float

class ExtractionResult(BaseModel):
    rules: list[PolicyRule]

# 2. structured_call(text, doc_name) -> ExtractionResult
#    Level-2 technique: schema in prompt, parse, one repair attempt on ValidationError.
# 3. async run over all 10 docs, Semaphore(4), return_exceptions=True
# 4. tenacity retry: 3 attempts, exponential backoff, jitter, only on transient errors
# 5. validate: assert evidence_quote is a substring of the source doc; flag misses
# 6. write evals/day02_extracted_rules.json  + print a rich summary table
```

Milestones so you know if you're on pace:

- **0:30** — models defined, one doc extracting successfully, sync.
- **1:00** — repair loop working (test it by forcing a bad schema).
- **1:30** — async over all 10 docs with the semaphore.
- **2:00** — evidence validation + output file + summary table.

### Then: `labs/day02/test_extractor.py` (last 30 min of the block)

Testing non-deterministic systems — the four patterns:

```python
# 1. Schema tests — deterministic, always run.
def test_result_parses_to_schema(): ...

# 2. Invariant tests — properties that must hold regardless of wording.
def test_all_evidence_quotes_are_substrings_of_source(): ...
def test_detention_rate_is_positive_and_under_500(): ...

# 3. Golden-fact tests — facts the corpus definitely contains.
@pytest.mark.parametrize("doc,topic,value,unit", [
    ("02_detention_and_accessorials.md", "detention", 65.0, "usd_per_hour"),
    ("02_detention_and_accessorials.md", "TONU", 150.0, "usd"),
    ("03_otif_measurement.md", "grocery appointment window", 30.0, "minutes"),
])
def test_known_facts_are_extracted(doc, topic, value, unit): ...

# 4. Regression snapshot — store today's output; fail loudly if tomorrow's differs
#    by more than a tolerance. Not a pass/fail gate, a "look at this" gate.
```

That fourth one is the mindset shift: for LLM systems, some tests are **alarms**, not
gates. Teaching a room the difference between an assertion and an alarm is a genuinely
good 10 minutes of curriculum.

---

## Block 3 — Teach-back #2 (0:30)

Record 6–8 min: **"Three ways to get JSON out of an LLM, and when each one breaks."**
Save `teaching/recordings/day_02.mov`.

Requirements:
- Show Level 1 failing live. Make the model emit a markdown fence and watch `json.loads` die.
- Use one concrete number from the freight corpus, not `{"foo": "bar"}`.
- Explicitly name who each level is for: Level 2 for "you don't control the model",
  Level 3 for "you do".

Self-grade in the log. Watch for: did you say "basically" more than twice? Did you
explain the *failure* before the *fix*? (Fix-first teaching doesn't stick.)

---

## Block 4 — Ship + retro (0:30)

```bash
ruff check labs/ src/ --fix
pytest labs/day02 -v
git add -A && git commit -m "Day 02: typed extraction, async fan-out, resilience, tests" && git push
```

---

## Done when

- [ ] `extractor.py` processes all 10 docs concurrently, under 30s on local model
- [ ] Repair loop demonstrably recovers from at least one validation failure
- [ ] Evidence-quote substring check runs and reports a hallucination rate
- [ ] All four test patterns present and passing
- [ ] Teach-back recorded and graded

---

## Trap list

- `asyncio.gather` without `return_exceptions=True` in an eval run.
- Retrying a 400. You are retrying your own bug.
- Pydantic `float` where the domain needs `Decimal` (money). Note it now; matters at invoicing.
- Trusting `confidence` from the model. It is a token, not a probability. Calibrate it
  against your evidence check on Day 13 and see how bad it is.
- Semaphore too high for local Ollama — it will queue and your "concurrency" is fake.
  Measure it.

---

## Stretch

Swap the extractor to Level 3 (provider-native JSON schema) on `--backend openai` and
compare: violation rate, latency, cost, and how much prompt you could delete. That
comparison is a slide on Day 22.
