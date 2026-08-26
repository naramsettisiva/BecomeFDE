#!/usr/bin/env bash
# One-time git + GitHub setup for macOS. Idempotent — safe to re-run.
#
#   bash scripts/git_setup.sh
#
# Walks through everything in GIT_GUIDE.md Part 1. Asks before changing anything,
# and tells you what it did. Written for bash 3.2 (what /bin/bash is on macOS).
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -t 1 ]; then
  OK=$'\033[32m'; BAD=$'\033[31m'; WARN=$'\033[33m'; DIM=$'\033[2m'; B=$'\033[1m'; Z=$'\033[0m'
else
  OK=""; BAD=""; WARN=""; DIM=""; B=""; Z=""
fi
say()  { printf "\n%s==> %s%s\n" "$B" "$1" "$Z"; }
ok()   { printf "  %s[ ok ]%s %s\n" "$OK" "$Z" "$1"; }
bad()  { printf "  %s[fail]%s %s\n" "$BAD" "$Z" "$1"; }
warn() { printf "  %s[note]%s %s\n" "$WARN" "$Z" "$1"; }
dim()  { printf "  %s%s%s\n" "$DIM" "$1" "$Z"; }
ask()  { printf "%s%s%s " "$WARN" "$1" "$Z"; read -r REPLY; }

say "Git setup for the FDE bootcamp — $ROOT"
dim "Full explanations: GIT_GUIDE.md"

# ── 1. git present, and which one ───────────────────────────────────────────
say "1. Git installation"
if ! command -v git >/dev/null 2>&1; then
  bad "git not found. Run: brew install git"
  exit 1
fi
GITPATH="$(command -v git)"
ok "$(git --version)  at  $GITPATH"
case "$GITPATH" in
  /usr/bin/git)
    warn "That's Apple's git (older). Works fine, but for the current version:"
    dim "  brew install git"
    dim "  echo 'eval \"\$(/opt/homebrew/bin/brew shellenv)\"' >> ~/.zprofile && exec zsh -l"
    ;;
esac

# ── 2. identity ─────────────────────────────────────────────────────────────
say "2. Your identity on commits"
CUR_NAME="$(git config --global user.name || true)"
CUR_MAIL="$(git config --global user.email || true)"

if [ -n "$CUR_NAME" ] && [ -n "$CUR_MAIL" ]; then
  ok "name:  $CUR_NAME"
  ok "email: $CUR_MAIL"
  ask "Keep these? [Y/n]"
  case "$REPLY" in n|N) CUR_NAME=""; CUR_MAIL="" ;; esac
fi

if [ -z "$CUR_NAME" ]; then
  ask "Your name (as it should appear on commits):"
  [ -n "$REPLY" ] && git config --global user.name "$REPLY" && ok "name set"
fi
if [ -z "$CUR_MAIL" ]; then
  dim "Use the SAME email as your GitHub account, or GitHub's no-reply address"
  dim "(Settings > Emails > Keep my email addresses private)."
  dim "If they don't match, your commits won't link to your profile."
  ask "Your email:"
  [ -n "$REPLY" ] && git config --global user.email "$REPLY" && ok "email set"
fi

# ── 3. editor — before vim ambushes anyone ──────────────────────────────────
say "3. Default editor"
CUR_ED="$(git config --global core.editor || true)"
if [ -n "$CUR_ED" ]; then
  ok "already set to: $CUR_ED"
else
  warn "Unset means git opens VIM when you commit without -m. Vim does not"
  warn "tell you how to leave. (It's Esc then :wq — write that down anyway.)"
  dim "  1) nano        simple, shows its shortcuts at the bottom  [recommended]"
  dim "  2) VS Code     needs 'code' on your PATH"
  dim "  3) leave as-is"
  ask "Choose [1/2/3]:"
  case "$REPLY" in
    1) git config --global core.editor "nano"; ok "editor = nano" ;;
    2) if command -v code >/dev/null 2>&1; then
         git config --global core.editor "code --wait"; ok "editor = code --wait"
       else
         bad "'code' not on PATH. In VS Code: Cmd+Shift+P > 'Shell Command: Install code command'"
         git config --global core.editor "nano"; warn "fell back to nano for now"
       fi ;;
    *) warn "left unset — remember Esc :wq" ;;
  esac
fi

# ── 4. sensible defaults ────────────────────────────────────────────────────
say "4. Settings that prevent specific problems"
set_cfg() {
  if [ "$(git config --global "$1" || true)" = "$2" ]; then
    dim "$1 = $2  (already)"
  else
    git config --global "$1" "$2"; ok "$1 = $2"
  fi
}
set_cfg init.defaultBranch main       # GitHub expects 'main'
set_cfg pull.rebase true              # linear history — it's a portfolio
set_cfg push.default simple
set_cfg color.ui auto
set_cfg credential.helper osxkeychain # only used on the HTTPS fallback path

# ── 5. ssh key ──────────────────────────────────────────────────────────────
say "5. SSH key — how your Mac proves it's you"
KEY="$HOME/.ssh/id_ed25519"

if [ -f "$KEY" ]; then
  ok "key exists: $KEY"
else
  dim "SSH means you never deal with expiring tokens. 5 minutes now, silent forever after."
  ask "Generate an SSH key? [Y/n]"
  case "$REPLY" in
    n|N) warn "skipped — you'll need HTTPS + a personal access token instead" ;;
    *)
      MAIL="$(git config --global user.email)"
      mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
      dim "A passphrase encrypts the key on disk. With Keychain you're asked once."
      dim "Press Return twice for no passphrase."
      ssh-keygen -t ed25519 -C "$MAIL" -f "$KEY" && ok "key generated"
      ;;
  esac
fi

if [ -f "$KEY" ]; then
  # macOS-specific: UseKeychain is not a thing on Linux.
  if ! grep -q "Host github.com" "$HOME/.ssh/config" 2>/dev/null; then
    cat >> "$HOME/.ssh/config" <<'EOF'

Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
EOF
    chmod 600 "$HOME/.ssh/config"
    ok "~/.ssh/config configured for github.com (macOS Keychain)"
  else
    dim "~/.ssh/config already has a github.com entry"
  fi

  eval "$(ssh-agent -s)" >/dev/null 2>&1
  ssh-add --apple-use-keychain "$KEY" >/dev/null 2>&1 && ok "key loaded into agent + Keychain" \
    || warn "ssh-add reported an issue — re-run: ssh-add --apple-use-keychain $KEY"

  say "Add this PUBLIC key to GitHub"
  printf "\n"
  cat "$KEY.pub"
  printf "\n"
  if command -v pbcopy >/dev/null 2>&1; then
    pbcopy < "$KEY.pub" && ok "copied to your clipboard"
  fi
  dim "GitHub > avatar > Settings > SSH and GPG keys > New SSH key"
  dim "Title it e.g. 'MacBook - FDE bootcamp'. Paste. Add."
  printf "\n"
  ask "Press Return once you've added it..."

  say "Testing the connection"
  OUT="$(ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 || true)"
  case "$OUT" in
    *successfully\ authenticated*)
      ok "$(printf '%s' "$OUT" | head -1)"
      dim "'does not provide shell access' in that message is SUCCESS, not an error." ;;
    *)
      bad "Not authenticated yet:"
      printf "      %s\n" "$OUT"
      dim "Check the key was added at github.com/settings/keys, then re-run this script." ;;
  esac
fi

# ── 6. this repository ──────────────────────────────────────────────────────
say "6. This repository"
if [ -d .git ]; then
  ok "git repo initialised"
else
  git init -q && git branch -M main && ok "repo initialised on branch main"
fi

BR="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
[ "$BR" = "main" ] || { git branch -M main; ok "branch renamed to main"; }

if git remote get-url origin >/dev/null 2>&1; then
  ok "remote origin: $(git remote get-url origin)"
else
  warn "No remote yet. First create an EMPTY repo on GitHub:"
  dim "  github.com/new  ->  name: fde-trainer-bootcamp"
  dim "  Do NOT tick README / .gitignore / license — you already have them locally."
  dim "  (Ticking them causes 'refusing to merge unrelated histories' on first push.)"
  printf "\n"
  ask "Your GitHub username (blank to skip):"
  if [ -n "$REPLY" ]; then
    git remote add origin "git@github.com:$REPLY/fde-trainer-bootcamp.git"
    ok "remote added: $(git remote get-url origin)"
  fi
fi

# ── 7. safety check before anything is published ────────────────────────────
say "7. Safety check — what would be published"
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  bad ".env IS TRACKED BY GIT. Fix before pushing:"
  dim "  git rm --cached .env && git commit -m 'remove .env from tracking'"
  dim "  Then ROTATE any key that was in it — assume it is compromised."
else
  ok ".env is not tracked"
fi
grep -q '^\.env$' .gitignore 2>/dev/null && ok ".gitignore excludes .env" \
  || bad ".gitignore is missing a '.env' line — add it now"

BIG="$(git status --porcelain 2>/dev/null | awk '{print $2}' | while read -r f; do
  [ -f "$f" ] || continue
  # BSD stat: -f%z. GNU would be -c%s. This script is macOS-only by design.
  SZ="$(stat -f%z "$f" 2>/dev/null || echo 0)"
  [ "$SZ" -gt 52428800 ] && printf "%s (%s MB)\n" "$f" "$((SZ/1048576))"
done)"
if [ -n "$BIG" ]; then
  bad "Files over 50 MB — GitHub will warn or refuse:"
  printf "      %s\n" "$BIG"
  dim "Usually a screen recording. Keep those local; .gitignore already excludes *.mov"
else
  ok "no oversized files staged"
fi

# ── done ────────────────────────────────────────────────────────────────────
say "Setup complete. Your first push:"
cat <<'EOF'
    git status                    # READ THIS. Every time. Three seconds.
    git add -A
    git commit -m "Day 0: bootcamp scaffold and AWS lane"
    git push -u origin main       # -u only on the first push; after that just: git push

  Then every day:
    make ship M="Day 07: agent loop from scratch, five failure modes"

  Stuck? GIT_GUIDE.md Part 4 covers the panics — including how to leave vim.
EOF
printf "\n"
