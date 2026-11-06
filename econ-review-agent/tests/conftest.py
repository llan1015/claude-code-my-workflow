import sys
from pathlib import Path

import pytest

# Make the package importable when running pytest from the econ-review-agent dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from econ_review.schema import PaperReview  # noqa: E402


@pytest.fixture
def sample_review_dict() -> dict:
    """A minimal valid PaperReview payload used across tests."""
    return {
        "research_question": "Does a higher minimum wage reduce teen employment?",
        "causal_claim": "Elasticity of teen employment with respect to the minimum wage (ATT).",
        "data": {
            "design_type": "panel",
            "unit_of_observation": "county-quarter",
            "time_dimension": "1994Q1-2019Q4, quarterly",
            "data_sources": ["QWI"],
            "sample_description": "1,181 contiguous border county pairs.",
        },
        "identification": {
            "method": "difference-in-differences",
            "source_of_variation": "Cross-border differences in state minimum wages.",
            "description": "County pairs straddling state borders, pair-by-quarter FE.",
            "estimating_equation": "ln(E_ipt) = a + b ln(MW_it) + g_i + d_pt + e_ipt",
        },
        "key_assumptions": [
            {
                "assumption": "Parallel trends within border pairs.",
                "stated_explicitly_by_authors": False,
                "testability": "partially testable (diagnostics exist)",
                "suggested_diagnostic": "Event-study pre-trends around large increases.",
            }
        ],
        "endogeneity_concerns": [
            {
                "concern": "Cross-border commuting contaminates the control county.",
                "channel": "spillovers / SUTVA violation",
                "severity": "major",
                "suggested_fix": "Drop pairs with high commuting flows (LODES data).",
            }
        ],
        "referee_questions": [
            {
                "question": "How do staggered-adoption biases affect the TWFE estimate?",
                "why_it_matters": "Negative weights can flip the sign of beta.",
            }
        ],
        "identification_credibility": 4,
        "overall_assessment": "Credible border-pair design; spillovers are the main threat.",
        "limitations_of_this_review": "Results section not provided.",
    }


@pytest.fixture
def sample_review(sample_review_dict) -> PaperReview:
    return PaperReview.model_validate(sample_review_dict)
