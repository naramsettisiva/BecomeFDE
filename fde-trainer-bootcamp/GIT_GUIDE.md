# Git on macOS — the bootcamp guide

**Written for someone who has never run git from a Mac terminal.**
Setup takes about 25 minutes, once. After that you use four commands a day.

---

## Part 0 — The mental model (5 minutes, read this first)

Almost every beginner git problem comes from not having this picture. It is worth
five minutes now to save an hour later.

Your work lives in **four places**, and git moves it between them:

```
  ┌───────────────┐   git add    ┌───────────┐   git commit   ┌────────────┐   git push   ┌──────────┐
  │   Working     │ ───────────► │  Staging  │ ─────────────► │   Local    │ ───────────► │  GitHub  │
  │   directory   │              │   area    │                │ repository │              │ (remote) │
  │               │ ◄─────────── │           │                │            │ ◄─────────── │          │
  └───────────────┘  git restore └───────────┘                └────────────┘   git pull   └──────────┘
   the files you        --staged      "I intend to             the permanent      other machines,
   actually edit                      save these"              history            other people
```

1. **Working directory** — the actual files on your Mac. Edit `DAY_07.md`, it changes here.
2. **Staging area** — a holding pen. `git add` puts changes here. This exists so you can
   commit *some* of your changes and not others. Most days you'll stage everything.
3. **Local repository** — `git commit` writes staged changes into permanent history, **on your
   Mac**. Nothing has touched the internet yet. You can commit on a plane.
4. **Remote (GitHub)** — `git push` sends your local commits up. Only now can anyone else see them.

**The single most common beginner confusion:** "I committed, why isn't it on GitHub?"
Because commit and push are different steps. Commit saves history locally. Push publishes it.

The second most common: "I edited a file, why didn't it get committed?" Because you didn't
`git add` it. Git only commits what you staged.

That's the whole model. Everything below is mechanics.

---

## Part 1 — One-time setup (25 minutes)

### 1.1 Install git (2 min)

macOS ships with Apple's git, but it lags several versions behind. Get the current one:

```bash
brew install git
```

Then **open a new terminal window** and check which one you're getting:

```bash
which git
# want:  /opt/homebrew/bin/git   (Apple Silicon)
#   or:  /usr/local/bin/git      (Intel)
# NOT:   /usr/bin/git            ← that's Apple's older one

git --version
```

If you see `/usr/bin/git`, Homebrew's version isn't on your PATH first:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
exec zsh -l          # reload the shell
which git            # check again
```

Apple's git works fine for everything in this course — this is tidiness, not necessity.

### 1.2 Tell git who you are (1 min)

Every commit is stamped with a name and email. Set them once, globally:

```bash
git config --global user.name "Siva Naramsetti"
git config --global user.email "your@email.com"
```

**Use the same email you'll use on GitHub.** If they don't match, your commits show up as
an unattached grey avatar instead of linking to your profile — which matters when the commit
history *is* the portfolio artifact.

GitHub also offers a private no-reply address (Settings → Emails → "Keep my email addresses
private") if you'd rather not have your real address in every commit. It looks like
`12345+username@users.noreply.github.com`. Either is fine; just be consistent.

### 1.3 Set your editor — do this before it ambushes you (2 min)

If you ever run `git commit` **without** `-m "message"`, git opens an editor so you can type
one. On a fresh Mac that editor is **vim**, and vim does not tell you how to leave. People
lose real time to this.

Pick one now:

```bash
# Option A — nano. Simple, shows its shortcuts at the bottom. Recommended.
git config --global core.editor "nano"

# Option B — VS Code. --wait is essential; without it git thinks you finished instantly.
git config --global core.editor "code --wait"
```

**And if vim catches you anyway before you've set this:** press `Esc`, then type `:wq` and
press Return. That's write-and-quit. `:q!` is quit-without-saving. Write those two on a
sticky note today.

### 1.4 A few settings that prevent specific problems (2 min)

```bash
# Name the first branch 'main'. GitHub expects main; git's old default was master.
git config --global init.defaultBranch main

# When you pull, replay your commits on top instead of making a merge bubble.
# Keeps your history a readable straight line — which matters when it's a portfolio.
git config --global pull.rebase true

# Push the current branch to the same-named branch upstream. Avoids a class of confusion.
git config --global push.default simple

# Colour the output. Genuinely helps you read status and diffs.
git config --global color.ui auto

# Store credentials in the macOS Keychain (only used if you fall back to HTTPS)
git config --global credential.helper osxkeychain
```

Check what you've set at any time:

```bash
git config --global --list
```

### 1.5 SSH key — how your Mac proves it's you (8 min)

GitHub needs to know a push is really from you. Two ways:

| | SSH key | HTTPS + token |
|---|---|---|
| Setup | 8 minutes, once | 3 minutes |
| Daily use | silent | token in keychain, occasionally re-prompts |
| Token expiry | never | 30–90 days, then it breaks and you've forgotten why |

**Use SSH.** The extra five minutes today saves a confusing outage in October.

```bash
# 1. Generate the key. Use the same email as your GitHub account.
ssh-keygen -t ed25519 -C "your@email.com"
#   "Enter file in which to save the key" → press Return (accept the default)
#   "Enter passphrase"                    → type one, or press Return twice for none
```

A passphrase encrypts the key on disk. With the Keychain config below you'll only be asked
once, so a passphrase costs you nothing ongoing. Recommended if this Mac ever leaves the house.

```bash
# 2. Start the ssh-agent
eval "$(ssh-agent -s)"

# 3. Tell macOS to load the key from Keychain automatically on every login.
#    UseKeychain is a macOS-only option — this exact config won't work on Linux.
cat >> ~/.ssh/config <<'EOF'

Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
EOF

# 4. Add the key to the agent and the Keychain
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# 5. Copy the PUBLIC key to your clipboard. Note the .pub — never share the other file.
pbcopy < ~/.ssh/id_ed25519.pub
```

Now in the browser: **GitHub → your avatar → Settings → SSH and GPG keys → New SSH key.**
Title it something like `MacBook — FDE bootcamp`. Paste. Add.

Test it:

```bash
ssh -T git@github.com
```

First run asks *"The authenticity of host 'github.com' can't be established… continue?"* —
type `yes`. Then you should see:

```
Hi <your-username>! You've successfully authenticated, but GitHub does not provide shell access.
```

**That "does not provide shell access" line is success, not an error.** It confuses everyone
the first time. GitHub is saying "I know who you are, but you can't get a terminal here" —
which is correct and expected.

### 1.6 Create the GitHub repository (3 min)

In the browser: **GitHub → New repository.**

- **Name:** `fde-trainer-bootcamp`
- **Visibility:** your call. **Public** if you want it to be portfolio evidence from day one —
  and I'd argue you do; a public repo with 24 dated commits is the artifact.
- **Do NOT tick** "Add a README", "Add .gitignore", or "Choose a license".

That last point matters. You already have those files locally. If GitHub creates its own,
the two histories have nothing in common and your first push is rejected with
`fatal: refusing to merge unrelated histories` — a genuinely baffling error for a first
push. Leave the repo empty and this never happens.

### 1.7 Connect your local folder to it (2 min)

```bash
cd ~/path/to/fde-trainer-bootcamp

# If you haven't already: scripts/setup.sh ran `git init` for you.
# Check — this should print a branch name, not an error:
git status

# If it says "not a git repository":
git init
git branch -M main
```

Now point it at GitHub. Use the **SSH** URL (starts `git@github.com:`), not the HTTPS one:

```bash
git remote add origin git@github.com:<your-username>/fde-trainer-bootcamp.git
git remote -v          # verify — should list origin twice, fetch and push
```

Got the wrong URL in? Fix it with `set-url`, don't add a second remote:

```bash
git remote set-url origin git@github.com:<your-username>/fde-trainer-bootcamp.git
```

### 1.8 The first push (2 min)

**Before you push anything, check what you're about to publish:**

```bash
git status
```

Read the list. Specifically confirm `.env` is **not** there — it's in `.gitignore`, but check
with your own eyes this first time. A leaked API key is a bad afternoon.

```bash
git add -A
git commit -m "Day 0: bootcamp scaffold and AWS lane"
git push -u origin main
```

The `-u` sets `origin/main` as this branch's default upstream. It's why every later push is
just `git push` with no arguments.

Refresh the GitHub page. Your repo is there, README rendering at the bottom.

---

## Part 2 — The daily loop (this is 95% of what you'll do)

At the end of every lab day:

```bash
git status                              # what changed? read it.
git add -A                              # stage everything
git commit -m "Day 07: agent loop from scratch, five failure modes"
git push
```

Or the one-liner the repo provides, which lints and tests first:

```bash
make ship M="Day 07: agent loop from scratch, five failure modes"
```

That's it. Four commands, or one.

### Writing commit messages that are worth something

Your commit history is a portfolio artifact — a hiring manager scrolling it sees four weeks
of daily work. Treat the messages accordingly.

| Bad | Good |
|---|---|
| `update` | `Day 07: agent loop from scratch, five failure modes` |
| `fixes` | `Day 08: fix synthesis bucket — query decomposition, 0.41 → 0.87` |
| `wip` | `Day 14: hybrid retrieval ablation on 200-doc corpus` |
| `stuff` | `Day 18: red-team report, 50 attacks, indirect injection confirmed` |

The convention: **imperative or descriptive, specific, and it names what changed.** If a
message could apply to any day, it's not doing its job.

### Checking your work

```bash
git log --oneline -10          # last 10 commits, one line each
git log --oneline --graph      # with branch structure drawn
git diff                       # unstaged changes — what you've edited
git diff --staged              # staged changes — what you're about to commit
git show HEAD                  # the full contents of your most recent commit
```

`git log --oneline` is the one you'll use most. On Day 24 run `git log --oneline | wc -l` and
look at the number.

**Note on paging:** `git log` and `git diff` open a pager. Scroll with arrows or space, and
**press `q` to quit**. If you're stuck in a screenful of text you can't escape, it's `q`.

---

## Part 3 — Reading what git tells you

Git's messages are informative once you know the shape. Three you'll see constantly:

### `git status` — the one to read carefully

```
On branch main
Your branch is ahead of 'origin/main' by 2 commits.       ← you have 2 unpushed commits

Changes not staged for commit:                            ← edited, NOT staged
        modified:   labs/DAY_07.md

Untracked files:                                          ← new, git has never seen these
        labs/day07/agent.py

nothing added to commit but untracked files present
```

Three sections, three states: **staged** (green, going in the next commit), **not staged**
(red, edited but not going in), **untracked** (red, brand new). `git add -A` moves everything
from the bottom two into the first.

### After a commit

```
[main 3f2a1b8] Day 07: agent loop from scratch
 4 files changed, 312 insertions(+), 8 deletions(-)
```

`3f2a1b8` is the commit hash — the permanent ID. You can always get back to this exact state.

### After a push

```
To github.com:siva/fde-trainer-bootcamp.git
   9c1d4e2..3f2a1b8  main -> main
```

Two hashes and an arrow means it worked. Now it's on GitHub.

---

## Part 4 — When things go wrong

This is the section you'll actually come back to. Nothing here is dangerous if you follow it
as written.

### "I'm stuck in vim and can't get out"

`Esc`, then `:wq` + Return to save and quit. Or `:q!` + Return to quit without saving.

Then go set your editor (§1.3) so it doesn't happen again.

### "I want to undo my last commit but keep the changes"

```bash
git reset --soft HEAD~1
```

The commit disappears; your edits stay staged. Fix, re-commit. **Only do this if you haven't
pushed yet** — rewriting history that's already on GitHub causes problems for anyone who
pulled it. On a solo repo it's still recoverable, but avoid the habit.

### "I want to throw away my changes to one file"

```bash
git restore labs/DAY_07.md            # discard edits, back to last commit
git restore --staged labs/DAY_07.md   # unstage it but keep the edits
```

`git restore` (without `--staged`) **permanently discards uncommitted work.** Be sure.

### "Push rejected — non-fast-forward" or "updates were rejected"

```
! [rejected]        main -> main (fetch first)
error: failed to push some refs
```

Means GitHub has commits you don't have locally — usually because you edited a file in the
GitHub web UI. Pull first, then push:

```bash
git pull            # your pull.rebase=true setting replays your work on top
git push
```

### "I accidentally committed `.env`"

Act immediately, in this order — **the key is compromised the moment it's pushed**.

```bash
# 1. ROTATE THE KEY FIRST. Go to OpenAI/Anthropic/AWS and revoke it, right now.
#    Removing it from git does NOT un-leak it. Assume it's public.

# 2. Then remove it from tracking, keeping the local file
git rm --cached .env
git commit -m "remove .env from tracking"
git push

# 3. Confirm .gitignore contains .env (it does in this repo)
grep '^\.env$' .gitignore
```

Step 1 is not optional and not paranoia. Bots scrape GitHub for committed keys within
minutes. This same discipline is exactly what you'd walk a client through, and having done it
once yourself makes that conversation calm instead of alarming.

### "It says my file is too large"

GitHub warns above 50 MB and refuses above 100 MB. In this repo that'll be a screen
recording. They're already in `.gitignore` (`teaching/recordings/*.mov`), but if one slipped
in before you committed:

```bash
git rm --cached teaching/recordings/day_06.mov
git commit -m "remove recording from tracking"
```

Keep recordings local. Upload the good ones to YouTube unlisted and link them from
`teaching/README.md` — which is better for your portfolio anyway, since a hiring manager will
click a video link and won't download a `.mov` from a repo.

### "Merge conflict"

Only happens if the same lines changed in two places — rare on a solo repo, but possible if
you edit on GitHub's web UI and locally. Git marks the file:

```
<<<<<<< HEAD
your local version
=======
the version from GitHub
>>>>>>> origin/main
```

Open the file, delete the three marker lines, keep the text you want, then:

```bash
git add <the-file>
git rebase --continue      # if you were pulling with rebase
```

If it gets messy and you want out: `git rebase --abort` returns you to before the pull.

### "I'm on a weird branch / detached HEAD"

```bash
git checkout main
```

If it complains about uncommitted changes, either commit them or stash them:

```bash
git stash              # shelve everything temporarily
git checkout main
git stash pop          # bring the changes back
```

### The universal escape hatch

Almost nothing in git is permanently lost, even things that look gone:

```bash
git reflog             # every state your repo has been in, with hashes
git checkout <hash>    # go look at one
```

If you've truly tangled something and don't want to think about it: your files are on GitHub,
so the brute-force fix is to clone fresh into a new folder and copy your uncommitted work
across. Inelegant, always works, and there's no shame in it.

---

## Part 5 — Specific to this bootcamp

**Commit at the end of every lab day.** Not weekly. The dated daily cadence is the portfolio
evidence — 24 commits on 24 consecutive working days tells a story that one bulk upload does not.

**What is deliberately NOT committed** (see `.gitignore`):

| Excluded | Why |
|---|---|
| `.env` | API keys. Never. |
| `.venv/` | Hundreds of MB, and rebuildable with `make setup` |
| `data/index/`, `chroma/`, `qdrant_storage/` | Generated; rebuildable |
| `teaching/recordings/*.mov` | Too large for GitHub |
| `.cost_log.jsonl` | Your spend log — keep it local |
| `__pycache__/` | Build artifacts |

**What definitely IS committed:** every lab file you write, `src/fdekit/`, your evals and
scorecards, `LEARNING_LOG.md`, `PROGRESS.md`, and the capstone. Those are the work.

**By Day 24** you'll want three separate repos (Day 24 Block 2 covers this):
`fde-trainer-bootcamp`, `carrier-performance-copilot`, and `mcp-freight-ops`. Extract the
latter two with clean histories when you get there — don't worry about it now.

---

## Part 6 — The cheat sheet

Print this or keep it in a tab.

```bash
# ── daily ────────────────────────────────────────────────────
git status                      # what changed
git add -A                      # stage everything
git commit -m "Day NN: what"    # save to local history
git push                        # publish to GitHub
make ship M="Day NN: what"      # all four, plus lint and tests

# ── looking around ───────────────────────────────────────────
git log --oneline -10           # recent commits          (q to quit)
git diff                        # unstaged changes        (q to quit)
git diff --staged               # what you're committing  (q to quit)
git show HEAD                   # your last commit in full

# ── undo ─────────────────────────────────────────────────────
git restore <file>              # discard edits to a file  ← destructive
git restore --staged <file>     # unstage, keep the edits
git reset --soft HEAD~1         # undo last commit, keep changes (if unpushed)
git stash / git stash pop       # shelve work / bring it back

# ── when stuck ───────────────────────────────────────────────
q                               # quit a pager
Esc :wq                         # quit vim, saving
git pull                        # push rejected? pull first
git reflog                      # find any state you've been in
git rebase --abort              # back out of a messy pull

# ── setup, once ──────────────────────────────────────────────
git remote -v                   # where does this push to
git config --global --list      # what have I configured
ssh -T git@github.com           # is my SSH key working
```

---

## One habit worth building now

Run `git status` **before** every `git add -A`, and actually read the output.

It takes three seconds. It's how you catch the `.env` you forgot, the 400 MB file you didn't
mean to include, and the twelve `__pycache__` directories. Every experienced engineer does
this reflexively, and it's the single highest-return git habit there is.
