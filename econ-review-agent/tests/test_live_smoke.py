"""Live smoke test — runs ONLY when ANTHROPIC_API_KEY is set.

Cost: one real Opus 5.5 call, roughly $0.05-$0.15 depending on thinking length.
Run from the econ-review-agent directory:

    ANTHROPIC_API_KEY=... pytest tests/test_live_smoke.py -v
"""

import os
from pathlib import Path

import pytest

from econ_review.reviewer import review_paper

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — live smoke test skipped",
)

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "minimum_wage_did.md"


def test_live_review_of_did_example(tmp_path):
    from econ_review.budget import Caps, Ledger

    result = review_paper(
        EXAMPLE.read_text(),
        title="Minimum wage border DiD (synthetic)",
        ledger=Ledger(tmp_path / "live_ledger.json"),
        caps=Caps(per_run_usd=0.50, cumulative_usd=90.0),
    )

    review = result.review
    # Substantive sanity checks, not just schema validity:
    assert review.identification.method in ("difference-in-differences", "event study")
    assert len(review.key_assumptions) >= 1
    assert any("parallel" in a.assumption.lower() for a in review.key_assumptions), \
        "A border-pair DiD review should surface parallel trends"
    assert len(review.referee_questions) >= 3
    assert 1 <= review.identification_credibility <= 5
    assert result.cost_usd < 0.50
    print(f"\nLive smoke OK: ${result.cost_usd:.4f} "
          f"({result.input_tokens} in / {result.output_tokens} out)")
