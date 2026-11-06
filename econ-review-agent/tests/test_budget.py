import pytest

from econ_review.budget import (
    BudgetExceededError,
    Caps,
    Ledger,
    UnknownModelError,
    cost_usd,
    estimate_input_tokens,
    precheck,
)


def test_cost_matches_list_price():
    # Opus 5.5: $4/MTok in, $20/MTok out
    assert cost_usd("claude-opus-5-5", 1_000_000, 0) == pytest.approx(4.00)
    assert cost_usd("claude-opus-5-5", 0, 1_000_000) == pytest.approx(20.00)
    # Typical review: ~3K in, ~5K out
    assert cost_usd("claude-opus-5-5", 3000, 5000) == pytest.approx(0.112)


def test_unknown_model_refused():
    with pytest.raises(UnknownModelError):
        cost_usd("claude-nonexistent-9", 100, 100)


def test_input_estimate_is_conservative():
    text = "word " * 1000  # 5000 chars, ~1250 real tokens
    assert estimate_input_tokens(text) >= 1250


def test_ledger_accumulates(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    assert ledger.total_usd() == 0.0
    ledger.record(model="claude-opus-5-5", input_tokens=1000, output_tokens=2000,
                  cost=0.044, label="test")
    ledger.record(model="claude-opus-5-5", input_tokens=1000, output_tokens=2000,
                  cost=0.044, label="test2")
    assert ledger.total_usd() == pytest.approx(0.088)


def test_precheck_blocks_per_run_cap(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    caps = Caps(per_run_usd=0.01, cumulative_usd=90.0)
    with pytest.raises(BudgetExceededError, match="per-run cap"):
        precheck(model="claude-opus-5-5", est_input_tokens=5000,
                 max_output_tokens=8000, ledger=ledger, caps=caps)


def test_precheck_blocks_cumulative_cap(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.record(model="claude-opus-5-5", input_tokens=0, output_tokens=0,
                  cost=89.99, label="prior spend")
    caps = Caps(per_run_usd=0.50, cumulative_usd=90.0)
    with pytest.raises(BudgetExceededError, match="pilot budget"):
        precheck(model="claude-opus-5-5", est_input_tokens=5000,
                 max_output_tokens=8000, ledger=ledger, caps=caps)


def test_precheck_passes_and_returns_estimate(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    caps = Caps(per_run_usd=0.50, cumulative_usd=90.0)
    worst = precheck(model="claude-opus-5-5", est_input_tokens=3000,
                     max_output_tokens=8000, ledger=ledger, caps=caps)
    assert worst == pytest.approx(cost_usd("claude-opus-5-5", 3000, 8000))
