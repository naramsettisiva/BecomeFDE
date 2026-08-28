# The learn modules

**One per day, read before the lab. `learn/DAY_01_LEARN.md` … `DAY_24_LEARN.md`.**

---

## Why these exist

The labs teach by doing. That works — but only once you have something to do it *with*.
Handing you a terminal and saying "notice what happens" is discovery learning, and discovery
learning is excellent for consolidating an idea and terrible for introducing one. You end up
inferring a mental model from a handful of outputs, and inferred models have holes you can't
see until a student asks about one.

So each day now has two halves:

**Learn** — actual instruction. What the thing is, how it works underneath, why it was built
that way, where it breaks, and what people get wrong about it. You read it, work the examples
on paper, and take a self-check before you touch the keyboard.

**Lab** — the hands-on. Now you're building something you understand rather than pattern-
matching a tutorial.

The order matters, and it matters *twice*. You learn faster, and — more importantly for where
you're going — **you can only teach the part you were taught.** A trainer who learned entirely
by doing can demonstrate. A trainer who understands the mechanism can answer the question
nobody prepared them for, which is the whole job.

---

## The daily shape (still 5 hours)

Nothing was added to your day. The concept block grew and the lab tightened.
The course runs Thu Aug 27 – Tue Sep 29, 2026.

| Block | Time | What |
|---|---|---|
| **0 · Warm-up** | 0:20 | Spaced-repetition recall from previous days. Closed book. |
| **1 · Learn** | 1:15 | The teaching module. Read, work the examples, take the self-check. |
| **2 · Lab** | 2:20 | Build it. |
| **3 · Teach-back** | 0:40 | Record yourself explaining it. Now includes a mechanism question. |
| **4 · Ship** | 0:25 | Commit, log, retro. |

Week 4 shifts: Days 20–21 are capstone build days where the learn block shrinks to 0:30, and
Days 22–24 invert entirely — the craft days are mostly instruction and delivery.

**If the learn block routinely runs over 1:15, tell me.** That means the module is pitched
wrong for you and I'll adjust the remaining ones. Don't just absorb the overrun — a course
that quietly becomes six hours a day is a course you stop doing in week three.

---

## What's in a module

Every one has the same seven parts, so you always know where you are:

1. **Where this sits** — one paragraph connecting today to what you already built, and naming
   the specific problem today solves. Never "today we'll cover X."
2. **The mechanism** — the actual explanation. How the thing works, built up from parts you
   already understand. This is the bulk.
3. **Worked example** — real numbers, done by hand, before any code runs. Usually from the
   freight corpus so it stays concrete.
4. **What people get wrong** — the misconceptions, stated as the wrong belief and then
   corrected. Naming a misconception before you form it is worth more than correcting it after.
5. **The trainer's angle** — how you'd explain this to a room, the analogy that lands, the
   demo that makes it click, and the question a sharp student will ask that you should have an
   answer ready for.
6. **Self-check** — 6–10 questions with answers folded below. If you can't answer them, re-read
   before the lab. The lab assumes the module.
7. **Going deeper** — a curated, link-checked reading list. Every day names **one** thing to
   read if you read nothing else, then the rest in the order I'd take them, each with the
   minutes it costs and why it earns them. 107 sources across the 24 days: papers, primary
   documentation, and the essays practitioners actually cite. Every URL was fetched and
   verified — a dead link in training material costs you more credibility than a missing one.

In the HTML navigator each module also opens with a **chapter opener** — reading time, what you
need first, three things you'll be able to do by the end, and the key terms — so you can decide
in fifteen seconds whether you're ready for it.

---

## Reading them on screen

The modules are long-form prose, so read them in **`fde-bootcamp.html`** rather than in a
markdown viewer. That page sets them like a book: serif text at a measured line length, a
section rail on the right that tracks where you are, an S/M/L size control that remembers your
choice, and the worked example in §3 framed as a worked example. The markdown files are the
source of record — good for grepping and for reading on GitHub, worse for sitting with for
seventy-five minutes.

---

## How to actually use these

**Read with a pen.** Not metaphorically. The worked examples are meant to be done on paper
first — the arithmetic is small on purpose. Deriving the cosine/Euclidean relationship yourself
takes four lines and permanently fixes a confusion that reading about it does not.

**Take the self-check honestly.** Cover the answers. Getting one wrong now is free; getting it
wrong in front of a room in November is not.

You don't have to make the flashcards — **the self-checks *are* the deck.** All 288 questions are
already cards in `fde-bootcamp.html`: **Flashcards** on any day page drills that day, and
**Warm-up drill** in the sidebar deals everything due across the days you've finished. Scheduling
is Leitner: a card you miss drops to box 1 and returns tomorrow, a card you know climbs a box and
comes back in 2, 4, 8, then 16 days. Space flips, `1` missed, `2` got it.

`learn/FLASHCARDS.csv` is the same deck as a three-column CSV if you'd rather run it in Anki on
your phone — import it with `question`, `answer`, `tags`, and the tags give you `day01` … `day24`
as sub-decks.

**Log the confusions here too, not just in the lab.** Your `LEARNING_LOG.md` is the source
material for the curriculum you build on Day 22. Confusions from the *learn* half are the most
valuable entries in it, because they're the ones your future students will hit at exactly the
same point — while being taught, before they have hands on anything to disambiguate with.

**Read one external source a day, not five.** Section 7 names a single pick for a reason.
The reading only counts if you finish it, and the fastest way to read nothing all month is to
open a list of five tabs each morning. Take the pick; take the rest when a topic actually grabs
you or a client question makes it urgent.

**Don't skip ahead to the lab because you're impatient.** You will be, around Day 8. The
labs are more fun. But the days where you skip the module are the days you build something
that works and can't explain, and those are the exact topics that will fail you in a Q&A.

---

## A note on how these are written

They assume you are an experienced engineer who is new to this specific stack. So they lean on
distributed systems, platform infrastructure, and operations for analogies — because you have
23 years of intuition there and it's faster to attach a new idea to an existing one than to
build it from nothing.

They do **not** assume you remember linear algebra, or that you've read the papers, or that you
know what a transformer does internally. Where that background is needed, it's taught.

Where I'm uncertain or where the field genuinely disagrees, the module says so rather than
presenting one view as settled. You're going to teach this material — inheriting my
overconfidence would be worse than inheriting a gap you know about.
