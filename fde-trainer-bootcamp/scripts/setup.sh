#!/usr/bin/env bash
# FDE Trainer Bootcamp — one-time environment setup (macOS)
# Usage: bash scripts/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say() { printf "\n\033[1;36m==> %s\033[0m\n" "$1"; }
warn() { printf "\033[1;33m[!] %s\033[0m\n" "$1"; }

say "FDE Trainer Bootcamp setup — $ROOT"

# ---------------------------------------------------------------- prerequisites
for cmd in git python3; do
  command -v "$cmd" >/dev/null 2>&1 || { warn "Missing '$cmd'. Install it and re-run."; exit 1; }
done

if ! command -v uv >/dev/null 2>&1; then
  say "Installing uv (fast Python package manager)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# ---------------------------------------------------------------- virtualenv
say "Creating virtual environment (.venv) on Python 3.12"
uv venv --python 3.12 .venv

say "Installing dependencies (this takes a few minutes the first time)"
# shellcheck disable=SC1091
source .venv/bin/activate
uv pip install -r requirements.txt

# ---------------------------------------------------------------- secrets
if [ ! -f .env ]; then
  say "Creating .env from template"
  cp .env.example .env
  warn "Edit .env and paste your API keys before running any [PAID] lab."
fi

# ---------------------------------------------------------------- git
if [ ! -d .git ]; then
  say "Initialising git repository"
  git init -q
  git add -A
  git commit -qm "Day 0: bootcamp scaffold"
  echo "Now create an empty GitHub repo and run:"
  echo "  git remote add origin git@github.com:<you>/fde-trainer-bootcamp.git"
  echo "  git push -u origin main"
fi

# ---------------------------------------------------------------- ollama
if command -v ollama >/dev/null 2>&1; then
  say "Checking local models"
  ollama list || true
  echo "If llama3.1:8b or nomic-embed-text are missing:"
  echo "  ollama pull llama3.1:8b && ollama pull nomic-embed-text"
else
  warn "ollama not found. brew install ollama  (needed for all free/local labs)"
fi

say "Setup complete. Next:"
echo "  source .venv/bin/activate"
echo "  python scripts/doctor.py"
