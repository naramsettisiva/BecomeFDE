# Day 03 · Learn — Embeddings, distance, and why retrieval misses

**Read before `labs/DAY_03.md`. Budget 1:15. Pen and paper for §3 — genuinely, this one has arithmetic.**

---

## 1. Where this sits

Day 1 you learned what a model call is. Day 2 you learned to get structured, reliable output
from one. Both assumed you already knew *which text to send*.

Today is that question. You have ten policy documents and a user asks "how much detention per
hour?" — which paragraph do you put in the prompt? You can't send all ten (cost, and the
lost-in-the-middle effect from Day 1). You need to *find* the relevant piece.

Keyword search would work for that particular query. It fails on "what do I get charged for
sitting at the dock" — same question, zero shared words with the answer. Solving that is what
embeddings are for.

**This is the most important module in Week 1, and the one where a shallow understanding does
the most damage later.** Every failing RAG system you get parachuted into will be failing at
retrieval, and "embeddings capture semantic meaning" is not a sentence you can debug with.

---

## 2. The mechanism

### 2.1 What an embedding is

An embedding model takes text and returns a fixed-length list of numbers:

```
"Detention accrues at $65 per hour"  →  [0.021, -0.113, 0.087, ..., 0.004]
                                          └─────── 1024 numbers ────────┘
```

Same length regardless of input length. A word, a sentence, a paragraph — all become a vector of
the same dimensionality (768, 1024, 1536, or 3072, depending on the model).

That vector is a **position in a very high-dimensional space**. And the property the model was
trained to have is:

> Texts that mean similar things land near each other.

### 2.2 The question everyone asks: what does one dimension mean?

**Nothing individually.** This is the honest answer and it's worth being precise about, because
half the confusion in this topic comes from people expecting dimension 47 to be "formality" or
"is about money."

Here's why. The model is a neural network trained with an objective like: *given a query and its
correct answer, and a batch of wrong answers, make the query vector close to the right one and
far from the wrong ones* (contrastive learning). Nothing in that objective assigns meaning to any
individual coordinate. What gets learned is a **geometry** — the whole arrangement carries the
information, distributed across all 1024 numbers.

A useful analogy from your world: think of a consistent-hashing ring. No single bit of a node's
hash "means" anything. The value is entirely in the *relative positions* — who lands near whom.
Embeddings are that, with 1024 axes and a meaningful notion of distance.

So: **dimensions are not features. Direction and distance are the only things that carry meaning.**

### 2.3 Measuring distance — the three metrics

Given two vectors **a** and **b**:

```
dot(a,b)       = Σ aᵢbᵢ                    magnitude AND angle
cosine(a,b)    = dot(a,b) / (|a| · |b|)    angle only — magnitude normalised away
euclidean(a,b) = √(Σ (aᵢ-bᵢ)²)             straight-line distance
```

Cosine ranges from −1 (opposite) through 0 (unrelated) to 1 (identical direction). It's the
default in this field because **document length shouldn't determine relevance**, and raw dot
product would let a long document outrank a short precise one purely by having a bigger magnitude.

**The relationship worth deriving yourself** (you'll do this in §3): if the vectors are
**unit-normalised** — meaning |a| = |b| = 1, which most modern embedding models output by
default — then:

```
euclidean(a,b)² = 2 − 2·cosine(a,b)
```

Which means euclidean distance is a strictly decreasing function of cosine similarity, so
**they produce identical rankings.** The choice between them is then purely about convention and
what your vector database expects.

That fact resolves a question you will be asked in a design review — *"should we use cosine or
L2?"* — and the correct answer is *"for normalised vectors it doesn't affect ranking; here's when
it would matter."* It matters only when magnitude carries signal, which for a few models it does.

**Check whether your vectors are normalised.** If they are, dot product and cosine are the same
operation, which is why many vector databases default to "inner product" and everyone finds it
confusing.

### 2.4 The distinction that explains most retrieval failures

This is the heart of today, and the part almost no tutorial states plainly.

Embeddings capture **topical** similarity far more strongly than **propositional** similarity.

Consider three sentences:

```
A: "Detention accrues at $65 per hour after 2 hours of free time."
B: "Drivers are compensated for waiting time once the free period expires."
C: "Demurrage applies to containers held at the marine terminal."
```

A and B are **paraphrases** — same proposition, different words.
A and C are **topically related** — both freight accessorial charges — but different propositions.

You would hope sim(A,B) > sim(A,C). Very often you will measure sim(A,C) ≥ sim(A,B), because
A and C share dense domain vocabulary while A and B share almost none.

**This single fact is why RAG retrieves the right document and the wrong paragraph.** The
embedding pulls you into the right neighbourhood of the corpus. It is much weaker at picking the
specific claim within that neighbourhood.

You'll measure this yourself in the lab. When you do, it stops being something you read and
becomes something you know.

### 2.5 Where dense retrieval fails outright

Beyond the topical/propositional issue, there are failure classes where embeddings are simply
the wrong tool:

| Failure | Why | Example from your corpus |
|---|---|---|
| **Rare tokens / acronyms** | Under-represented in training; the vector is close to arbitrary | `TONU`, `EDI 214`, `INC-4471` |
| **Exact identifiers** | Embeddings don't do exact match, ever | `SHP-202608-0041729` |
| **Negation** | "not X" embeds very close to "X" — the negation is a small perturbation | "lanes where intermodal is *not* suitable" |
| **Numeric comparison** | No magnitude reasoning in the geometry | "carriers scoring below 70" |
| **Vocabulary mismatch** | This is the one embeddings *do* fix | "sitting at the dock" → detention ✓ |

The negation one deserves a moment because it's genuinely counter-intuitive: to an embedding
model, "intermodal is suitable for this lane" and "intermodal is not suitable for this lane" are
nearly the same point in space. One token changed out of a dozen. The meaning inverted; the
geometry barely moved.

The fixes — BM25 for rows 1–2, metadata filtering for rows 3–4 — are Day 14. Today you just need
to see the failures clearly, because a system that fails these and you don't know why is a system
you'll blame the model for.

### 2.6 Chunking is a retrieval decision

You can't embed a whole document usefully. A 3,000-word policy averaged into 1024 numbers is a
vector that's vaguely near everything and sharply near nothing. So you split it into chunks and
embed each.

**How you split determines what can be found.** Two failure directions:

- **Chunks too small** → the answer is split across chunk boundaries. Neither half scores well
  alone, and even if one is retrieved it's incomplete.
- **Chunks too large** → the embedding averages several topics. It matches everything weakly and
  nothing strongly.

The strategies, and the trade-off you must be able to state out loud:

| Strategy | How | Good for | Breaks on |
|---|---|---|---|
| **Fixed-size + overlap** | Every N characters, with N/10 overlap | Uniform prose | Tables, lists, code — splits mid-row |
| **Recursive character** | Split on `\n\n`, then `\n`, then `. `, then chars | General default | Still blind to document meaning |
| **Heading-aware** | Split on markdown/HTML structure | Structured docs like ours | Documents with no structure |
| **Semantic** | Split where consecutive-sentence embedding similarity drops | Long unstructured prose | Slow and costs an embedding pass |
| **Whole-document** | No splitting | Tiny corpora, long-context models | Cost per query, lost-in-the-middle |

**The specific failure to look for today.** Open `data/corpus/02_detention_and_accessorials.md`.
The rule is:

> Free time is **2 hours** from scheduled appointment time at both origin and destination.
> After free time expires, detention accrues at **$65 per hour**…

A 500-character fixed chunker will, depending on offset, cut between those two sentences. Now
you have a chunk saying "$65 per hour" with no free-time condition attached. Retrieved on its
own, it produces a *confidently wrong answer* — the model will tell someone they owe $325 for a
5-hour wait instead of $195.

**No amount of prompt engineering fixes that**, because the correct information was never in the
context. This is clause 2 of the RAG contract you'll meet tomorrow, and it's why chunking is an
architecture decision rather than a preprocessing detail.

### 2.7 The technique worth more than it looks: heading-path prefixing

Before embedding a chunk, prepend its structural location:

```
Raw chunk:
  "Free time is 4 calendar days at inland ramps, 5 at marine terminals..."

Prefixed:
  "Detention, Demurrage and Accessorial Charges > Demurrage > Free time is 4
   calendar days at inland ramps, 5 at marine terminals..."
```

The prefixed version embeds much closer to the query "how much free time for containers" because
the disambiguating context — *demurrage*, not detention — is now inside the text being embedded.

Costs nothing. Requires no extra model call. Routinely worth several points of recall. On Day 14
you'll meet the fully-general version of this idea (contextual retrieval, using a model to write
the prefix) — the heading-path trick is the free approximation.

### 2.8 Why production indexes are approximate

Brute-force search compares the query against every vector: O(N·d). At 10,000 vectors × 1024
dimensions that's ~10M multiply-adds per query — a few milliseconds, entirely fine. At 50 million
vectors it's not.

So production systems use an **approximate nearest neighbour** index. The dominant one is
**HNSW** (Hierarchical Navigable Small World), and the idea is one you'll recognise:

Build a layered graph. The top layer is sparse with long-range links; lower layers get denser.
Start at the top, greedily walk toward the query, drop a layer, repeat. It's a skip list, in
high-dimensional space.

The three knobs and what they cost:

| Knob | Effect | Cost |
|---|---|---|
| `M` — edges per node | Higher = better recall | More memory |
| `ef_construction` — build-time search width | Higher = better graph | Slower index build |
| `ef_search` — query-time search width | Higher = better recall | Slower queries |

**You are trading recall for latency.** The index can miss a true nearest neighbour — that's what
"approximate" means. So when a client asks "why didn't it find that document?", the answer might
be your embeddings, your chunking, *or* `ef_search` being too low. Being able to name that third
possibility, and to measure it against a brute-force ground truth, is FDE-grade knowledge.

This is why today's lab makes you build brute-force search first: **it's the ground truth you
measure the approximation against.**

---

## 3. Worked example — on paper

Small numbers, done by hand. Two dimensions instead of 1024, but every property is the same.

**Given:**
```
q = (3, 4)        the query
a = (6, 8)        document A
b = (4, 3)        document B
c = (-3, -4)      document C
```

**Q1.** Compute |q|, |a|, |b|, |c|. (Magnitude = √(x² + y²).)

**Q2.** Compute dot(q,a), dot(q,b), dot(q,c).

**Q3.** Rank a, b, c by **dot product**. Which wins?

**Q4.** Compute cosine(q,a), cosine(q,b), cosine(q,c). Rank them.

**Q5.** The rankings from Q3 and Q4 differ. Explain in one sentence *why*, and say which you'd
want for document retrieval.

**Q6.** Normalise q and a to unit length. Then verify numerically that
`euclidean(q̂,â)² = 2 − 2·cosine(q̂,â)`.

**Q7.** What does vector c represent, semantically, relative to q?

<details>
<summary><b>Answers — do them first, the arithmetic is the point</b></summary>

**Q1.** |q| = √(9+16) = **5** · |a| = √(36+64) = **10** · |b| = √(16+9) = **5** · |c| = √(9+16) = **5**

**Q2.** dot(q,a) = 3·6 + 4·8 = 18+32 = **50** · dot(q,b) = 3·4 + 4·3 = 12+12 = **24** ·
dot(q,c) = 3·(−3) + 4·(−4) = −9−16 = **−25**

**Q3.** **a (50) > b (24) > c (−25).** A wins decisively.

**Q4.** cos(q,a) = 50/(5·10) = **1.0** · cos(q,b) = 24/(5·5) = **0.96** ·
cos(q,c) = −25/(5·5) = **−1.0**
Ranking: **a (1.0) > b (0.96) > c (−1.0)** — same order, but look at the *gap*.

**Q5.** `a` is exactly the same *direction* as q (a = 2q) — cosine says they're identical, 1.0.
Dot product ranks it far above b mainly because a is twice as long. Under cosine, a and b are
nearly tied (1.0 vs 0.96) because they point almost the same way.

For retrieval you want **cosine** — a document shouldn't rank higher merely for being longer.
That's the whole argument, in two numbers.

**Q6.** q̂ = (0.6, 0.8), â = (0.6, 0.8) — identical after normalising, since a = 2q.
euclidean(q̂,â) = 0, so LHS = 0. cosine = 1, so RHS = 2 − 2(1) = 0. ✓

Try it with b too: b̂ = (0.8, 0.6). euclidean(q̂,b̂)² = (0.6−0.8)² + (0.8−0.6)² = 0.04 + 0.04 = **0.08**.
And 2 − 2(0.96) = **0.08**. ✓

**Q7.** c = −q. It points in exactly the opposite direction, cosine −1.0. In a real embedding
space you essentially never see this — real text vectors cluster in a relatively narrow cone, and
typical "unrelated" pairs score around 0.3–0.6, not 0. Which leads directly to the next point…

</details>

**The consequence of that last answer**, and it's important: **a similarity score of 0.82 means
nothing on its own.** Scores aren't calibrated, they aren't comparable across embedding models,
and the useful range is much narrower than [−1, 1]. The only way to choose a threshold is to plot
the score distribution for known-relevant pairs against known-irrelevant pairs and find where
they separate. You'll do exactly that in the lab.

---

## 4. What people get wrong

**"Embeddings understand meaning."**
They encode a geometry trained so that similar things land nearby. "Understanding" implies
propositional grasp, and §2.4 is the counter-example: a paraphrase can score *lower* than a
topically-adjacent but different claim.

**"Dimension 200 must encode something."**
Individual dimensions carry no interpretable meaning. Only relative position does.

**"Cosine is better than Euclidean."**
For normalised vectors they produce identical rankings. The real question is whether magnitude
carries signal for your model.

**"A score of 0.85 is good."**
Meaningless without the distribution. Plot relevant-vs-irrelevant and find the separation.

**"I can compare scores from two embedding models."**
No. Different models, different geometries, different score distributions. You can compare
*rankings* via a metric like nDCG. You cannot compare raw similarity values.

**"Bigger embeddings are better."**
Often marginal. Titan V2 offers 256/512/1024 and you'll measure the difference on Day 3's AWS
lane — smaller vectors are cheaper to store and faster to scan, frequently at very little recall
cost. Measure, don't assume.

**"Chunking is preprocessing."**
Chunking determines what is findable. It is the highest-leverage retrieval decision you make and
it happens before any query is ever issued.

**"If retrieval missed it, add more context."**
Sometimes. But if the chunk boundary severed a condition from its number, more context of the
same kind won't help — you need different chunking. Diagnose before you increase k.

---

## 5. The trainer's angle

**The analogy that lands:** a library where books are shelved by what they're *about* rather than
by title, and you find things by walking to the right shelf. It gets across the right idea
(proximity by meaning) *and* sets up the failure honestly — you get to the right shelf and still
have to find the right page. Which is exactly the topical-vs-propositional gap.

**The demo that makes it click:** compute the A/B/C similarities from §2.4 live, on screen, with
your own corpus. When the paraphrase scores *lower* than the topically-related-but-different
sentence, the room goes quiet. That single measurement teaches more than twenty minutes of
explanation, and it's honest in a way that "embeddings capture semantics" is not.

**Your second demo:** open the detention document, show where a 500-char boundary falls, show
"$65 per hour" severed from "after 2 hours free time", then show the model confidently
over-billing by $130. It makes chunking feel consequential rather than fiddly.

**The predictive question to ask before running anything:** *"I'm about to compare the query
'TONU' against this corpus. What do you think comes back?"* Take two guesses. Then run it and
watch dense retrieval fail on a bare acronym. Prediction-before-observation roughly doubles
retention and it costs you thirty seconds.

**The question a sharp student will ask:** *"If embeddings are so weak at exact matches and
negation, why does anyone use them instead of keyword search?"* Have this ready:

> Because keyword search fails the vocabulary-mismatch case completely, and that's most real user
> queries. "What do I get charged for sitting at the dock" shares no terms with the detention
> policy. Dense retrieval finds it; BM25 returns nothing. The mature answer is that you use both —
> hybrid retrieval, which is Day 14 — and each covers the other's failure mode. Anyone selling you
> one as a replacement for the other is selling you something.

---

## 6. Self-check

1. What does an embedding model return, and does its size depend on input length?
2. What does an individual dimension of an embedding mean?
3. Write the formula for cosine similarity.
4. For unit-normalised vectors, how do Euclidean and cosine rankings relate? Why?
5. Explain topical vs. propositional similarity, and what it predicts about RAG failures.
6. Name three query types where dense retrieval fails, and say why for each.
7. Why does "not suitable" embed close to "suitable"?
8. Chunk too small vs. chunk too large — what breaks in each direction?
9. What does heading-path prefixing do, and why is it free?
10. What do `M`, `ef_construction`, and `ef_search` trade against each other?
11. Is a cosine score of 0.85 good? Defend your answer.
12. Why does today's lab make you write brute-force search before touching a vector database?

<details>
<summary><b>Answers</b></summary>

1. A fixed-length vector of floats (768/1024/1536/3072 depending on model). Size is fixed by the
   model, independent of input length.
2. Nothing interpretable. Meaning lives in relative position across all dimensions, because the
   training objective constrains geometry, not coordinates.
3. cosine(a,b) = (a·b) / (|a|·|b|).
4. Identical rankings, because euclidean² = 2 − 2·cosine for unit vectors — a strictly decreasing
   function, so it can't reorder anything.
5. Topical = same subject area. Propositional = same claim. Embeddings capture topical much more
   strongly, which is why RAG lands in the right document and the wrong paragraph.
6. Rare tokens/acronyms (near-arbitrary vectors); exact IDs (embeddings never do exact match);
   negation (tiny perturbation, inverted meaning); numeric comparison (no magnitude reasoning).
   Any three.
7. One token changed out of many — the geometry barely moves while the meaning inverts.
8. Too small: the answer splits across boundaries and no chunk scores well alone. Too large: the
   embedding averages multiple topics and matches nothing sharply.
9. Prepends the structural path into the chunk text before embedding, so disambiguating context is
   part of what gets embedded. Free because the headings already exist — no extra model call.
10. `M` = edges per node (recall vs. memory); `ef_construction` = build width (graph quality vs.
    build time); `ef_search` = query width (recall vs. query latency). All trade recall against a
    resource.
11. Meaningless in isolation. You need the distribution of relevant vs. irrelevant pairs *for that
    model on that corpus*, and you pick the threshold where they separate.
12. It's the ground truth. Approximate indexes can miss true neighbours, and without an exact
    baseline you cannot tell an approximation miss from an embedding or chunking problem.

</details>

**Scored below 8?** Re-read §2.4 and §2.6. Those two sections are the ones the lab and the whole
of Day 4 are built on.

---

## 7. Going deeper (optional)

- *Efficient and robust approximate nearest neighbor search using HNSW graphs* (Malkov &
  Yashunin, 2016) — read §3 and the figures. The skip-list intuition is right there.
- *Lost in the Middle: How Language Models Use Long Contexts* (Liu et al., 2023) — you'll measure
  this yourself on Day 10, but the paper is short and the U-shaped curve is memorable.
- *Contextual Retrieval* (Anthropic engineering blog, 2024) — the general form of §2.7's
  heading-prefix trick, with measured gains.
- MTEB leaderboard — how embedding models are benchmarked, and worth a skeptical read: the tasks
  are not your task, and leaderboard position rarely survives contact with a domain corpus.

---

**Now go to `labs/DAY_03.md`.** The lab is built directly on §2.3 (metrics), §2.4 (the topical
gap — you'll measure it), §2.6 (the chunking bake-off), and §2.8 (brute force as ground truth).
