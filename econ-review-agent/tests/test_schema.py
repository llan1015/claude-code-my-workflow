import pytest
from pydantic import ValidationError

from econ_review.schema import PaperReview


def test_valid_payload_parses(sample_review_dict):
    review = PaperReview.model_validate(sample_review_dict)
    assert review.identification.method == "difference-in-differences"
    assert review.key_assumptions[0].testability.startswith("partially")


def test_missing_required_field_rejected(sample_review_dict):
    bad = dict(sample_review_dict)
    del bad["research_question"]
    with pytest.raises(ValidationError):
        PaperReview.model_validate(bad)


def test_invalid_severity_rejected(sample_review_dict):
    bad = dict(sample_review_dict)
    bad["endogeneity_concerns"] = [
        {**sample_review_dict["endogeneity_concerns"][0], "severity": "catastrophic"}
    ]
    with pytest.raises(ValidationError):
        PaperReview.model_validate(bad)


def test_credibility_bounds(sample_review_dict):
    bad = dict(sample_review_dict)
    bad["identification_credibility"] = 6
    with pytest.raises(ValidationError):
        PaperReview.model_validate(bad)


def test_round_trip_json(sample_review):
    dumped = sample_review.model_dump_json()
    assert PaperReview.model_validate_json(dumped) == sample_review
