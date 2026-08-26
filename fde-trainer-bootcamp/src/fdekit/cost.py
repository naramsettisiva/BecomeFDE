"""Token + dollar accounting.

Every FDE gets asked "what does this cost at 10,000 users?" in week one of an
engagement. Start measuring on Day 1 so that by Day 18 you have four weeks of
real data instead of a guess.

Prices are USD per 1M tokens and WILL drift — treat them as a config you refresh,
not a constant. That habit is itself the lesson.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[2] / ".cost_log.jsonl"

# USD per 1M tokens: (input, output). Local models are free but not costless —
# see Day 18, where you convert wall-clock + electricity into an effective rate.
PRICES: dict[str, tuple[float, float]] = {
    # --- direct providers ---
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    # --- amazon bedrock (us-east-1, Aug 2026 — refresh before quoting) ---
    # Nova is 6-30x cheaper than Claude. Default your labs to Nova; reserve
    # Claude for judging and demos. See labs/aws/AWS_COST_DISCIPLINE.md.
    "amazon.nova-micro": (0.08, 0.24),
    "amazon.nova-lite": (0.30, 0.90),
    "amazon.nova-pro": (1.20, 3.60),
    "amazon.titan-embed-text-v2": (0.02, 0.0),
    "anthropic.claude-sonnet-4-6": (3.00, 15.00),
    "anthropic.claude-sonnet-4-5": (3.00, 15.00),
    "anthropic.claude-opus-4-8": (5.00, 25.00),
    "anthropic.claude-opus-4-7": (5.00, 25.00),
    # Legacy trap: 3.5 Sonnet moved to "Public Extended Access" Dec 2025 at
    # DOUBLE the price of current Sonnet, for a worse model. If you find this
    # model ID pinned in client code, that is a free cost win in week one.
    "anthropic.claude-3-5-sonnet": (6.00, 30.00),
}


def price_for(model: str) -> tuple[float, float]:
    for key, price in PRICES.items():
        if model.startswith(key):
            return price
    return (0.0, 0.0)  # local / unknown → free


def track(model: str, input_tokens: int, output_tokens: int) -> float:
    """Append one usage record and return its USD cost."""
    pin, pout = price_for(model)
    usd = (input_tokens / 1_000_000) * pin + (output_tokens / 1_000_000) * pout
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "usd": round(usd, 6),
        "lab": os.environ.get("FDE_LAB", "unknown"),
    }
    with LOG_PATH.open("a") as fh:
        fh.write(json.dumps(record) + "\n")
    return usd


@dataclass
class CostTracker:
    """Context manager for scoping cost to one block of work.

    with CostTracker("rag-v1 eval run") as c:
        ...
    print(c.usd)
    """

    label: str
    _start_bytes: int = field(default=0, init=False)
    usd: float = field(default=0.0, init=False)
    calls: int = field(default=0, init=False)
    input_tokens: int = field(default=0, init=False)
    output_tokens: int = field(default=0, init=False)

    def __enter__(self) -> "CostTracker":
        self._start_bytes = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
        return self

    def __exit__(self, *exc) -> None:
        if not LOG_PATH.exists():
            return
        with LOG_PATH.open() as fh:
            fh.seek(self._start_bytes)
            for line in fh:
                if not line.strip():
                    continue
                rec = json.loads(line)
                self.usd += rec["usd"]
                self.calls += 1
                self.input_tokens += rec["input_tokens"]
                self.output_tokens += rec["output_tokens"]

    def report(self) -> str:
        return (
            f"[{self.label}] {self.calls} calls · "
            f"{self.input_tokens:,} in / {self.output_tokens:,} out · "
            f"${self.usd:.4f}"
        )


def total_spend() -> float:
    if not LOG_PATH.exists():
        return 0.0
    total = 0.0
    with LOG_PATH.open() as fh:
        for line in fh:
            if line.strip():
                total += json.loads(line)["usd"]
    return total


if __name__ == "__main__":
    print(f"Bootcamp spend to date: ${total_spend():.4f}")
