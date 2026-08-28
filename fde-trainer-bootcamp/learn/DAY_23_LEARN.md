# Day 23 · Learn — Live delivery: teaching when you can't stop the tape

**Read before `labs/DAY_23.md`. Budget 0:30.**

---

## 1. Where this sits

Yesterday you designed a lesson. Today you find out whether you can deliver it, once, straight
through, with no edit pass.

Every recording you have made in twenty-two days has been forgiving. You could stop when a demo hung,
restart when a sentence came out backwards, and cut the ninety seconds where you looked something up.
That is a real skill and it is not this one. **Live delivery removes three affordances at once:** you
cannot stop, you cannot retake, and — the one that actually changes the job — **the audience can be
confused at you in real time.** A camera absorbs a bad explanation silently. Twelve people do not:
they go quiet in a particular way, they stop typing, and one of them asks the question that reveals
your explanation was wrong ten minutes ago.

Half of today is genuinely familiar. You have run escalation bridges and steering committees; you
know what it is to be the person in the room when something is failing, and you are not going to
panic at a stack trace on a projector. That instinct transfers whole and it is worth more than most
people's teaching experience.

The other half doesn't. **A hostile question in a QBR and a hostile question in a workshop have
different correct answers.** In a QBR, "I don't know" is often a cost you manage — you bridge, you
take it offline, you protect the decision. In a room where you are the instructor, "I don't know"
delivered in the right shape is a *credibility gain*, because the room's actual question is not "does
he know everything" but "will he tell me when he doesn't." And the whole workshop-facilitation half
of today — install disasters, skill spreads, derailers, silent rooms — is a discipline you have never
practised, because a steering committee has none of those problems.

---

## 2. The mechanism

### 2.1 What changes when it is live

Three constraints, each driving a different preparation.

**No stopping.** Every failure becomes content whether you like it or not, so your recovery *is* the
lesson at that moment. Hence fallback outputs, and hence practising the narration of a failure.

**No retakes.** Everything verifiable before you start — fonts, keys, index loaded, demo run — must be
verified before you start, because at minute 12 there is no version of you who gets to go back.

**A live audience.** A gift disguised as pressure: you get signal a camera never gives you — the
moment the typing stops, the face frowning for two minutes, the question revealing your frame didn't
land. Use the signal rather than defending against it; yesterday's checkpoint discipline exists to
manufacture it deliberately rather than waiting for it.

### 2.2 The pre-flight checklist, and why each line is there

Every line is somebody's session that went wrong. Run it before every session you ever teach.

| Check | Why it exists |
|---|---|
| **Every demo run once, start to finish, in the exact state you'll present from** | "It worked yesterday" fails on a stale index, an expired key, a `.env` you moved, or a cell you'd already run. The *exact state* clause is the whole check — a demo verified in a different terminal, venv or directory is unverified. |
| **Terminal 18pt+, editor 16pt+ — checked by standing 6 feet back** | You read your screen from 24 inches. Half the room is at ten feet or on a laptop mirroring a shrunk share. Actually stand up and look; you will be surprised, and unreadable code is a silently lost audience. |
| **Notifications off, calendar closed, Slack quit** | One personal message on a shared screen ends the session's professionalism permanently and cannot be un-seen. Also: every notification steals your attention at the moment you can least afford it. |
| **Fallback outputs saved for every live demo** | Not pessimism — arithmetic. Any demo has some failure probability per run; run enough sessions and one fails. A pre-generated result you can paste converts a session-ending failure into a fifteen-second detour. |
| **Local model warm, keys valid, index loaded** | Cold-start latency reads as a hang. Ninety seconds of dead air at minute three costs you the room's attention for the next ten. |
| **Timer visible to you, not the audience** | You need pacing data; they need not to watch a countdown. An audience that can see the clock starts managing your time for you. |
| **Water within reach** | A dry throat at minute 40 is not a small problem, and leaving to fetch water is a hole in the recording. |
| **Recording started *before* you start talking** | The single most common lost artifact in technical teaching is the first eight minutes — which contains your opening failure, the beat you rehearsed most. Start it, then set up. |

**The fallback-output line deserves its emphasis.** The mental model is a runbook entry, not a
confidence problem: you don't keep a rollback because you expect to fail, you keep it because rollback
converts an outage into an inconvenience. Same discipline, and you have twenty-three years of it.

### 2.3 Recovering on camera

The claim surprises people and it is true: **a failed demo debugged live is a better teaching moment
than a demo that works** — conditional on one thing, that you **narrate the diagnosis instead of
panicking**. A working demo shows the happy path, which nobody will be on within a week. A failing
demo shows the traceback, the hypothesis, the check and the fix — the invisible skill they came for.
It is yesterday's deliberate error, arriving unplanned.

What the narration sounds like — worth having by heart:

> "Right — that's not what I expected. Let's read it. `KeyError: 'chunk_id'` — so something upstream
> isn't returning the field I think it is. Two possibilities: either the index was built with an
> older schema, or I'm calling the wrong retriever. Cheapest check first — print one result. …There
> it is, no `chunk_id`, this index is from the old build. This is exactly the failure mode we talked
> about in slot two, and it's the reason you version your index."

Four moves: name the surprise, read the actual error aloud, state two hypotheses, run the cheapest
discriminating check. A diagnostic process rendered visible, worth more than the demo would have been.

**The failure mode is silence.** A presenter who goes quiet and starts typing has left the room; ten
seconds of silent debugging feels like thirty from the other side, and attention doesn't come back for
several minutes. If you need to think, say what you're thinking about.

**Two hard limits.** Set a **budget — ninety seconds, or two** — in advance, and when it expires take
the fallback and say so: *"I'm not burning your time on this; here's the output it produces, and I'll
post the fix afterwards."* And never fix it by silently editing around it — the room can tell, and a
concealed failure costs far more than the visible one.

**Keep your typos.** Backspacing and re-typing is fine; apologising for it is not. A student watching
flawless typing concludes the skill is inaccessible; one watching you typo, notice and fix concludes
it is learnable.

### 2.4 Questions: the three-part "I don't know", and the discipline of parking

**The three-part answer.** Ten seconds, and it *builds* credibility rather than spending it:

> **"I don't know. Here's how I'd find out: [specific method]. I'll follow up by [when]."**

Each part is load-bearing. Part one is the honest signal. **Part two is the actual credibility
move** — it demonstrates a method, which is what a client is really buying; "I'd run it at both chunk
sizes on your corpus and compare recall@5" is more impressive than a fact would have been. Part three
converts a gap into a commitment, and is only worth saying if you mean it. The version that fails is
*"I don't know, but I think probably…"* — bluffing with a disclaimer. Pick one.

**Why bluffing is always visible.** Always, and independent of the audience's expertise. Specifics
disappear, hedges multiply, sentences lengthen and end weakly, prosody shifts. And **the person asking
is usually the one person who knows the answer** — that is generally why they asked. The economics are
brutal: an admitted gap costs nothing and often gains; a detected bluff retroactively devalues every
confident statement you made earlier, because the room must now re-evaluate which were real.

**Parking, and actually returning.** *"Great question — let me take that at the end"* is a broken
promise about 80% of the time, which is worse than not parking. Make it mechanical: **write it down
where the room can see you write it.** That commits you publicly, reassures the asker they weren't
dismissed, and stops you forgetting. Then return by name — *"Priya asked about 200,000 documents;
here's the honest answer."* It is one of the strongest trust signals an instructor gives, precisely
because it is rare. Out of time? Name it in the close and follow up in writing.

### 2.5 The five question types

You will get all five in any hostile Q&A. They look similar and they are handled differently — the
common error is answering every one as though it were type 1.

| Type | What it sounds like | Handling | Trap |
|---|---|---|---|
| **1. Genuinely hard technical** | "How does this hold at 200,000 documents?" | Answer directly, with a number and a boundary. Say where your knowledge ends. | Padding. If you know it, say it in three sentences and stop. |
| **2. Sceptical challenge to the premise** | "We tried RAG last year and it didn't work. Why is this different?" | Concede the premise honestly, then differentiate specifically. "You're right that most 2023 RAG pilots failed, and mostly for one reason — no eval. Here's what changes when you have one." | Defensiveness. Watch the recording; you will see it before you feel it. |
| **3. About something not covered** | "What about fine-tuning?" | One-sentence orientation, then the boundary: "Out of scope today; here's the 30-second version and where it fits." | Following it. Twenty minutes of your best material on the wrong topic loses the other nineteen people. |
| **4. Built on a false premise** | "Since the judge model always agrees with GPT-4, how do you…?" | **Correct the premise first, then answer.** "Let me stop on one thing — it doesn't always agree; I measured κ at 0.61 on this set. Given that, your question becomes…" | Answering as asked. |
| **5. A disguised objection** | "What's the ROI? My CFO will ask." | Answer the surface question briefly, then name the real one: "The underlying question is whether this survives a budget review. Here's what I'd put in front of a CFO." | Treating it as technical. It is a decision question wearing a technical costume. |

**Type 4 deserves the emphasis.** Answer a false-premise question as asked and you have endorsed the
premise in front of the whole room — everyone now believes it, including the people who will repeat it
to their teams. The correction comes *first*, specifically, and briefly enough not to feel like a
lecture: "it doesn't always agree — κ was 0.61 — and given that, here's the answer" takes six seconds
and stops a wrong belief propagating.

**Type 5 is the one your background is best at**, so trust the instinct. The only new part is that in
a teaching room you *name* the real question out loud rather than smoothly handling it, because naming
it is useful to everyone else present.

### 2.6 Workshop facilitation is a different skill

A lecture is a broadcast you control. A workshop is twenty people typing, at different speeds, on
different machines, and your job is throughput rather than delivery. Most client enablement takes
this second shape. Four situations; have a scripted default for each *before* the day.

**1. The install disaster (0:00–0:10).** A third of the room can't get the environment running.

| Option | Cost | When |
|---|---|---|
| Fix them one by one | You lose the session. 15 people wait on 5. | Never, at scale |
| Push everyone to a pre-built Codespace/Colab | You lose local realism | The reliable default |
| Pair broken with working | Halves the problem, builds the room | Good when the split is under a third |

Decide the default now. But the actual rule is the preparation, not the choice: **have the fallback
environment built and tested beforehand, not built during.** A Codespace you assemble live is a
second install disaster with an audience. Test it from a clean account, on the day's material, and
have the link in the chat before anyone reports a problem.

**2. The spread.** Two people finish the core exercise in six minutes; four are still on step one at
fifteen. Tiered exercises (core / stretch / challenge — built yesterday) are half the fix. The other
half: **recruit the fast finishers as floaters** — *"you're through it; go sit with the two people on
the far side and get them unstuck"* — because **being asked to help is the most engaging thing that
can happen to an advanced student.** It converts your two most likely disengagers into two more
instructors, and teaches them more than the stretch task would.

**3. The derailer.** Someone asks increasingly tangential questions and the room drifts. Almost always
well-intentioned and often the most engaged person present, which is why bluntness backfires. Three
parts, kindly and firmly:

> "That's a real question and it's outside what we can do justice to today — let me grab it for the
> end and make sure I get you a proper answer. Right now I want to make sure everyone's got output
> from step two. **Who's got a number?**"

**Redirect + commitment + a concrete check.** The third part is the one people omit and it does the
work: it moves the room's attention off the tangent onto their own screens, so the redirect lands as a
group activity rather than a public correction of one person. If it recurs, handle it in the break,
individually and generously.

**4. The silent room.** No questions, no chat, nothing. **Never ask "any questions?"** — for the
reasons in yesterday's §2.5, it is a check on social confidence. Three replacements, in escalating
order of how stuck you think they are:

- **Concrete artifact.** *"Paste your recall@5 in the chat. I'll wait."* Low social cost, and you get
  a distribution.
- **Pair-compare.** *"Turn to the person next to you and compare your numbers. Two minutes."* Peer
  first — after two minutes of talking to one person, talking to the room is far cheaper, and it
  surfaces confusions that were never going to reach you.
- **Binary show of hands.** *"Who got something above 0.7? Below?"* Nearly anonymous, everyone can
  answer, and you get a number.

And the one that costs nothing: **wait longer.** Most instructors give a question three seconds. Ten
seconds of silence is uncomfortable for you and productive for them, and the answers that arrive
after eight seconds are the good ones.

### 2.7 Self-assessment: watch it at 1.0×, in full

Watch it back at **1.0×, all of it, no skipping.** Unpleasant and non-negotiable, for one reason:
**the defects you need live in the gaps.** At 2× your pacing sounds fine, filler words vanish into the
compression, and forty seconds of dead air sounds like four. Everything wrong with a delivery is a
*timing* property, and speed destroys timing.

Score things you can count, not things you can feel:

| Dimension | Countable evidence |
|---|---|
| Opened with a real failure that created a question | Timestamp; did anyone react? |
| Frame stated and named 3+ times | Count of uses, with timestamps |
| Predictive question before at least one demo | Count |
| Deliberate error included and debugged live | Timestamp, plus seconds of silence during it |
| A number visibly moved | Timestamp |
| Checkpoint every ~10 min | Longest gap between checkpoints |
| Recovered from at least one unplanned problem | Time from failure to first spoken word |
| Filler words per minute | Count a 5-minute sample, extrapolate |
| Finished within ±5 min of plan | Signed error per section — that's your multiplier |

**Counted things improve; felt things plateau.** "I think I was a bit fast" produces no change;
"longest gap between checkpoints was 22 minutes" produces one next session. Same argument as every
eval you built this month.

Then compare three minutes of today against three minutes of Day 6, back to back. Eighteen sessions of
deliberate practice (Ericsson's term, and this is what it means — a specific target and immediate
feedback, not repetition) produce a visible difference, and seeing it is the evidence.

---

## 3. Worked example — on paper

Five awkward moments. For each, **write the words you would actually say** — not a strategy, the
script. The gap between "I'd stay calm and redirect" and a sentence you can say under pressure is the
whole exercise.

Setting: your evals lesson, 18 people, mixed skill, one hour, recorded.

**Q1.** Minute 12. The live golden-set generation call hangs, then returns a 429. Twenty seconds of
nothing. Script the next sixty seconds.

**Q2.** Minute 26. *"What's the inter-annotator agreement you'd expect between two human labellers on
this rubric?"* You don't know. Script the answer.

**Q3.** Minute 4 of a workshop. Six of eighteen have a broken environment. Script the announcement.

**Q4.** Minute 31. The same person asks their fourth increasingly tangential question, this one about
fine-tuning embedding models. Script the redirect.

**Q5.** Minute 22. You asked for a paste. Nothing in chat. Nobody speaks. Script the next ninety
seconds.

**Q6.** Minute 40. *"Since LLM judges always favour longer answers, isn't your whole quality score
just measuring verbosity?"* Handle it.

**Q7.** You watched the recording. Frame named once (minute 6). Longest checkpoint gap: 24 minutes.
Two predictive questions. Finished 9 minutes over. What are the two changes, and what do you *not*
change?

<details>
<summary><b>Answers — script yours first, out loud, then compare</b></summary>

**Q1.** The failure is real, so use it.

> "That's a 429 — we're rate-limited. Which, honestly, is useful: this is the single most common
> thing that breaks an eval run in CI, and it's the reason clause four of the ladder says a gate that
> silently passes on API error is worse than no gate. I've got ten pre-generated cases saved for
> exactly this — [pastes] — here they are. Read them with me. **Predict: how many of these ten are
> actually good questions?**"

It names the error out loud, converts it into content already in the lesson, uses the fallback inside
the ninety-second budget, and lands on a predictive question — which re-engages the room and buys the
ten seconds you need. What not to do: retry silently three times, apologise twice, or say "this always
works" (an excuse, and probably false).

**Q2.**

> "I don't know. It's a good question and I've never measured human–human agreement on this rubric —
> I've only measured judge-versus-me. Here's how I'd find out: take 30 cases, have two people label
> them independently against the same rubric, compute Cohen's κ, and treat *that* as the ceiling for
> the judge rather than assuming 1.0. I'd expect it to be uncomfortably low — probably in the 0.5–0.7
> range on a rubric this subjective, which would mean some of what I've been calling judge error is
> actually rubric ambiguity. I'll run it this week and put the number in the FAQ."

Three parts present, plus one bonus worth including: **an honest expectation, flagged as an
expectation.** "I'd expect roughly X, and here's why" is not bluffing — it is a calibrated prediction,
clearly labelled — and it is often more useful than the fact.

**Q3.** Decision made before the day, announced without deliberation.

> "Quick check — hands up if you've got a green test run. …Okay, about two-thirds. Here's what we're
> doing: the Codespace link is in the chat now, it's pre-built and I tested it this morning, and it
> has everything today needs. If you're stuck, click it and you'll be running in ninety seconds — we
> can debug your local setup at the break and I'll stay after for it. Everyone who's green, stay
> local. Nobody is behind; you're on a different runtime, that's all. Back together in two minutes."

The moves: measure before deciding (a show of hands, not an impression); decide with no visible
deliberation, because deliberation reads as unpreparedness; the fallback exists *already*; local setup
is deferred, not abandoned; and one sentence of reassurance, because six people currently think they
are the problem. Note what is absent — any diagnosis of any individual error. That is the trap.

**Q4.**

> "Fine-tuning embeddings is a real topic and a good question, and it's genuinely outside what we can
> do justice to in the time — let me take it at the end and I'll point you at the two things worth
> reading. Right now I want to make sure everyone's got a κ on screen from build three. **Show of
> hands: who's got a number? Who's got an error?**"

Redirect (named as real, not dismissed) + commitment (written on the visible parking list) + concrete
check (which moves eighteen people's attention to their own screens and ends the exchange without
anyone being publicly corrected). Say it warmly — tone is the difference between this working and
being remembered as a snub.

**Q5.**

> "Nothing in chat, which usually means one of two things and I'd like to know which. Turn to the
> person next to you and compare what you've got for recall@5 — two minutes, go." [waits the full two
> minutes, walks the room / watches breakouts] "Okay — show of hands, who got something above 0.5?
> Below? …Right, most of you are below, and that's the interesting case. What did you set k to?"

Escalation in the right order: the artifact request already failed, so go to **pair-compare** rather
than repeating yourself louder; then binary hands, which everyone can answer; then a specific question
with a short factual answer. Two things not to do: fill the silence with more explanation (you are
already ahead of them, so more talking widens the gap), and ask "does that make sense?" — which asks
them to assess their comprehension of something they don't understand.

**Q6.** Type 4 — false premise, and a partly-true one, which is the hardest kind.

> "Let me take the premise first, because it's half right. Length bias in LLM judges is real and
> well documented — but 'always' is doing a lot of work there, and it's mostly a property of
> *absolute* scoring. When I ran this rubric pairwise with position swapping, the length correlation
> dropped a lot; I can show you the numbers after. So: it's a bias you have to design against, not a
> fact that invalidates the method. Given that, your real question is 'how do I know my judge isn't
> measuring verbosity', and the answer is that you test for it — hold content constant, vary length,
> and see if the score moves. If it does, you've got the bug and you switch to pairwise."

The shape: correct the premise *first*, concede the true part specifically (which is what makes the
correction land rather than sound defensive), then reconstruct the question in its valid form and
answer that. Note that it hands them a test rather than a reassurance — a method is a better answer
than a claim, and it is the one they can repeat to their own sceptic.

**Q7. The two changes.** (1) **The checkpoint gap.** 24 minutes means you taught blind for nearly half
the session — the defect most likely to have cost real learning. Fix it structurally, not by
intention: write the checkpoints into the plan as numbered lines with their scripts, so they get
delivered rather than remembered. (2) **The frame, named once.** A frame named once is a slide. Add
two scripted callbacks at planned transitions.

**What you don't change: the 9-minute overrun.** Not a delivery defect — a measurement. Your
multiplier is real and the plan didn't use it, so re-plan the *content* rather than resolving to talk
faster: cut the generalise beat and pre-write more of the build. Two predictive questions is fine;
don't add more for the count.

The discipline: **fix the two highest-cost defects, not all nine.** A revision list that changes
everything gets applied to nothing, and you are delivering this again next week.

</details>

---

## 4. What people get wrong

**"A smooth session is a good session."**
Smooth means nothing went wrong, which usually means nothing was attempted live and nobody struggled.
The best sessions have a failure in them.

**"Recovering from a failed demo is damage control."**
It is the most valuable content in the hour, provided you narrate. The audience will be on the
unhappy path within a week; you are showing them the only thing that helps there.

**"Saying 'I don't know' costs credibility."**
It costs nothing and usually gains, because the room's real question is whether you'll tell them.
What costs is the detected bluff, which retroactively devalues everything confident you said earlier.

**"I'll remember the parked question."**
You won't. Write it visibly, and return to it by the asker's name.

**"A false-premise question can be answered as asked."**
Answer it as asked and you have endorsed the premise for the entire room. Correct first, briefly,
then answer.

**"Facilitation is lecturing with exercises."**
Different job. Lecturing optimises delivery; facilitation optimises throughput across a spread, and
the moves — tiering, floaters, artifact checkpoints, pair-compare — have no lecture equivalent.

**"I'll sort the environment issues during the workshop."**
The fallback environment must exist and be tested before the day. Built live, it is a second install
disaster with an audience.

**"Fast finishers are the group I don't have to worry about."**
They are the group that disengages first and the group whose opinion travels. Give them the stretch
task or, better, give them people.

**"Watching at 2× is review."**
Every defect worth finding is a timing property — pacing, dead air, filler rate, checkpoint gaps —
and speed destroys timing. 1.0×, in full.

---

## 5. The trainer's angle

**This section is meta on Days 22–24** — it is about teaching someone else to teach, not about
teaching today's topic.

**The drill that does the most work per minute: the failure drill.** Have the trainee deliver five
minutes of their lesson while you, privately, break something — kill their network, empty their
index, change a key. Score only the first thirty seconds after it breaks: did they say what happened
out loud within five seconds, or did they go silent and start typing? Almost everyone goes silent the
first time, and almost nobody does the second time. That is the highest-leverage half hour in trainer
development, and it cannot be taught by telling.

**The drill for questions: the type-sorting drill.** Fire fifteen questions and have them *name the
type before answering* — out loud, "that's a type four" — then answer. It feels artificial and it
installs the classification habit in about twenty minutes. Under real pressure, classification is the
thing that vanishes first; everything gets answered as type 1.

**The uncomfortable rehearsal that pays most: rehearse saying "I don't know."** Have them say the
three-part answer ten times to ten different questions until it stops feeling like a concession. Most
new trainers have never said it out loud in a professional setting, and an unpractised admission
comes out apologetic, which reintroduces exactly the credibility cost you were avoiding.

**The thing to insist on and expect resistance to:** watching their own recording at 1.0× in full,
with a counting sheet. They will do it once, hate it, and improve more from that hour than from three
more deliveries. Insist on numbers on the sheet, because a trainee who writes "pacing: okay" has not
done the exercise.

**The question a sharp trainee will ask:** *"If a failed demo teaches better, why not fake one?"*

> Because it doesn't survive contact. A staged failure is *scripted recovery*, and the room can tell
> — the diagnosis is too fluent, the hypotheses arrive in the right order, and there's no moment of
> actual surprise. That moment is what makes the recovery instructive and what makes it credible. The
> legitimate version is yesterday's deliberate error: a real error you introduce on purpose, that
> really fails, and that you really debug. And you don't need to fake anything anyway — deliver
> enough live sessions and reality supplies them.

**The failure mode in trainer development:** they treat delivery as a performance skill and try to
improve by rehearsing more. Past about the third rehearsal that stops working. Improvement comes from
counted feedback on real deliveries and from drilling the specific recoveries — the failed demo, the
unknown question, the silent room — which are the moments rehearsal never touches because rehearsal
never breaks.

---

## 6. Self-check

1. Name the three things live delivery removes, and one preparation each drives.
2. Why must a demo be verified in the *exact state you'll present from*?
3. What's the real argument for fallback outputs, and what does it have in common with a rollback plan?
4. Under what condition is a failed demo better than a working one — and what are the four narration moves?
5. What is your silence budget for a live failure, and what happens when it expires?
6. Give the three-part "I don't know" and say what each part is for.
7. Why is bluffing always visible, and why is the trade economically bad?
8. What makes parking a question work rather than becoming a broken promise?
9. Name the five question types and the trap for each.
10. Why must a false premise be corrected before the answer?
11. Install disaster: three options, and the rule that matters more than which you pick.
12. Why is recruiting fast finishers as floaters better than giving them a stretch task?
13. Three replacements for "any questions?", in escalating order.
14. Why 1.0× and in full?

<details>
<summary><b>Answers</b></summary>

1. No stopping (rehearse recovery, keep fallbacks); no retakes (verify everything verifiable before
   you start); a live audience that can be confused at you (manufacture the signal with checkpoints
   and use it).
2. "It worked yesterday" fails on a stale index, an expired key, a moved `.env`, or an already-run
   cell. A demo verified in a different terminal, venv or directory is unverified.
3. Arithmetic, not pessimism: any demo has a per-run failure probability, so across enough sessions
   one fails. Like a rollback plan, it converts an outage into an inconvenience — you don't have one
   because you expect to fail.
4. Conditional on narrating the diagnosis rather than panicking. Name the surprise, read the error
   aloud, state two hypotheses, run the cheapest discriminating check.
5. Ninety seconds to two minutes, decided in advance. On expiry, take the fallback and move on
   explicitly — never fix it by silently editing around it.
6. "I don't know." (honest signal) "Here's how I'd find out: [method]." (the credibility move — a
   method is what the client is buying) "I'll follow up by [when]." (converts gap to commitment; only
   say it if you mean it.)
7. Specifics disappear, hedges multiply, sentences lengthen and end weakly, prosody shifts — and the
   asker is usually the one person who knows the answer. An admitted gap costs ~nothing; a detected
   bluff retroactively devalues every earlier confident statement.
8. Writing it down visibly, and returning to it by the asker's name. Otherwise it's broken about 80%
   of the time, which is worse than not parking.
9. Hard technical (trap: padding); sceptical challenge (defensiveness); not covered (following it);
   false premise (answering as asked); disguised objection (treating it as technical).
10. Answering as asked endorses the premise for the whole room, and everyone repeats it to their
    teams. Correct first, specifically, briefly.
11. One-by-one (lose the session), pre-built cloud environment (lose local realism), pair broken with
    working (halves it, builds the room). The rule that matters more: the fallback environment must
    be **built and tested beforehand**.
12. Being asked to help is the most engaging thing that can happen to an advanced student. It
    converts your two most likely disengagers into instructors and teaches them more than the stretch
    task.
13. Concrete artifact ("paste your recall@5"), pair-compare ("compare with your neighbour, two
    minutes"), binary show of hands ("above 0.7? below?"). Plus: wait ten seconds, not three.
14. Every defect worth finding is a timing property — pacing, dead air, filler rate, checkpoint gaps
    — and speed destroys timing. At 2× a lost room sounds fine.

</details>

**Scored below 10?** Re-read §2.4 and §2.5 before the lab. Block 2 is fifteen hostile questions in
real time and you cannot classify them while looking up the classification.

---

## 7. Going deeper

<!--reading:23-->

### If you read one thing this week

**[speaking.io — Tips for Public Speaking](https://speaking.io/)** — Zach Holman · docs · ~45 min

The most practical free guide to technical speaking there is — read "Prep for the Big Day" and "Deliver and Do Your Thing" the night before your one-take.

### Then, in the order I'd take them

- **[Teaching Tech Together — ch. 8, Teaching as a Performance Art](https://teachtogether.tech/en/index.html)** — Greg Wilson · docs · ~30 min  
  Live-coding technique specifically — pacing, typos, and why narrating your mistakes teaches more than a clean run.
- **[Ideas for making better conference talks & conferences](https://jvns.ca/blog/2016/06/06/make-better-conference-talks/)** — Julia Evans (Jun 2016) · essay · ~15 min  
  Her test — "say a new-to-your-audience thing in an understandable way" — is the one to hold your teach-back against. Also the argument for getting feedback from an actual target listener before you deliver.

<!--/reading-->

### Also mentioned in this module

- Your own Day 6 recording — ten minutes of it, today, *before* you deliver. It's tonight's baseline,
  and watching it first makes the comparison honest instead of flattering.
- Lemov, *Teach Like a Champion* — written for schools; the cold-call, wait-time and "no opt out"
  techniques transfer directly to a silent adult room. Skim the techniques, ignore the framing.
- Ericsson on deliberate practice (Ericsson, Krampe & Tesch-Römer, 1993) — read once for what it
  actually claims: a specific target, immediate feedback, repetition at the edge. Delivery reps
  without a scored rubric are not deliberate practice, which is why today ends with a counting sheet.
- Any recording of a conference talk where a live demo fails. Watch the first thirty seconds after it
  breaks; you'll learn more from one bad recovery than from ten smooth talks.

---

**Now go to `labs/DAY_23.md`.** Block 0 is §2.2, Block 1 lives on §2.3 (you will need it), Block 2 is
§2.4–2.5 — classify out loud before answering — Block 3 is §2.6, and Block 4 is §2.7 with a counting
sheet, at 1.0×.
