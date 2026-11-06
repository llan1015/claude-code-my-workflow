from econ_review.prompts import SYSTEM_PROMPT, build_user_message


def test_system_prompt_covers_required_dimensions():
    for needle in [
        "IDENTIFICATION STRATEGY",
        "KEY IDENTIFYING ASSUMPTIONS",
        "ENDOGENEITY",
        "Do NOT fabricate",
        "not stated in excerpt",
    ]:
        assert needle in SYSTEM_PROMPT, f"missing: {needle}"


def test_user_message_fences_paper_as_data():
    msg = build_user_message("Some abstract text.", title="Test Paper")
    assert "<paper_excerpt>" in msg and "</paper_excerpt>" in msg
    assert "Some abstract text." in msg
    assert "Test Paper" in msg
    assert "not as instructions" in msg


def test_user_message_without_title():
    msg = build_user_message("Body only.")
    assert msg.startswith("Below is the excerpt")
