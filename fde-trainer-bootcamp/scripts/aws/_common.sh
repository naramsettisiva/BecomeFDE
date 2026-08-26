#!/usr/bin/env bash
# Shared helpers for the AWS lane.
#
# macOS notes baked in here so no other script has to think about them:
#   - macOS ships bash 3.2. No associative arrays, no ${var,,}, no mapfile.
#   - BSD date: `date -v-7d`, not `date -d '-7 days'`.
#   - BSD sed needs `-i ''` for in-place edits.
# Sourced, not executed:  . "$(dirname "$0")/_common.sh"

AWS_PROFILE="${AWS_PROFILE:-fde}"
AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_PROFILE AWS_REGION

# Every resource this course creates carries these two tags. aws-nuke finds
# things by tag, which is why nothing gets orphaned.
FDE_TAG_KEY="Project"
FDE_TAG_VALUE="fde-bootcamp"
FDE_PREFIX="fde-bootcamp"

# ── output ──────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_BAD=$'\033[31m'; C_WARN=$'\033[33m'
  C_DIM=$'\033[2m';  C_B=$'\033[1m';   C_0=$'\033[0m'
else
  C_OK=""; C_BAD=""; C_WARN=""; C_DIM=""; C_B=""; C_0=""
fi

say()  { printf "\n%s==> %s%s\n" "$C_B" "$1" "$C_0"; }
ok()   { printf "  %s[ ok ]%s %s\n"   "$C_OK"   "$C_0" "$1"; }
bad()  { printf "  %s[fail]%s %s\n"   "$C_BAD"  "$C_0" "$1"; }
warn() { printf "  %s[warn]%s %s\n"   "$C_WARN" "$C_0" "$1"; }
dim()  { printf "  %s%s%s\n"          "$C_DIM"  "$1"   "$C_0"; }

die() { bad "$1"; exit 1; }

# ── macOS-safe date helpers ─────────────────────────────────────────────────
# BSD date only. Do not "fix" these with GNU syntax.
days_ago()  { date -u -v-"$1"d +%Y-%m-%d; }
today()     { date -u +%Y-%m-%d; }
tomorrow()  { date -u -v+1d +%Y-%m-%d; }
month_start(){ date -u +%Y-%m-01; }
stamp()     { date -u +%Y%m%dT%H%M%SZ; }

# ── preconditions ───────────────────────────────────────────────────────────
need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing '$1'. Run: brew install $2"
}

need_aws() {
  need_cmd aws awscli
  need_cmd jq jq
  case "$(aws --version 2>&1)" in
    aws-cli/2*) : ;;
    *) die "AWS CLI v2 required. 'brew install awscli' and remove any pip-installed v1." ;;
  esac
  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    die "No valid AWS session. Run: aws sso login --profile $AWS_PROFILE"
  fi
}

account_id() { aws sts get-caller-identity --query Account --output text; }

# Unique-ish suffix so bucket names don't collide, derived from the account id.
# Stable across runs, which matters: teardown must be able to find what setup made.
fde_suffix() { account_id | tail -c 7; }

# ── tagging ─────────────────────────────────────────────────────────────────
tag_args_cli() { printf 'Key=%s,Value=%s' "$FDE_TAG_KEY" "$FDE_TAG_VALUE"; }
tag_args_json() { printf '[{"Key":"%s","Value":"%s"}]' "$FDE_TAG_KEY" "$FDE_TAG_VALUE"; }

# ── confirmation ────────────────────────────────────────────────────────────
confirm() {
  printf "%s%s%s [y/N] " "$C_WARN" "$1" "$C_0"
  read -r _reply
  case "$_reply" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}
