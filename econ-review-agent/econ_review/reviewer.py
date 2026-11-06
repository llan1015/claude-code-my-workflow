"""The single-call review pipeline: budget precheck -> API call -> validated review.

Uses `client.messages.parse` with the `PaperReview` Pydantic model, so the
response either validates against the schema or the call raises — no JSON
scraping, no silent drift.

The Anthropic client resolves credentials itself (ANTHROPIC_API_KEY env var, or
a profile from `ant auth login`). This module never handles key material.
"""

from __future__ import annotations

from dataclasses import dataclass

from .budget import Caps, Ledger, cost_usd, estimate_input_tokens, precheck
from .prompts import SYSTEM_PROMPT, build_user_message
from .schema import PaperReview

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_MAX_TOKENS = 8000


class ReviewRefusedError(RuntimeError):
    """The model declined the request (stop_reason == 'refusal')."""


class ReviewTruncatedError(RuntimeError):
    """The response hit max_tokens before completing the review."""


@dataclass
class ReviewResult:
    review: PaperReview
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


def review_paper(
    paper_text: str,
    *,
    title: str | None = None,
    client=None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    ledger: Ledger | None = None,
    caps: Caps | None = None,
) -> ReviewResult:
    """Review one paper excerpt. Raises BudgetExceededError before any spend
    if the worst case would breach a cap."""
    ledger = ledger or Ledger()
    user_message = build_user_message(paper_text, title=title)

    precheck(
        model=model,
        est_input_tokens=estimate_input_tokens(SYSTEM_PROMPT + user_message),
        max_output_tokens=max_tokens,
        ledger=ledger,
        caps=caps,
    )

    if client is None:  # imported lazily so offline tests never need the SDK configured
        import anthropic

        client = anthropic.Anthropic()

    response = client.messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_format=PaperReview,
    )

    if response.stop_reason == "refusal":
        detail = getattr(response, "stop_details", None)
        raise ReviewRefusedError(f"Model declined the request. stop_details={detail!r}")
    if response.stop_reason == "max_tokens":
        raise ReviewTruncatedError(
            f"Hit max_tokens={max_tokens} before finishing. Re-run with a higher "
            "--max-tokens (budget precheck will re-apply)."
        )

    usage = response.usage
    actual = cost_usd(model, usage.input_tokens, usage.output_tokens)
    ledger.record(
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cost=actual,
        label=title or paper_text.strip().splitlines()[0][:80],
    )

    return ReviewResult(
        review=response.parsed_output,
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cost_usd=actual,
    )
