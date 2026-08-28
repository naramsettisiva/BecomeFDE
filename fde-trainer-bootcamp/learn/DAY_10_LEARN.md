# Day 10 · Learn — Memory, and the context window as a budget

**Read before `labs/DAY_10.md`. Budget 1:15.**

---

## 1. Where this sits

Day 7 gave you a loop that re-sends its whole transcript every step. Day 9 gave you several of
those loops handing work to each other. Both days you treated the context as something that
happened *to* you — it grew, you paid for it, you capped it and stopped.

Today you take control of it. The question stops being "how do I bound the context" and becomes
**"what exactly is in it, and who decided?"**

Two client complaints motivate this, and they're the same complaint. *"It forgot what I told it
last week."* *"Why is this so expensive?"* One is a token you failed to include; the other is a
thousand tokens you included on every step without deciding to. Both are allocation failures, and
neither is fixed by a bigger model or a longer window.

---

## 2. The mechanism

### 2.1 The model has no memory. None.

Every request to a model API is cold. No session, no connection state, no server-side transcript.
When a chat interface appears to remember your last message, what physically happens is that **the
client re-sent every prior message in the array.** Continuity is an application feature implemented
by resending.

You know this shape: a stateless app server behind a load balancer, where all continuity lives in a
store you built plus a token you pass. The model is that app server, and no sticky session is
available at any price. So "memory" here is never a model property — it is **a store you own plus a
policy for what gets loaded into the request**, and all of today's engineering is in the policy.

### 2.2 The four types, and what each is made of

The taxonomy is borrowed from cognitive science — Tulving's 1972 episodic/semantic split, extended
with the declarative/procedural distinction. Borrowed vocabulary usually adds nothing; this earns
its place because the four have **genuinely different storage, lifetimes, read paths, and failure
modes.**

| Type | Holds | Lifetime | Storage | Read path | Freight example |
|---|---|---|---|---|---|
| **Working** | This request's context | One request | The `messages` array | All of it, every step | Chunks, question, tool results so far |
| **Episodic** | What happened this session | Session | Message store + summaries | Recency-ordered, compacted | "Earlier you asked about DAL→CHI" |
| **Semantic** | Durable facts about user/org | Indefinite | Key-value or vector index | **Relevance-ranked, not recency** | "Free time here is 2 hours, not 1" |
| **Procedural** | How to do the work | Indefinite, **versioned** | Prompt fragments, tool defs, skill files | Always-on or task-selected | "Always state the $650 detention cap" |

Mapped to your world: **working memory is process RAM**, gone when the request returns. **Episodic
is the ticket thread** — chronological, verbose, occasionally holding the one line that explains
everything. **Semantic is the CMDB** — you query it for the three entries relevant to now.
**Procedural is the runbook** — not facts but procedure, written because somebody got burned.

**Row 3's recency-vs-relevance distinction is the one most often missed.** Episodic is ordered by
*when*; semantic is retrieved by *how related to this question*. That's why semantic wants a vector
index, and why a fact established six weeks ago can surface today. Build semantic memory as "the
last 50 things the user said" and you've built a second episodic store with a misleading name.

**Procedural is the most-skipped and the highest-leverage.** You've been writing it by hand since
Day 2. Every line you added to a system prompt after watching something fail — *"always state the
cap," "never quote `detention_minutes` for a live dispute"* — was a procedural write: manual,
unversioned, with no record of the failure that caused it and no test that it still helps.

Making the loop explicit is what separates a system from a habit:

```
observe failure → write a candidate rule → version it with provenance
                → re-run the golden set  → keep it only if it improves without regressing
```

The last clause is the whole thing. A rules file that only grows is a prompt that slowly rots:
rules contradict each other, dead rules from fixed bugs keep costing tokens on every step, and
nobody can say which one is load-bearing. **Give every rule a `learned_from` and an `added_at`, and
gate additions on the Day 5 golden set.**

### 2.3 Semantic memory decays without dedupe-on-write

A small implementation detail with an outsized production consequence, and the source of one of the
most common "our AI got worse" reports you'll be handed.

Semantic recall is **top-k by similarity.** You have five slots. If the store holds eleven
slightly-different phrasings of *"free time is two hours"*, a detention question scores all eleven
above everything else — so your five slots return **one distinct fact, five times**, and the four
other facts that mattered never load. Nothing was lost; **effective recall fell**, because
duplicates crowd the k. It degrades gradually, correlating with no deployment, which is exactly why
it gets reported as model regression.

The fix is four lines at the write path:

```python
def write(self, fact: Fact) -> None:
    v = embed(fact.text)
    near = self.index.search(v, k=1)
    if near and near[0].score > 0.90:
        self.supersede(near[0].id, fact)   # newer wins; keep the old one's provenance
    else:
        self.index.add(v, fact)
```

Three things about it people get wrong.

**0.90 is a starting point, not a constant.** It's a threshold on a score distribution, and Day 3
already told you what that means: model- and corpus-specific, found by plotting known-duplicate
pairs against known-distinct pairs and taking the separation point.

**Supersede, don't merge, and never silently coexist.** "Free time is 2 hours" and "free time is 90
minutes on the Memphis lane" aren't duplicates — they're a rule and an exception, and both belong.
"Free time is 2 hours" and "we get 2 hours of free time" are one fact, and keeping both is pure
loss. On genuine contradiction the newer write wins and the older is kept as *history*, not as a
retrievable fact — because when a client asks "why did it say 90 minutes," you need to point at the
write that caused it.

**A fact store is not a log.** Turns go in episodic. Semantic holds what is durable, org-scoped, and
worth retrieving out of order — "Ridgeline Freight is primary on DAL→CHI," "OTIF is reported at
PO-line level here." A question somebody asked once is not a fact about the world.

### 2.4 The window is a budget you allocate line by line

Here's the reframe. A context window is not a capacity you fill until it complains. It is **a fixed
quantity you allocate deliberately, with a declared policy for who loses when demand exceeds
supply** — if you've run an error budget, you already have the instinct.

A worked allocation for a 32k window, one agent step:

| Component | Tokens | Kind | Who sets it | Eviction rank |
|---|---:|---|---|---|
| System prompt + guardrails | 1,500 | fixed | you, at design time | never |
| Tool schemas (6 tools) | 1,200 | fixed | your tool list | never — prune the list instead |
| Procedural memory (14 rules) | 630 | fixed-ish | the learning loop, §2.2 | 4th — oldest low-value rules |
| Semantic memory (top-k facts) | 450 | selected | relevance to this query | 2nd — beyond top-3 |
| Episodic summary | 800 | compacted | the compactor, §2.6 | 3rd — recompact tighter |
| Recent turns verbatim (last 3) | 1,140 | windowed | recency | 3rd — drop to last 2 |
| Retrieved chunks (k=8) | 6,800 | **the tunable one** | retrieval + k | **1st — lowest-ranked chunk** |
| | **12,520** | | | |
| Reserved for output | 1,000 | | | |
| Headroom for agent steps | 18,480 | | | |

Four consequences.

**The window is not the budget.** It's the window minus reserved output minus headroom for the steps
still to come. An allocation that fits in 32k on step 1 does not fit on step 6, because steps 2–5
appended observations you're now re-sending. Budget against the *projected* size at the last step —
Day 7 §2.5's "check before you call," applied to space instead of money.

**Retrieved chunks are the only large variable.** Everything else is within a few hundred tokens of
fixed, which is why k is the parameter everyone tunes.

**Declare the eviction order in advance.** Otherwise a framework decides for you, and the common
default — drop from the oldest end — eventually eats your system prompt.

**Report inclusions and evictions on every request.** The highest-value twenty lines in today's lab.
When quality drops next Thursday, "k fell from 8 to 7 on 31% of requests after the new rules landed"
is a finding. "It seems worse" is not.

### 2.5 Tool schemas are context, and you pay them on every step

1,200 tokens of tool schemas feels small — about 10% of that input. But recall Day 7 §2.2: the
schemas go in the request, and there is a request *per step*.

```
6 tools × 200 tokens = 1,200 per step
1,200 × 8 steps      = 9,600 tokens of pure schema, for one user question
```

Nothing was retrieved with those tokens. They're the price of the model knowing what it *could*
call, paid once per step, forever.

**This is the biggest single reason agent bills surprise people.** Everyone quotes cost per query,
because that's how a RAG call works. An agent's fixed costs are per *step*, and the model decides
the step count at runtime:

```
fixed cost per query ≈ (system + rules + schemas) × steps
```

Multiply before you quote. Two mitigations and one trap:

**Prune the tool list, not the descriptions.** Day 7 §2.7 was emphatic that descriptions are the
only evidence the model gets for a routing decision it makes every step. Cutting them saves 60
tokens per step and buys an extra step — a net loss. **Cut whole tools.** Three sharp tools at 180
tokens beat nine terse ones at 90.

**Load tools by route.** You built a router on Day 8. A `policy_lookup` query doesn't need
`compute_detention` and `carrier_scorecard` in context. This routinely halves the fixed cost and
improves selection accuracy, because a shorter list is an easier choice.

**The trap:** dynamic tool lists break prompt caching. If your provider caches a stable prefix and
you vary the list per request, you lose the hit on the largest fixed block in your prompt. On
high-volume, low-step workloads the cache is worth more than the pruning. Measure both.

### 2.6 Compaction: four strategies, and precisely what each loses

Episodic memory grows without bound; your budget doesn't. Every strategy is lossy, so the
engineering is in **knowing which loss you chose.**

| Strategy | How | Compression | Loses — precisely |
|---|---|---|---|
| **Truncation** (sliding window) | Keep the last N turns | Arbitrary | Everything older, **silently and completely**. Free and instant |
| **Summarisation** | LLM-compress older turns to prose | ~8:1 | Specifics — numbers, IDs, dates, who-said-what — **and negations** (§2.7) |
| **Extraction** | Pull structured facts into semantic memory, discard prose | ~20:1 | Nuance, hedging, the reasoning behind a decision. Best signal per token |
| **Hierarchical** | Recent verbatim + middle summarised + old extracted | Tunable | Complexity, and two extra calls to maintain |

Three properties discovered late:

**Compaction costs money and latency, in the request path.** Summarising a 5,700-token transcript is
a real API call — cents and seconds, while a user waits. So **compact on a threshold, not every
turn**, and **cache the result**. Recompacting an unchanged history every turn is the most common
performance bug here, and it's invisible because everything still works.

**Compaction is an irreversible write.** Once turns 1–13 are an 800-token summary, the originals are
gone unless you kept them. Keep the raw transcript in cold storage — the first time you must answer
"why did it say that?" about last month, the summary won't tell you and the transcript will.

**Truncation's silence is the real danger.** You can read a summary and notice what's missing.
Truncation drops turn 3 with no trace, so the system can't report what it forgot — and neither
can you.

### 2.7 Why summarisation drops negations, and the sentence that fixes it

Today's most useful single fact, and it's a *mechanical* failure rather than bad luck.

A 15-turn conversation about Dallas–Chicago reefer volume contains this at turn 3:

> "Don't recommend intermodal for our reefer lanes — we tried it in 2024 and the claims rate was
> unacceptable."

Summarise and you reliably get:

> "Discussed options for the Dallas–Chicago reefer volume, including intermodal."

The constraint isn't weakened, it's **inverted in effect** — a downstream reader now sees intermodal
listed as an option under discussion. Ask what to do with that volume and the system confidently
recommends the one thing it was told not to.

Why, mechanically:

**A summariser optimises for topic coverage.** Trained or prompted, it behaves as if the objective
is *"a shorter text covering what this was about."* A prohibition is not a topic — it is **a modifier
attached to a topic**, one clause qualifying something the summary will mention anyway. Topic-level
compression is exactly the operation that keeps the topic and drops the modifier.

**And the negation carries no length.** "Don't recommend intermodal" versus "recommend intermodal"
is one token in a dozen, so nothing protects it. You met the same asymmetry on Day 3 §2.5, where
"not suitable" sits nearly on top of "suitable" in embedding space. Different mechanism, same
underlying fact: **negation is semantically enormous and syntactically tiny**, and every compression
operation in this stack is biased against it.

The fix is one sentence in the summariser prompt:

```
Preserve all negative constraints, prohibitions, and things explicitly ruled out —
verbatim, with the reason given. Never generalise a prohibition into a topic.
```

You'll measure the delta in the lab and it's large enough to feel like cheating. The general
principle:

> **A compactor preserves what you told it to preserve. Its default is topics.**

Which generalises past negations. Apply the same treatment to whatever your domain can't afford to
lose — in freight that list is short and specific: **prohibitions, exact figures and identifiers,
deadlines, and attribution.** Losing that Ridgeline's FTA was 83% rather than "low" is the
difference between a Lane Review determination (below 85% for two consecutive quarters) and a vague
opinion.

Extraction is weak on negations only *by default*. Give the fact schema an explicit `prohibitions`
field and it becomes the **best** strategy for this failure, because a required schema field is an
instruction the model can't quietly skip — Day 9 §2.7's `already_tried` argument, one layer down.

### 2.8 Lost in the middle, and "effective context"

Day 4 §2.5 gave you the finding: Liu et al. (2023) showed accuracy traces a **U-shape** as the
answer-bearing content moves through a long context — strong at the ends, weakest in the middle, in
their key setting falling *below* closed-book accuracy. Mechanism unsettled; the leading
explanations are recency from causal attention and primacy from attention sinks near the sequence
start. Measure the magnitude on your model rather than quoting a constant.

Today adds the second axis: the effect isn't a number, it's **a surface over (length × position)**,
and mapping it is what the needle experiment does. An illustrative surface for a small local model —
your own will differ, which is the point:

| Length | 0% | 25% | 50% | 75% | 100% | **min** | mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2k | 100 | 100 | 98 | 100 | 100 | **98** | 99.6 |
| 8k | 100 | 96 | 92 | 96 | 100 | **92** | 96.8 |
| 16k | 98 | 90 | 78 | 88 | 98 | **78** | 90.4 |
| 32k | 96 | 74 | 52 | 70 | 94 | **52** | 77.2 |
| 64k | 92 | 58 | 31 | 55 | 90 | **31** | 65.2 |

**Read the `min` column, never the mean.** At 16k the mean is 90.4 — comfortably passing a
mean-based acceptance test — while a fact mid-context is found 78% of the time. You don't control
where the answer lands, so the minimum is your real reliability.

**Advertised context ≠ effective context.** A model sold with 128k may be reliable to 16k on your
task with your documents. RULER (Hsieh et al., 2024) was built to measure that gap and found
effective lengths well short of claimed ones across many models. Your heatmap is the version that
applies to *your* stack, and **the length at which your worst position drops below threshold is a
real engineering constraint you can quote to a client.**

**"Just use a bigger window" is wrong on three independent counts:**

| | Why |
|---|---|
| **Quality** | The U-shape. More context means more middle, and the middle is where accuracy goes |
| **Cost** | Input is billed per step, and an agent loop re-sends the whole context every step |
| **Latency** | Prefill grows with input length — a 90k prompt is slow before one output token exists |

None of which makes stuffing always wrong. On a short single-shot task with a strong long-context
model and a corpus that genuinely fits, it can be right and it saves you a retrieval subsystem. It's
a measurement, not a principle — but it is never *free*, and anyone telling a client it is hasn't
run the heatmap.

### 2.9 Assembly order

Budget decides *what* is in the context; the U-shape decides *where* it sits. **The two ends are
premium real estate**: system prompt and procedural rules at the front, the question last, chunks
score-sorted and alternated front/back per Day 4 §2.5, with episodic summary and semantic facts in
the middle. One caveat: prompt caching keys on a stable prefix, so anything reordered per request
must sit *after* the cached block or you lose the discount.

---

## 3. Worked example — on paper

> **Setup.** The Freight Ops agent. **$3.00/M input, $15.00/M output.** Six tools averaging **200
> tokens** of schema. System prompt + guardrails **1,500**. A 15-turn session, each turn (user +
> assistant) averaging **380 tokens**. Retrieved chunks average **850 tokens**.

**Q1.** An 8-step run: how many tokens of *tool schema alone* does one question pay for, and what
does it cost? Then prune to 3 tools at 180 tokens — new figures, and the monthly difference at
10,000 queries.

**Q2.** Fit §2.4's allocation into a **12,000-token** input budget. Total, overflow, and what gets
evicted under the declared order?

**Q3.** Semantic memory holds **60 entries** that are restatements of **18 distinct facts**. The
free-time fact accounts for **11** of the 60, and all 11 outscore everything else on a detention
query. Recall is `k=5`. Distinct facts reaching the context, with dedupe and without?

**Q4.** Compact the session (5,700 tokens) to **800**. For truncation, summarisation, extraction
(12 facts × 25 tokens), and hierarchical (1 turn verbatim + turns 8–14 summarised to 200 + turns
1–7 extracted to 200): size, compression ratio, and the API cost of compacting. Assume a
summarisation call reads the full 5,700.

**Q5.** The reefer prohibition was stated at turn 3. Which strategy *structurally cannot* preserve
it, which will probably drop it, and which can be made to keep it reliably?

**Q6.** The client's real policy set is **220 documents ≈ 90,000 tokens**. Compare (a) retrieval at
k=4 in one call, (b) stuffing the corpus in one call, (c) stuffing it inside a 6-step agent loop.
Output 300 tokens throughout. Then the monthly figure for (c) at 10,000 queries.

**Q7.** Using §2.8's heatmap and a **90%** threshold: what's your ceiling, and what would a
mean-based test have told you instead?

<details>
<summary><b>Answers — do the arithmetic first</b></summary>

**Q1.** 6 × 200 = **1,200/step**; × 8 = **9,600 tokens**, at $3/M = **$0.0288**. Pruned: 3 × 180 =
540/step × 8 = **4,320** = **$0.01296**, a **55%** cut. At 10,000 queries/month, **$288 → $130** from
deleting three tools — and no description was shortened, so Day 7 §2.7's routing evidence is intact.

**Q2.** Chunks = 8 × 850 = 6,800; total **12,520**; overflow **520**. Rank 1 is the lowest-ranked
chunk: −850 → **11,670**, fitting with 330 spare. **k drops 8 → 7 and nothing else is touched**;
the reportable line is `evicted: chunk[7] (score 0.51), k 8→7`. Without a declared order, the common
framework default — truncate from the oldest end — takes those 520 tokens out of your **system
prompt**.

**Q3.** Without dedupe the top 5 are all one fact → **1 distinct fact** in 5 slots. With dedupe the
store is 18 entries → **5 distinct facts**. **Five times the effective recall, from a similarity
check on the write path** — and it worsens weekly, with no deploy to correlate against.

**Q4.**

| Strategy | Size | Ratio | Compaction cost |
|---|---:|---:|---:|
| Truncation | floor(800/380) = 2 turns = **760** | 7.5:1 | **$0** — no model call |
| Summarisation | **~700** (5,700 in / 700 out) | 8.1:1 | $0.0171 + $0.0105 = **$0.0276** |
| Extraction | 12 × 25 = **300** | 19:1 | $0.0171 + $0.0045 = **$0.0216** |
| Hierarchical | 380 + 200 + 200 = **780** | 7.3:1 | two calls ≈ **$0.040** |

Truncation loses turns 1–13: **4,940 tokens, 86.7% of the session, silently.** And read the cost
column against the ratio — extraction is both the cheapest model-based option and the highest
compression, which is why it's underused relative to how good it is.

**Q5.** **Truncation structurally cannot** — turn 3 is outside a 2-turn window and no prompt fixes
that. **Summarisation will probably drop it**, for the §2.7 reason. **Summarisation with the added
sentence, and extraction with a `prohibitions` field, both keep it** — one instructs, the other
requires. Hierarchical inherits whatever its components do: not safer by construction.

**Q6.**
(a) 1,500 + 3,400 + 60 = 4,960 in, 300 out → **$0.0194**
(b) 91,560 in, 300 out → $0.2747 + $0.0045 = **$0.2792**, **14.4×** (a)
(c) 6 × 91,560 = 549,360 in → ≈ **$1.65 per query**; at 10,000/month, **$16,500** versus about
**$194** for (a). Week 1's retrieval subsystem pays for itself in four days at that volume — before
the quality cost, since 90k of context puts the answer in a middle found half the time.

**Q7.** Ceiling = **8k**, the largest length whose worst position (92%) clears 90. The mean column
says 16k passes at **90.4%**, while a mid-context fact there is found **78%** of the time — one
answer in five missing a fact that was sitting in the prompt, shipped with a green test.

</details>

---

## 4. What people get wrong

**"The model remembers our conversation."**
It's stateless. Your client re-sends the whole array every turn. All continuity is code you wrote.

**"Memory means a vector database."**
Only semantic memory wants one. Working is a list, episodic is a store plus a compactor, procedural
is a versioned text file. Using a vector DB for all four is the day's classic over-engineering.

**"Store every turn in semantic memory."**
It's a fact store, not a log — and it returns the most *relevant* fact, not the most recent.
Recency is episodic's ordering. A question someone asked once is not a fact about the world.

**"Procedural memory is just prompt engineering."**
It's prompt engineering with provenance, versioning, and a regression gate. The gate is the part
that matters — an ungated rules file only grows, and eventually contradicts itself.

**"Tool schemas are a rounding error."**
§3 Q1: 9,600 tokens per question at six tools and eight steps, before anything useful is retrieved.

**"Compaction is free."**
It's an API call in the request path, it adds latency where a user is waiting, and it's
irreversible. Compact on a threshold, cache the result, keep the raw transcript.

**"Summarisation is lossy but roughly faithful."**
It is systematically biased against what you can least afford to lose: prohibitions, numbers, IDs,
attribution. §2.7 — mechanical, not random.

**"A bigger window means we don't need retrieval."**
Three separate costs (§2.8). Sometimes stuffing still wins. It's a measurement, never a default.

**"If it forgot something, increase the window."**
Diagnose first: never written, evicted by the allocator, compacted away, or present but
mid-context and unattended. Four different bugs, and only the last is about size.

---

## 5. The trainer's angle

**The analogy that lands (structure):** a stateless app server behind a load balancer. The messages
array is process RAM, episodic is the session store, semantic is the CMDB, procedural is the
runbook. For an infrastructure audience it lands in fifteen seconds and makes the right thing
obvious — the engineering is in the store and the load policy, not the server.

**The analogy that lands (budget):** an error budget. Fixed quantity, more claimants than supply,
and all the value is in deciding *in advance* who gets cut. Put the allocation table up with its
eviction-rank column and the room stops thinking of context as a container.

**For compaction:** log rotation. Truncation is `logrotate` with no archive — perfect right up until
the incident where you needed last Tuesday.

**The demo that makes it click:** two needle heatmaps side by side, a small local model and a
frontier one, same axes and colour scale. The U-shape becomes *visible*, and the contrast kills both
"just use a better model" and "it's fine at 64k" in one image.

**The demo that's visceral:** the negation loss. Build the 15-turn conversation with the reefer
prohibition at turn 3, compact by summarisation, ask what to do with the Dallas–Chicago reefer
volume, and let the room watch the system recommend intermodal. Then paste one sentence into the
summariser prompt, re-run, watch it refuse and cite the reason. **One sentence, on screen, before
and after** — Day 6 §2.5's measured-fix beat in its purest form.

**The cheap third demo:** ask "what about for reefer?" in turn 3 of a warm session, then cold in a
new one. Coherent in one, meaningless in the other. Ten seconds, and it defines episodic memory
better than a definition does.

**The predictive question before running anything:** *"Six tools, eight steps — how many tokens of
tool schema does this one question pay for?"* Take two guesses. Almost everyone says 1,200: they
multiply by tools and forget to multiply by steps. Then walk §3 Q1.

**The question a sharp student will ask:** *"If the window is 200k, why are you compacting at 12k?"*

> Three reasons, independent. Quality: my heatmap says the worst position on this stack drops below
> 90% past 8k, and I don't control where the answer lands. Cost: an agent loop re-sends the whole
> context every step, so 90k on a 6-step run is half a million input tokens — about $1.65 for one
> question, versus two cents with retrieval. Latency: prefill scales with input length, so a 90k
> prompt is slow before a single output token exists. And a fourth that's about me rather than the
> model — if I didn't decide what went in, I can't debug what went wrong. That said, for a
> single-shot task on a strong long-context model with a corpus that genuinely fits, stuffing can be
> right, and I'd rather measure it than defend a principle. What I won't accept is "it's free."

---

## 6. Self-check

Cover the answers.

1. Where does conversational continuity physically live, and what does the model contribute?
2. Name the four memory types with storage and lifetime for each.
3. What's the read-path difference between episodic and semantic memory, and why does it drive a
   different storage choice?
4. Why is procedural memory the highest-leverage type, and what makes it a system not a habit?
5. What does semantic memory look like after six months without dedupe-on-write, and what does the
   client report?
6. Why is 0.90 a starting point rather than a constant?
7. Give the arithmetic for tool-schema cost across a run, and say why pruning descriptions is
   usually the wrong optimisation.
8. Name the four compaction strategies and state precisely what each loses.
9. Explain mechanically why summarisation drops negations, and give the fix.
10. Why read the `min` column of a needle heatmap rather than the mean?
11. Give the three independent reasons "just use a bigger window" is wrong.
12. Something the user said last week is missing from an answer. Name four distinct causes.

<details>
<summary><b>Answers</b></summary>

1. In your application — the client re-sends the full messages array every request. The model is
   stateless and contributes nothing between calls.
2. Working: messages array, one request. Episodic: message store + summaries, session. Semantic:
   key-value or vector index, indefinite. Procedural: prompt fragments / tool defs / skill files,
   indefinite and versioned.
3. Episodic by recency, semantic by relevance. Relevance ranking is what makes a vector index right
   for semantic and unnecessary for episodic.
4. It changes behaviour on every request for a few hundred tokens, and it compounds — each observed
   failure becomes a permanent fix. It's a system when rules carry provenance, are versioned, and
   additions are gated on the golden set.
5. Full of near-duplicate restatements, so top-k returns one fact several times and effective recall
   falls. Reported as "the AI got worse" — gradual, correlating with no deploy.
6. It's a threshold on a similarity distribution, so it's model- and corpus-specific. Plot known
   duplicates against known distinct pairs and take the separation point.
7. `(system + rules + schemas) × steps` — 6 × 200 × 8 = 9,600 tokens per question. Descriptions are
   the only evidence for a routing decision made every step, so cutting them buys an extra step and
   loses money. Cut whole tools instead.
8. Truncation: everything older, silently. Summarisation: specifics (numbers, IDs, attribution) and
   negations. Extraction: nuance, hedging, the reasoning behind a decision. Hierarchical: complexity
   and two extra calls.
9. The summariser optimises topic coverage; a prohibition is a one-clause modifier on a topic it
   keeps anyway, and the negation carries no length, so nothing protects it. Fix: one sentence
   instructing it to preserve prohibitions verbatim, with reasons.
10. You don't control where the answer lands, so the worst position is your real reliability. The
    mean hides a bad middle — 90.4 over a 78 middle at 16k.
11. Quality (U-shaped attention over a longer middle); cost (context re-sent every agent step);
    latency (prefill scales with input length).
12. Never written; evicted by the allocator; compacted away; or present but mid-context and
    unattended. Only the last is about window size.

</details>

**Scored below 9?** Re-read §2.4 and §2.7. The allocator and the negation experiment are what the
lab makes you build, and it will not re-explain either.

---

## 7. Going deeper

<!--reading:10-->

### If you read one thing this week

**[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)** — Prithvi Rajasekaran, Ethan Dixon, Carly Ryan & Jeremy Hadfield (Anthropic Applied AI team) · essay · ~30 min

The single best framing of §2.5's context budget as a finite resource you spend rather than a window you fill, and it names compaction, note-taking and sub-agent offload as the three strategies with the trade-off each one makes.

### Then, in the order I'd take them

- **[Context Rot: How Increasing Input Tokens Impacts LLM Performance](https://www.trychroma.com/research/context-rot)** — Kelly Hong, Anton Troynikov & Jeff Huber (Chroma) · essay · ~35 min  
  Eighteen models measured across growing inputs, including a needle-in-a-haystack variant with distractors — this is the empirical successor to Day 4's lost-in-the-middle paper and it is what makes 'more context is not free' a number rather than a slogan.
- **[MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560)** — Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica & Joseph E. Gonzalez · paper · ~40 min  
  Read §3 (the memory hierarchy and the paging interface) and skip the evaluations — it is your virtual-memory intuition applied directly to the context window, which is the fastest route from 23 years of systems experience to the working/episodic/semantic split.
- **[Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)** — Anthropic · docs · ~20 min  
  A memory store as a concrete file-backed API (view / create / str_replace / insert / delete) — useful because it forces the question §2.2 raises: which of the four memory types are you actually writing into it, and with what dedupe policy.
- **[Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)** — Anthropic · docs · ~20 min  
  Compaction as a shipped product surface — tool-result clearing, thinking-block clearing and summary-based compaction, each with a different thing it throws away, which is exactly §2.4's 'what each strategy loses' made checkable against a real implementation.

<!--/reading-->

### Also mentioned in this module

- *Lost in the Middle: How Language Models Use Long Contexts* — Liu et al., 2023. Short, and the
  U-shaped figure is the one you'll put on a slide.
- *RULER: What's the Real Context Size of Your Long-Context Language Models?* — Hsieh et al., 2024.
  The systematic version of "advertised ≠ effective." Needle retrieval is the *easiest* of its
  categories, so treat your own heatmap as an optimistic bound.
- *Generative Agents: Interactive Simulacra of Human Behavior* — Park et al., 2023. Its memory
  stream scores retrieval on recency **plus importance plus relevance** — read it as a critique of
  the pure-similarity recall you're building today.
- Greg Kamradt's "needle in a haystack" pressure test (2023) — origin of today's experiment.
- Whatever your provider documents about **prompt caching**, alongside §2.5's trap.

---

**Now go to `labs/DAY_10.md`.** The lab builds on §2.2 and §2.3 (all four memory classes, with
dedupe on the semantic write path), §2.4 (the `ContextBudget` allocator and its eviction report),
§2.6–§2.7 (four compaction strategies, then the negation-loss experiment and the one-sentence fix),
and §2.8 (the needle heatmap and your own reliability ceiling).
