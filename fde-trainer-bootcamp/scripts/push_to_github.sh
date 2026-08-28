#!/usr/bin/env bash
# One-shot: initialise this folder as a git repo and push it to GitHub.
# Safe to re-run — every step checks before acting.
#
#   bash scripts/push_to_github.sh
#
# Requires: git, and either an SSH key on your GitHub account (recommended)
# or a personal access token. See GIT_GUIDE.md §1.5.
set -uo pipefail

REPO_SSH="git@github.com:naramsettisiva/BecomeFDE.git"
REPO_HTTPS="https://github.com/naramsettisiva/BecomeFDE.git"

cd "$(cd "$(dirname "$0")/.." && pwd)"

if [ -t 1 ]; then
  OK=$'\033[32m'; BAD=$'\033[31m'; WARN=$'\033[33m'; DIM=$'\033[2m'; B=$'\033[1m'; Z=$'\033[0m'
else OK=""; BAD=""; WARN=""; DIM=""; B=""; Z=""; fi
say(){ printf "\n%s==> %s%s\n" "$B" "$1" "$Z"; }
ok(){  printf "  %s[ ok ]%s %s\n" "$OK" "$Z" "$1"; }
bad(){ printf "  %s[fail]%s %s\n" "$BAD" "$Z" "$1"; }
warn(){ printf "  %s[note]%s %s\n" "$WARN" "$Z" "$1"; }
dim(){ printf "  %s%s%s\n" "$DIM" "$1" "$Z"; }

say "Pushing to $REPO_SSH"
dim "Working from: $(pwd)"

# ── 1. git present and identity set ─────────────────────────────────────────
command -v git >/dev/null 2>&1 || { bad "git not found — brew install git"; exit 1; }
if [ -z "$(git config --global user.name || true)" ] || [ -z "$(git config --global user.email || true)" ]; then
  bad "git identity not set. Run first:  bash scripts/git_setup.sh"
  exit 1
fi
ok "git $(git --version | awk '{print $3}') as $(git config --global user.name)"

# ── 2. choose transport ─────────────────────────────────────────────────────
say "Checking GitHub authentication"
TRANSPORT=""
if ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
  ok "SSH key works"
  TRANSPORT="$REPO_SSH"
else
  warn "SSH not authenticated with GitHub."
  dim "Best fix (2 min, permanent):   bash scripts/git_setup.sh"
  dim "That generates a key, copies it to your clipboard, and tells you where to paste it."
  printf "\n  %sUse HTTPS instead for now? You'll be prompted for a Personal Access Token.%s [y/N] " "$WARN" "$Z"
  read -r r
  case "$r" in
    y|Y|yes) TRANSPORT="$REPO_HTTPS"
             dim "Create a token at: github.com/settings/tokens  (scope: repo)"
             dim "Paste it as the PASSWORD when prompted — your GitHub password will not work." ;;
    *) bad "Stopped. Set up SSH first, then re-run this script."; exit 1 ;;
  esac
fi

# ── 3. repo init ────────────────────────────────────────────────────────────
say "Repository"
if [ -d .git ]; then ok "already a git repo"
else git init -q && ok "initialised"; fi
git branch -M main 2>/dev/null; ok "branch: main"

# ── 4. remote ───────────────────────────────────────────────────────────────
if git remote get-url origin >/dev/null 2>&1; then
  CUR="$(git remote get-url origin)"
  if [ "$CUR" != "$TRANSPORT" ]; then
    git remote set-url origin "$TRANSPORT"; ok "remote updated -> $TRANSPORT"
  else ok "remote already $CUR"; fi
else
  git remote add origin "$TRANSPORT"; ok "remote added -> $TRANSPORT"
fi

# ── 5. safety: nothing secret, nothing huge ─────────────────────────────────
say "Safety check — what would be published"
FAIL=0
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  bad ".env IS TRACKED. Fix, then ROTATE those keys:"
  dim "  git rm --cached .env && git commit -m 'remove .env'"
  FAIL=1
else ok ".env not tracked"; fi

grep -q '^\.env$' .gitignore 2>/dev/null && ok ".gitignore excludes .env" \
  || { bad ".gitignore missing a '.env' line"; FAIL=1; }

BIG="$(git status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//' | while IFS= read -r f; do
  [ -f "$f" ] || continue
  SZ="$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0)"
  [ "$SZ" -gt 52428800 ] && printf "%s (%s MB)\n" "$f" "$((SZ/1048576))"
done)"
if [ -n "$BIG" ]; then
  bad "Files over 50 MB — GitHub will warn or refuse:"; printf "      %s\n" "$BIG"; FAIL=1
else ok "no oversized files"; fi

[ "$FAIL" -eq 0 ] || { bad "Fix the above, then re-run."; exit 1; }

# ── 6. commit + push ────────────────────────────────────────────────────────
say "Staging"
git add -A
N="$(git diff --cached --numstat | wc -l | tr -d ' ')"
if [ "$N" = "0" ] && git rev-parse HEAD >/dev/null 2>&1; then
  ok "nothing new to commit"
else
  git commit -qm "${1:-FDE Trainer Bootcamp: 24 learn modules, 24 labs, AWS lane, toolkit}"
  ok "committed $N file(s)"
fi

say "Pushing"
if git push -u origin main; then
  printf "\n"
  ok "Done."
  dim "https://github.com/naramsettisiva/BecomeFDE"
  printf "\n"
  dim "From now on, every day:   make ship M=\"Day 07: what you did\""
else
  printf "\n"
  bad "Push failed. Most likely causes:"
  dim "  · SSH key not on your GitHub account   -> bash scripts/git_setup.sh"
  dim "  · HTTPS token expired or wrong scope   -> github.com/settings/tokens (scope: repo)"
  dim "  · Repo has commits you don't have      -> git pull --rebase && git push"
  exit 1
fi
