# FDE Trainer Bootcamp — macOS
#
# Tab-indented recipes (make requires literal tabs).
# Everything assumes .venv is active except the aws-* targets, which only need the AWS CLI.

SHELL := /bin/bash
.DEFAULT_GOAL := help

PY  := python3
AWS := AWS_PROFILE=$${AWS_PROFILE:-fde} AWS_REGION=$${AWS_REGION:-us-east-1}

## ── core lane ───────────────────────────────────────────────────────────────

help:            ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[1m%-16s\033[0m %s\n", $$1, $$2}'

setup:           ## One-time environment setup (venv, deps, .env, git)
	bash scripts/setup.sh

git-setup:       ## One-time git + GitHub setup (identity, editor, SSH key, remote)
	bash scripts/git_setup.sh

git-check:       ## Pre-push safety check — is .env tracked? anything oversized?
	@git status --short
	@git ls-files --error-unmatch .env >/dev/null 2>&1 \
	  && echo "  !! .env IS TRACKED — git rm --cached .env, then ROTATE the keys" \
	  || echo "  ok  .env not tracked"

doctor:          ## Check the local environment
	$(PY) scripts/doctor.py

corpus:          ## (Re)generate the freight corpus
	$(PY) scripts/build_corpus.py

test:            ## Run the test suite
	pytest -q

lint:            ## Format and lint
	ruff check src/ labs/ scripts/ --fix && ruff format src/ labs/ scripts/

cost:            ## Bootcamp LLM spend to date (local log)
	$(PY) -m fdekit.cost

ship:            ## Lint, test, commit, push — end of every day
	@$(MAKE) lint test
	@git add -A && git commit -m "$${M:-daily ship}" && git push

## ── aws lane ────────────────────────────────────────────────────────────────

aws-preflight:   ## Verify the AWS lane is ready (run before Day 1)
	@$(AWS) bash scripts/aws/preflight.sh

aws-cost:        ## Month-to-date AWS spend vs the $50 budget — run every morning
	@$(AWS) bash scripts/aws/cost.sh

aws-nuke:        ## Delete every bootcamp AWS resource — run after EVERY aws lab
	@$(AWS) bash scripts/aws/nuke.sh

aws-nuke-dry:    ## Show what aws-nuke would delete, without deleting
	@$(AWS) bash scripts/aws/nuke.sh --dry

aws-budget:      ## Create the $50 budget + alerts (EMAIL=you@example.com)
	@test -n "$(EMAIL)" || (echo "Usage: make aws-budget EMAIL=you@example.com" && exit 1)
	@$(AWS) bash scripts/aws/budget.sh "$(EMAIL)"

aws-login:       ## Refresh the SSO session (when things start 403ing)
	@aws sso login --profile $${AWS_PROFILE:-fde}

aws-models:      ## List the Bedrock models you have access to
	@$(AWS) aws bedrock list-foundation-models \
	  --query 'modelSummaries[?contains(modelId,`nova`)||contains(modelId,`claude`)||contains(modelId,`titan-embed`)].modelId' \
	  --output table

.PHONY: help setup git-setup git-check doctor corpus test lint cost ship \
        aws-preflight aws-cost aws-nuke aws-nuke-dry aws-budget aws-login aws-models
