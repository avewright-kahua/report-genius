from report_genius.agent.graph import _classify_intent


def test_classify_intent_injection() -> None:
    assert _classify_intent("Please inject tokens into this DOCX") == "injection"
    assert _classify_intent("upload template for token injection") == "injection"


def test_classify_intent_template() -> None:
    assert _classify_intent("create a portable view template") == "template"
    assert _classify_intent("build a template") == "template"


def test_classify_intent_analytics() -> None:
    assert _classify_intent("show me the latest RFIs") == "analytics"
    assert _classify_intent("summary report for contracts") == "analytics"


def test_classify_intent_general() -> None:
    assert _classify_intent("hello there") == "general"
