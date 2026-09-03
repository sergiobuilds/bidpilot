"""The tender detail can run the decision and draft a proposal live, gated by evidence."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from bidpilot import agent_core

APP_PATH = Path(__file__).parents[1] / "app.py"
NOTICE = "R26BK01680611-000"


def _fake_draft(notice_number, supplier_evidence=None, **kwargs):
    return {
        "notice_number": notice_number,
        "decision": "PURSUE",
        "proposal_gate": "HISTORICAL EXERCISE"
        if kwargs.get("historical_exercise")
        else "OPEN",
        "supplier": {
            "id": "supplier-northstar",
            "name": "Northstar Systems",
            "synthetic": True,
        },
        "selected_position": {"title": "Proven Data Quality Operations"},
        "sections": [
            {
                "criterion": "Technical",
                "heading": "Technical approach",
                "markdown": "## Technical\n\nBody T.",
            },
            {
                "criterion": "Price",
                "heading": "Price",
                "markdown": "## Price\n\nBody P.",
            },
        ],
        "markdown": "## Technical\n\nBody T.\n\n## Price\n\nBody P.",
        "red_team": [],
        "tasks": [{"title": "Confirm delivery hours", "owner": "Operator"}],
        "provider": "LOCAL_PYTHON_POLICY",
        "persisted": False,
        "disclosure": "Synthetic demo supplier profile; nothing here is a real company claim.",
    }


def _detail_app(monkeypatch) -> AppTest:
    monkeypatch.setattr(agent_core, "draft_proposal", _fake_draft, raising=False)
    app = AppTest.from_file(APP_PATH)
    app.query_params["tender"] = NOTICE
    return app


def _text(app: AppTest) -> str:
    return " ".join(item.value for item in app.markdown)


def test_detail_without_evidence_stays_review_and_offers_no_download(
    monkeypatch,
) -> None:
    app = _detail_app(monkeypatch)
    app.run(timeout=60)

    assert not app.exception
    assert len(app.checkbox) == 4
    app.button(key="bp-draft-run").click()
    app.run(timeout=60)

    text = _text(app)
    assert "REVIEW" in text
    assert "4 of 4 eligibility requirements still need supplier evidence" in text
    assert "Body T." not in text
    assert len(app.download_button) == 0


def test_detail_with_full_evidence_drafts_a_proposal_and_enables_download(
    monkeypatch,
) -> None:
    app = _detail_app(monkeypatch)
    app.run(timeout=60)
    for box in app.checkbox:
        box.check()
    app.button(key="bp-draft-run").click()
    app.run(timeout=60)

    assert not app.exception
    text = _text(app)
    assert "PURSUE" in text
    assert "Proven Data Quality Operations" in text
    assert "Body T." in text and "Body P." in text
    assert any("Synthetic demo supplier profile" in w.value for w in app.warning)
    assert "Confirm delivery hours" in text
    assert len(app.download_button) == 1
    assert not app.download_button[0].disabled


def test_detail_after_the_deadline_drafts_only_as_a_historical_exercise(
    monkeypatch,
) -> None:
    from datetime import datetime

    from bidpilot import refinement_app

    seen: dict[str, object] = {}

    def fake_draft(notice_number, supplier_evidence=None, **kwargs):
        seen.update(kwargs)
        draft = _fake_draft(notice_number, supplier_evidence, **kwargs)
        return draft

    monkeypatch.setattr(agent_core, "draft_proposal", fake_draft, raising=False)
    monkeypatch.setattr(
        refinement_app,
        "current_clock",
        lambda: datetime.fromisoformat("2026-09-03T16:30:00+09:00"),
    )
    app = AppTest.from_file(APP_PATH)
    app.query_params["tender"] = NOTICE
    app.run(timeout=60)
    for box in app.checkbox:
        box.check()
    app.button(key="bp-draft-run").click()
    app.run(timeout=60)

    assert not app.exception
    text = _text(app)
    assert "historical exercise" in text.lower()
    assert seen.get("historical_exercise") is True
    assert "HISTORICAL EXERCISE" in text
