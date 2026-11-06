"""Offline tests of the review pipeline using a fake client (no API calls)."""

from types import SimpleNamespace

import pytest

from econ_review.budget import Caps, Ledger
from econ_review.reviewer import (
    ReviewRefusedError,
    ReviewTruncatedError,
    review_paper,
)


class FakeMessages:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    def parse(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


def make_client(response):
    return SimpleNamespace(messages=FakeMessages(response))


def ok_response(sample_review):
    return SimpleNamespace(
        parsed_output=sample_review,
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=3000, output_tokens=5000),
    )


def test_happy_path_returns_review_and_logs_cost(tmp_path, sample_review):
    ledger = Ledger(tmp_path / "ledger.json")
    client = make_client(ok_response(sample_review))

    result = review_paper(
        "Abstract text. " * 50,
        title="Border DiD",
        client=client,
        ledger=ledger,
        caps=Caps(per_run_usd=0.50, cumulative_usd=90.0),
    )

    assert result.review == sample_review
    # 3000 in * $4/M + 5000 out * $20/M = 0.012 + 0.100
    assert result.cost_usd == pytest.approx(0.112)
    assert ledger.total_usd() == pytest.approx(0.112)

    # The request used structured outputs with the schema and the system prompt
    kwargs = client.messages.last_kwargs
    assert kwargs["output_format"].__name__ == "PaperReview"
    assert "referee" in kwargs["system"].lower()
    assert "<paper_excerpt>" in kwargs["messages"][0]["content"]


def test_refusal_raises_and_spends_nothing_in_ledger(tmp_path, sample_review):
    ledger = Ledger(tmp_path / "ledger.json")
    resp = ok_response(sample_review)
    resp.stop_reason = "refusal"
    with pytest.raises(ReviewRefusedError):
        review_paper("text", client=make_client(resp), ledger=ledger,
                     caps=Caps(per_run_usd=0.50, cumulative_usd=90.0))
    assert ledger.total_usd() == 0.0


def test_truncation_raises(tmp_path, sample_review):
    resp = ok_response(sample_review)
    resp.stop_reason = "max_tokens"
    with pytest.raises(ReviewTruncatedError):
        review_paper("text", client=make_client(resp),
                     ledger=Ledger(tmp_path / "l.json"),
                     caps=Caps(per_run_usd=0.50, cumulative_usd=90.0))


def test_budget_block_prevents_api_call(tmp_path, sample_review):
    client = make_client(ok_response(sample_review))
    from econ_review.budget import BudgetExceededError

    with pytest.raises(BudgetExceededError):
        review_paper("text " * 10000, client=client,
                     ledger=Ledger(tmp_path / "l.json"),
                     caps=Caps(per_run_usd=0.001, cumulative_usd=90.0))
    assert client.messages.last_kwargs is None  # API never touched
