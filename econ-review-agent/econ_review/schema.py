"""Pydantic schema for the structured paper review.

The schema is the contract between the model and downstream code: the API call
uses structured outputs (`client.messages.parse`) so the response is guaranteed
to validate against `PaperReview` or the call fails loudly.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DataStructure(BaseModel):
    design_type: Literal[
        "cross-section",
        "repeated cross-section",
        "panel",
        "time series",
        "event-study panel",
        "not stated in excerpt",
        "other",
    ]
    unit_of_observation: str = Field(
        description="e.g., 'county-quarter', 'individual worker', 'MSA'. "
        "Use 'not stated in excerpt' if the text does not say."
    )
    time_dimension: str = Field(
        description="Sample period and frequency, e.g., '1990-2006, quarterly'."
    )
    data_sources: List[str] = Field(
        description="Named datasets (e.g., QCEW, CPS, ACS). Empty list if none named."
    )
    sample_description: str


class IdentificationStrategy(BaseModel):
    method: Literal[
        "difference-in-differences",
        "event study",
        "instrumental variables",
        "regression discontinuity",
        "synthetic control",
        "shift-share (Bartik)",
        "matching",
        "randomized experiment",
        "structural model",
        "selection on observables (OLS with controls)",
        "bunching",
        "not stated in excerpt",
        "other",
    ]
    source_of_variation: str = Field(
        description="What variation in treatment the design exploits, in one or two sentences."
    )
    description: str = Field(
        description="How the strategy is implemented in this paper, per the excerpt."
    )
    estimating_equation: Optional[str] = Field(
        default=None,
        description="The main specification if the excerpt states one, in plain text or LaTeX; null otherwise.",
    )


class KeyAssumption(BaseModel):
    assumption: str
    stated_explicitly_by_authors: bool = Field(
        description="True only if the excerpt itself states the assumption."
    )
    testability: Literal[
        "directly testable",
        "partially testable (diagnostics exist)",
        "untestable",
    ]
    suggested_diagnostic: Optional[str] = Field(
        default=None,
        description="A concrete test or robustness check (e.g., pre-trend event study, placebo outcome).",
    )


class EndogeneityConcern(BaseModel):
    concern: str
    channel: Literal[
        "omitted variables",
        "reverse causality",
        "measurement error",
        "selection",
        "simultaneity",
        "anticipation effects",
        "spillovers / SUTVA violation",
        "attrition",
        "other",
    ]
    severity: Literal["fatal if unaddressed", "major", "minor"]
    suggested_fix: str = Field(
        description="A concrete design change, robustness check, or additional data that would address it."
    )


class RefereeQuestion(BaseModel):
    question: str
    why_it_matters: str


class PaperReview(BaseModel):
    """Structured review of an empirical economics paper excerpt."""

    research_question: str
    causal_claim: str = Field(
        description="The causal parameter the paper claims to identify, stated precisely."
    )
    data: DataStructure
    identification: IdentificationStrategy
    key_assumptions: List[KeyAssumption] = Field(
        description="The assumptions required for the identification strategy to be valid."
    )
    endogeneity_concerns: List[EndogeneityConcern]
    referee_questions: List[RefereeQuestion] = Field(
        description="3-5 questions a top-5 journal referee would raise."
    )
    identification_credibility: int = Field(
        ge=1, le=5, description="1 = not credible, 5 = airtight, judged from the excerpt alone."
    )
    overall_assessment: str = Field(
        description="2-3 sentence synthesis: contribution, main strength, main threat."
    )
    limitations_of_this_review: str = Field(
        description="What could not be determined because only the abstract and design section were provided."
    )
