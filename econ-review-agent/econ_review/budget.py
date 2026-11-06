"""Budget guard: per-run and cumulative USD caps plus a local usage ledger.

The $100 credit expires 2026-12-01, so every call is pre-checked against a
WORST-CASE cost (full `max_tokens` output) and logged with its ACTUAL cost
afterwards. The ledger is a local JSON file (gitignored) — it is the source of
truth for "how much of the credit has this pilot spent".
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

# USD per 1M tokens (input, output). Anthropic first-party API list prices,
# cached 2026-11-06 — verify at https://claude.com/pricing before trusting
# large-batch estimates.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
}

DEFAULT_LEDGER = Path(__file__).resolve().parent.parent / "usage_ledger.json"


class BudgetExceededError(RuntimeError):
    """Raised BEFORE an API call whose worst-case cost would breach a cap."""


class UnknownModelError(ValueError):
    """Model has no price entry — refuse to estimate rather than undercount."""


def estimate_input_tokens(text: str) -> int:
    """Conservative local estimate (~3 chars/token) for the pre-call budget check.

    This deliberately OVERestimates English text (typically ~4 chars/token) so
    the guard errs on the side of blocking. Actual billing uses the token
    counts the API reports in `response.usage`.
    """
    return max(1, len(text) // 3)


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in PRICES_PER_MTOK:
        raise UnknownModelError(
            f"No price entry for '{model}'. Add it to PRICES_PER_MTOK in budget.py."
        )
    p_in, p_out = PRICES_PER_MTOK[model]
    return (input_tokens * p_in + output_tokens * p_out) / 1_000_000


@dataclass
class Caps:
    per_run_usd: float = float(os.environ.get("ECON_REVIEW_MAX_USD_PER_RUN", "0.50"))
    cumulative_usd: float = float(os.environ.get("ECON_REVIEW_BUDGET_USD", "90.0"))


class Ledger:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else DEFAULT_LEDGER

    def _load(self) -> list[dict]:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return []

    def total_usd(self) -> float:
        return sum(e["cost_usd"] for e in self._load())

    def record(self, *, model: str, input_tokens: int, output_tokens: int,
               cost: float, label: str = "") -> None:
        entries = self._load()
        entries.append({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "label": label,
        })
        self.path.write_text(json.dumps(entries, indent=2))


def precheck(*, model: str, est_input_tokens: int, max_output_tokens: int,
             ledger: Ledger, caps: Caps | None = None) -> float:
    """Raise BudgetExceededError if the worst-case cost would breach a cap.

    Returns the worst-case cost estimate (useful for --dry-run display).
    """
    caps = caps or Caps()
    worst_case = cost_usd(model, est_input_tokens, max_output_tokens)
    if worst_case > caps.per_run_usd:
        raise BudgetExceededError(
            f"Worst-case cost ${worst_case:.3f} exceeds per-run cap "
            f"${caps.per_run_usd:.2f} (ECON_REVIEW_MAX_USD_PER_RUN). "
            f"Lower --max-tokens, shorten the input, or raise the cap."
        )
    spent = ledger.total_usd()
    if spent + worst_case > caps.cumulative_usd:
        raise BudgetExceededError(
            f"Cumulative spend ${spent:.2f} + worst-case ${worst_case:.3f} would exceed "
            f"the pilot budget ${caps.cumulative_usd:.2f} (ECON_REVIEW_BUDGET_USD)."
        )
    return worst_case
