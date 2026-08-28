# Day 04 · Learn — The RAG contract, prompt assembly, and citations you can check

**Read before `labs/DAY_04.md`. Budget 1:15. Pen and paper for §3 — the detention arithmetic matters.**

---

## 1. Where this sits

Day 1 gave you the call. Day 2 gave you a typed, concurrent, retried call. Day 3 gave you a way
to find the relevant paragraph in a corpus.

Today is everything between "here are five chunks" and "here is an answer the ops team will act
on." That gap holds more consequential decisions than any other part of the pipeline, and almost
all of them are invisible in a demo: which chunks, in what order, in what delimiters, with what
refusal instruction, producing what kind of citation.

The specific problem: **your Day 3 retriever will sometimes hand the generator the wrong chunks,
and the generator will answer anyway, confidently, with a citation that looks correct.**
Everything in this module is machinery for making that outcome *detectable* — not preventable,
detectable. That distinction is the difference between a chatbot and a system a client will put
in front of carriers.

---

## 2. The mechanism

### 2.1 The four-clause contract

RAG is not "give the model some context." It's a contract with four clauses, and it's useful
precisely because **every production RAG failure violates exactly one of them.** That makes it a
diagnostic partition, not a slogan. Each clause has an experiment that tells you whether it's
the broken one:

| Clause | The claim | The experiment that tests it |
|---|---|---|
| **1. The answer is in the corpus** | If it isn't, the system says so | Ask a question with no answer in the corpus. Does it refuse? |
| **2. Retrieval surfaces it** | The right chunk is in the top-k | Paste the correct chunk in by hand. Does the answer become right? |
| **3. The prompt makes it usable** | Position, order, format don't destroy it | Same chunks, different order. Does the answer change? |
| **4. The answer is attributable** | Every claim traces to a span | Substring-check every quote. What fraction verify? |

Run those four in order and you'll localise any RAG failure in about ten minutes. Clause 2's
experiment is the highest-leverage one and almost nobody runs it: **if hand-pasting the correct
chunk fixes the answer, you have a retrieval problem and no amount of prompt work will help.** If
it doesn't fix the answer, stop touching the retriever. Write these on an index card.

### 2.2 Clause 1 — refusal is a feature you build, not a behaviour you hope for

The single most common complaint about RAG systems is "it hallucinated." Usually it didn't. It
was handed irrelevant context, given no permission to decline, and asked a direct question. Its
training pushes it hard toward being helpful. **Answering was the highest-probability
continuation because you never made declining available.**

So make it available, and make it machine-checkable:

```
If the context does not contain the answer, reply with exactly: INSUFFICIENT_CONTEXT
```

Three reasons the sentinel beats "say if you don't know". It's **testable** —
`answer.strip() == "INSUFFICIENT_CONTEXT"` is a boolean, whereas "I'm not sure, but it might be
around $65" needs a judge to classify. It's **unambiguous** — a single exact string is a sharper
target than a described behaviour. And it's **routable** — your UI renders a refusal differently
and your application can escalate to a human.

**The tension you must be able to state out loud:** refusal has a precision/recall trade-off.
Tighten it and you get false refusals on answerable questions, which users experience as the
system being useless. Loosen it and you get confident wrong answers, which they experience as
untrustworthy. Those costs aren't symmetric, and which one you'd rather have is a *client*
decision — so ask. For a carrier-facing accessorial quote, a false refusal costs a phone call and
a wrong answer costs a billing dispute: refuse aggressively. For internal exploratory search,
invert it.

This is why Day 5's golden set contains five deliberately unanswerable questions. Without them
you have no refusal metric, and a system scoring 0.95 on faithfulness that never once declines
isn't a good system — it's an untested one.

### 2.3 Clause 2 — recall is the ceiling, and you can compute it

This is arithmetic, not philosophy. If the correct chunk reaches the prompt in 78% of queries,
then **no prompt engineering, no model upgrade, and no reranker downstream of retrieval can push
end-to-end accuracy above 0.78.** The information isn't there.

The composition, roughly:

```
P(good answer) ≈ P(chunk retrieved) × P(model uses it faithfully)
```

At recall@5 = 0.78 and faithfulness-given-retrieval = 0.90, your ceiling is 0.70. So when someone
proposes upgrading the generator model, the honest answer is "that moves the 0.90, which is
already the smaller loss — the 0.78 is where the money is."

And the half that hurts: in the 22% where retrieval missed, what happens? If your refusal path
works you get 22 refusals; if it doesn't you get confident wrong answers. **Clause 1 and clause 2
multiply.** §3 makes you do this with real numbers, because it's the calculation that tells a
client where to spend.

### 2.4 Clause 3 — prompt assembly is a set of decisions, so make them explicitly

The assembled prompt has an anatomy. Decide each part deliberately:

**Delimiters.** Use XML-ish tags, not markdown fences:

```xml
<context>
<doc id="02" title="Detention, Demurrage and Accessorial Charges" section="Detention">
Free time is 2 hours from scheduled appointment time at both origin and destination.
After free time expires, detention accrues at $65 per hour, billed in 15-minute
increments, capped at $650 per event.
</doc>
</context>
```

Two reasons, one obvious and one not. Obvious: your corpus *is* markdown, including fenced blocks
and tables, so fences collide with content and the boundary goes ambiguous. Not obvious: **tags
carry attributes, and attributes are in-band metadata.** The `id="02"` is now inside the model's
context, which is what makes it possible to cite by ID rather than paraphrase a filename. You
cannot ask for `[02]` citations if `02` never appears in the prompt. Same argument for
`section="Detention"`, which disambiguates this chunk from the demurrage chunk two paragraphs
later — Day 3's heading-path trick, working a second time for the same reason.

**Repeat the question after the context.** Costs ~15 tokens, measurably helps on long contexts,
and follows directly from §2.5: the question at the top sets the reading frame, the question at
the bottom sits in the highest-attention position immediately before generation.

**Rules traceable to observed failures.** Two rules earn their place today, both from Day 3:

```
- Never state a number that does not appear verbatim in the context.
- Include the condition attached to a number (e.g. free time) whenever one exists.
```

That second one exists because you watched a chunk boundary sever `$65 per hour` from `after
2 hours of free time`. **A prompt full of generic pieties — "be accurate," "be helpful" — is a
prompt nobody maintains and nobody can defend in review.** Every rule should have an incident
behind it. When a client asks "why is this line here," you should have an answer.

### 2.5 Lost in the middle

Liu et al. (2023) measured a clean, reproducible effect: when the answer-bearing document is
placed at varying positions in a long context, accuracy traces a **U-shape** — highest when the
relevant content is at the very start or very end, and lowest in the middle. In their key
setting the middle-position accuracy fell below the model's *closed-book* accuracy with no
retrieved documents at all.

Be honest about the mechanism, because you'll be asked. **This is an empirical finding, not a
derived property of transformers.** The leading explanations are recency from causal attention
and primacy from attention sinks near the sequence start, plus training data where important
content clusters at document boundaries. Nobody has a settled account. Newer long-context models
are measurably better and none are immune, so treat the magnitude as something you measure on
*your* model rather than a constant.

The mitigation is cheap and deterministic. Sort your k chunks descending by score, then place
them alternately front and back, working inward:

```
scores:   c1 0.847  c2 0.812  c3 0.771  c4 0.734  c5 0.702  c6 0.498

place c1 → front:  [c1]
place c2 → back:   [c1, c2]
place c3 → front:  [c1, c3, c2]
place c4 → back:   [c1, c3, c4, c2]
place c5 → front:  [c1, c3, c5, c4, c2]
place c6 → back:   [c1, c3, c5, c6, c4, c2]

final order: c1, c3, c5, c6, c4, c2
```

Best and second-best occupy the two high-attention positions; the weakest get buried where
degradation costs least. Note this is a *reordering*, not a filter — same tokens, same price. It
is the cheapest quality improvement in the pipeline.

**And the better fix is usually to reduce k.** Three good chunks routinely beat six mediocre ones,
because the mediocre three don't merely fail to help — they dilute. Which brings us to:

### 2.6 k is a parameter with three costs

Recall rises monotonically with k. Everything else gets worse:

| Cost of raising k | Magnitude | Notes |
|---|---|---|
| Tokens / money | Linear, and small | ~900 tokens per chunk; §3 quantifies it. Usually the *weakest* argument |
| Latency | Linear on input processing, small | Day 1: input is processed largely in parallel |
| **Dilution** | Non-linear, and large | More distractors, more middle positions, more chances to cite the wrong doc |

The last row is why "just set k=20 to be safe" is wrong: **every irrelevant chunk you add is
another plausible thing for the model to answer from.** Doc 02 contains both detention free time
(2 hours) and demurrage free time (4–5 days). Retrieve both for "how many days of free time do I
get?" and you've handed the model a choice it will make silently.

So k gets chosen by measurement, not taste — which is tomorrow. Today, pick 5, note that you
picked it arbitrarily, and don't pretend otherwise.

### 2.7 Clause 4 — three grades of citation

| Grade | What it is | Verifiable? |
|---|---|---|
| **Bronze** | "Source: doc 02" appended, by you or the model | No. The model attaches whatever ID looks right |
| **Silver** | Model emits `[02]` inline; you check `02` was in the retrieved set | Partly — proves the doc was available, not that it was used |
| **Gold** | Model emits a verbatim `evidence_quote` per claim; you assert it's a substring of that chunk | Yes, automatically, in microseconds, with no LLM |

Build Gold. It costs about 40 output tokens per answer and gives you a hallucination detector
that runs free in CI. On Day 5 it becomes a headline row on your scorecard; on Day 6 it becomes
the green checkmark clients remember.

Same caveats as Day 2 §2.5, and they matter more here. **Normalise before comparing** — smart
quotes and collapsed whitespace produce false negatives. **Verified ≠ supported** — Gold proves
provenance; whether the quote *establishes* the claim is a faithfulness judgement, which is Day 5.
And **add one free second check**: if the answer states a number, assert that number appears in
at least one verified quote. That catches the specific failure where the model quotes the
free-time sentence and then states a fabricated rate.

---

## 3. Worked example — on paper

From `data/corpus/02_detention_and_accessorials.md`:

> Free time is **2 hours** from scheduled appointment time at both origin and destination.
> After free time expires, detention accrues at **$65 per hour**, billed in 15-minute
> increments, capped at **$650 per event**.

**Q1.** A driver waits 5 hours at destination. Billable increments and dollar amount?

**Q2.** A different driver waits 4 hours 50 minutes. Same two numbers. Compare to Q1.

**Q3.** At what total wait time does the $650 cap start to bind?

**Q4.** A chunk boundary severed the free-time sentence from the rate sentence. Only the rate
chunk is retrieved. What does the model answer for the 5-hour wait, and what's the error? If ops
quotes this figure on 360 detention events a month, what's the monthly exposure?

**Q5.** Your scorecard says recall@5 = 0.78, faithfulness-given-retrieval = 0.90, and refusal
accuracy on unanswerable questions = 0.40. Out of 100 typical queries, how many produce a
correct answer, how many produce a refusal, and how many produce a confident wrong answer?

**Q6.** k=6, scores `c1 0.847, c2 0.812, c3 0.771, c4 0.734, c5 0.702, c6 0.498`. Give the
assembled order under the §2.5 reordering.

**Q7.** Chunks average 900 tokens. Compare k=5 to k=12 on input tokens per query and monthly
cost at 10,560 queries and $0.15 per 1M input tokens. Is cost a good argument for keeping k
small?

<details>
<summary><b>Answers — work them first</b></summary>

**Q1.** 5 h = 300 min. Less 120 min free = 180 billable min = **12 increments**. Each increment
is $65/4 = $16.25. 12 × $16.25 = **$195**.

**Q2.** 290 − 120 = 170 billable min. 170/15 = 11.33, increments round up → **12 increments =
$195.** Identical to Q1. Ten minutes of the driver's life are free and the next second costs
$16.25 — that's what "billed in 15-minute increments" means, and it's exactly the detail a
carrier's billing team will challenge you on.

**Q3.** $650 / $16.25 = 40 increments = 10 billable hours, plus 2 free = **12 hours total wait**.
Beyond that, detention is free to the shipper — another condition a severed chunk loses.

**Q4.** Without the free-time condition the model computes 5 × $65 = **$325** against an actual
**$195**: an over-quote of **$130 per event**, or **$46,800/month** at 360 events. Status 200. No
exception. Nothing in the logs.

That's the number for the slide. Not "chunking is important" — *forty-six thousand eight hundred
dollars a month, from one chunk boundary.*

**Q5.** Of 100 queries, 78 retrieve correctly → 0.90 × 78 = **70 correct** and **8 unfaithful**.
The 22 misses hit the refusal path, which fires correctly 40% of the time → **~9 refusals** and
**~13 confident wrong answers**.

Totals: **70 correct, 9 refusals, 21 wrong-and-confident.** One query in five produces a
plausible, cited, wrong answer and nothing reports it. Note which lever is biggest: taking the
refusal path from 0.40 to 0.90 converts 11 wrong answers into refusals without touching retrieval
at all, and refusals are cheap where wrong answers are expensive. **Clause 1 is usually the
cheapest fix on the board and the one everyone skips.**

**Q6.** `c1, c3, c5, c6, c4, c2` — best at the front, second-best at the back, weakest buried.

**Q7.** k=5: 4,500 tokens. k=12: 10,800. Delta 6,300/query = $0.000945 → **$9.98/month**.

So no — **cost is a terrible argument for small k**, and making it in front of a client spending
$200K on the engagement makes you look like you're optimising the wrong thing. The real argument
is dilution (§2.6): seven extra chunks add distractors and middle positions, and the measured
faithfulness drop dwarfs ten dollars. Make the quality argument; keep the cost number in your
pocket for when someone asks.

</details>

---

## 4. What people get wrong

**"It hallucinated."**
Usually it was handed bad context and given no way to decline. Check clause 1 before you blame
the model. "It hallucinated" is a diagnosis; you haven't earned it until the refusal path works.

**"More context is safer."**
More context is more distractors, more middle, and more chances to cite the wrong document.
Recall goes up, faithfulness goes down, and only one of those is on your dashboard.

**"The citation proves the answer is right."**
A Bronze citation proves nothing. Gold proves the quoted span exists. Neither proves the span
supports the claim.

**"If retrieval is bad, use a better model."**
Recall is a hard ceiling (§2.3). A better generator moves the second factor, which is already
the larger of the two. Compute the product before you spend.

**"Lost-in-the-middle is fixed in modern long-context models."**
Reduced, not eliminated, and the magnitude varies enough by model that you measure yours rather
than quote a paper. Anyone claiming it's solved should be asked for their positional sweep.

**"Prompt engineering will fix this."**
Sometimes. But if the correct chunk never reached the prompt, or a boundary severed the condition
from the number, the information isn't in the context and no instruction conjures it. Run clause
2's paste-it-in experiment first — ninety seconds, and it tells you which half of the pipeline to
work on.

**"We'll add citations later."**
Citations change the prompt, the schema and the output format, so every eval number recorded
before them is incomparable to every number after. Build Gold on day one.

**"k=5 because that's what the tutorial used."**
It's a free parameter with a measurable optimum that differs by corpus and question type.
Choosing it by eval is tomorrow; choosing it by vibes and then defending the vibe is the failure.

---

## 5. The trainer's angle

**The analogy that lands:** the four clauses are a request path, and you already debug request
paths for a living.

| Clause | Its equivalent in a system you've run |
|---|---|
| 1. Answer is in the corpus | Is the record in the database at all? |
| 2. Retrieval surfaces it | Does the query hit the right index — or table-scan and time out? |
| 3. The prompt makes it usable | Did the serialiser mangle it between the store and the response? |
| 4. Attributable | Can you trace this response back to the row that produced it? |

Clause 4 is the one that converts a room. **A Gold citation is a correlation ID for a factual
claim.** Everyone in an operations org already believes an untraceable response is an
unsupportable one; you're saying the same discipline applies to a model's output. That lands in a
way "grounding" never does.

**The demo that makes it click:** the k=3 / k=12 experiment. Ask a question the system answers
correctly at k=3, re-run at k=12 with the correct chunk forced into position 6, and watch it get
the answer wrong while the correct text is *visibly on screen inside the prompt.* Then turn on
the reordering and watch it come back. **You have just shown a room that a model can fail to use
information it was given** — a fact almost nobody there believed thirty seconds earlier, and it
justifies the whole concept of prompt assembly in one move. Record the terminal output; you'll
use it for years.

**The predictive question to ask first:** *"I'm about to ask this system about our drone delivery
policy. There's nothing about drones in the corpus. What does it say?"* Take two guesses before
running it — half the room says "it'll say it doesn't know" — then run it without the refusal
instruction.

**The question a sharp student will ask:** *"This corpus is thirty pages. Why not just put the
whole thing in the context window and skip retrieval entirely?"* This is a genuinely good
question and the honest answer wins you more credibility than a defensive one:

> For a thirty-page corpus you're right, and you should. Long-context stuffing beats naive RAG on
> small corpora and the field broadly agrees; with prompt caching, the cost argument gets weaker
> every quarter. Four things bring retrieval back. Volume — you pay the full corpus on every
> query, and inside an agent loop that's every *step*. Latency, for the same reason.
> Lost-in-the-middle, which worsens as context grows. And attribution — with retrieval I have a
> specific chunk to substring-check against; with thirty pages in context, "cite your source"
> loses the granularity that makes verification cheap. But the real reason is the fifth: corpora
> grow. You're building for the version with four thousand documents, and the architecture that
> gets you there isn't the one that fits today's thirty pages.

---

## 6. Self-check

Cover the answers.

1. State the four clauses of the RAG contract.
2. For each clause, name the experiment that tells you it's the broken one.
3. Why is `INSUFFICIENT_CONTEXT` better than "say if you don't know"? Give three reasons.
4. Why does a refusal threshold have a trade-off, and who decides where to set it?
5. Recall@5 is 0.78. What is the maximum possible end-to-end accuracy, and why?
6. Why do XML-ish tags beat markdown fences for delimiting context? Two reasons.
7. What is lost-in-the-middle, and is the mechanism understood?
8. Give the reordering for k=5 with descending scores c1..c5.
9. Name the three costs of raising k. Which is largest, and which is the weakest argument?
10. Bronze, Silver, Gold — define each and say what each proves.
11. A Gold citation verifies. Name two things that can still be wrong.
12. A model gives a wrong detention figure. Give the order of checks you run.

<details>
<summary><b>Answers</b></summary>

1. The answer is in the corpus (or the system refuses); retrieval surfaces it; the prompt makes
   it usable; the answer is attributable.
2. Ask an unanswerable question — does it refuse? Paste the correct chunk in by hand — does the
   answer become right? Reorder the same chunks — does the answer change? Substring-check every
   quote — what fraction verify?
3. Machine-checkable string equality; unambiguous as an exact target; routable by the app and UI.
4. Tighter means false refusals on answerable questions; looser means confident wrong answers.
   The costs aren't symmetric, and which hurts more depends on the use case — so the client
   decides, and you make sure they're asked.
5. 0.78. In the other 22% the information is absent from the prompt, and nothing downstream of
   retrieval recovers it.
6. Your corpus *is* markdown, so fences collide with content. And tags carry attributes, putting
   `doc_id` and heading path in-band so the model can cite by ID.
7. Accuracy is highest when relevant content sits at the start or end of a long context and
   lowest in the middle — a U-shape (Liu et al., 2023). The mechanism isn't settled; recency from
   causal attention and primacy from attention sinks are the leading explanations. Measure yours.
8. c1, c3, c5, c4, c2.
9. Tokens (linear, small), latency (linear, small), dilution (non-linear, large). Dilution is
   largest; cost is the weakest argument and you'll lose the room making it.
10. Bronze: an appended source label — proves nothing. Silver: an inline `[doc_id]` checked
    against the retrieved set — proves the doc was available. Gold: a substring-checked verbatim
    quote — proves the span exists in that chunk.
11. The quote may not support the claim, and the answer may state a number appearing in no
    verified quote. Also, normalisation differences cause false negatives — a low verification
    rate can be a bug in your checker.
12. Clause 1 (did it refuse when it should?), then 2 (paste the chunk in — does it fix?), then 3
    (reorder / reduce k), then 4 (do the quotes verify?). Cheapest diagnostic first.

</details>

**Scored below 8?** Re-read §2.1 and §2.3. The lab's three deliberate breakages are each a
clause violation, and if the partition isn't solid you'll debug them by guessing.

---

## 7. Going deeper

<!--reading:04-->

### If you read one thing this week

**[Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)** — Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni & Liang (2023) · paper · ~35 min

Short, and the U-shaped curve figures are the entire argument for §2.5's ordering decision; do not skip the closed-book comparison, which is the part people forget when they claim more context is always better.

### Then, in the order I'd take them

- **[Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)** — Lewis, Perez, Piktus, Petroni, Karpukhin, Goyal, Küttler, Lewis, Yih, Rocktäschel, Riedel & Kiela (NeurIPS 2020) · paper · ~45 min  
  The paper that named the thing — read §2 and note how different the original formulation (a trained, differentiable retriever) is from the prompt-assembly pipeline you are building, because that gap is a question you will be asked in a room.
- **[Enabling Large Language Models to Generate Text with Citations (ALCE)](https://arxiv.org/abs/2305.14627)** — Tianyu Gao, Howard Yen, Jiatong Yu & Danqi Chen (2023) · paper · ~40 min  
  The academic treatment of §2.7's citation grades — read the citation-recall and citation-precision definitions in particular, since those two metrics give you the vocabulary to argue that Bronze citations are not citations.
- **[Citations](https://platform.claude.com/docs/en/build-with-claude/citations)** — Anthropic · docs · ~25 min  
  A shipped implementation of Gold citations from §2.7 — character-index spans back into the source document rather than model-generated reference numbers, which is precisely the verifiability property you are building by hand in the lab.
- **[Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997)** — Gao, Xiong, Gao, Jia, Pan, Bi, Dai, Sun, Wang & Wang (2023) · paper · ~30 min  
  Skim it as a map, not a reading list — the naive/advanced/modular taxonomy and its figures give you shared vocabulary for a client design review, and it previews where Day 8 goes.

<!--/reading-->

### Also mentioned in this module

- *Self-RAG* — Asai et al. (2023). One rigorous approach to the refusal problem in §2.2.

---

**Now go to `labs/DAY_04.md`.** The lab is built on §2.1 (the contract — your three breakages are
clause violations 2, 3 and 3 again), §2.4 (you're assembling the prompt by hand), §2.5 (Break 3
is the positional experiment), and §2.7 (build Gold, not Silver).
