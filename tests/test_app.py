"""The pursuit workspace's product contract.

Every test drives the real app. The Snowflake connector is faked at the same
seam the store tests use, so four-stage navigation, the production states and
the proposal review gate are exercised without live credentials — and without
the app ever reading a local fixture in place of a failed query.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import streamlit as st
from streamlit.runtime.memory_media_file_storage import _calculate_file_id
from streamlit.testing.v1 import AppTest

from bidpilot import ui

APP_PATH = Path(__file__).parents[1] / "app.py"

RUN_ID = "run-app-1"
OLDER_RUN_ID = "run-app-0"
OTHER_RUN_ID = "run-app-other"

# Internal store names belong to provenance, not to the working screens.
STORE_NAMES = (
    "AGENT_RUNS",
    "PURSUIT_DECISIONS",
    "RUBRIC_RESPONSE_PLANS",
    "WIN_STRATEGIES",
    "PROPOSAL_SECTIONS",
    "PURSUIT_TASKS",
)

TRACE = json.dumps(
    {
        "completed_at": "2026-08-02T00:01:00Z",
        "execution_provenance": {
            "cortex_session_id": "session-1",
            "cortex_write_query_ids": ["q-1", "q-2"],
        },
    }
)

# Stored exactly as Snowflake returns it, offset and all.
CREATED_AT_RAW = "2026-08-01 17:09:33.705000-07:00"

LIST_COLUMNS = (
    "RUN_ID",
    "OPPORTUNITY_ID",
    "OPPORTUNITY_VERSION",
    "SUPPLIER_PROFILE_ID",
    "POLICY_VERSION",
    "PROVIDER",
    "STATE",
    "CREATED_AT",
    "AGENT_COUNT",
    "DECISION_COUNT",
    "STRATEGY_COUNT",
    "SELECTED_STRATEGY_COUNT",
    "PLAN_COUNT",
    "SECTION_COUNT",
    "TASK_COUNT",
    "IS_COMPLETE",
)

LIST_ROW = (
    RUN_ID,
    "opp-1",
    "v1",
    "supplier-1",
    "2026-08-02.v1",
    "CORTEX_CODE_CLI",
    "COMPLETED",
    CREATED_AT_RAW,
    1,
    1,
    3,
    1,
    2,
    2,
    3,
    True,
)
OLDER_LIST_ROW = (
    OLDER_RUN_ID,
    "opp-1",
    "v1",
    "supplier-1",
    "2026-08-02.v1",
    "CORTEX_CODE_CLI",
    "COMPLETED",
    "2026-07-28 09:00:00.000000-07:00",
    1,
    1,
    3,
    1,
    2,
    2,
    3,
    True,
)
INCOMPLETE_LIST_ROW = (
    "run-unfinished",
    "opp-2",
    "v1",
    "supplier-1",
    "2026-08-02.v1",
    "SNOWPARK",
    "COMPLETED",
    "2026-07-20 09:00:00.000000-07:00",
    1,
    1,
    0,
    0,
    0,
    0,
    0,
    False,
)


def product_responses(list_rows: list[tuple] | None = None) -> list[tuple]:
    """Fake result sets for one complete run, in store query order."""
    return [
        (
            "SELECT a.run_id",
            LIST_COLUMNS,
            [LIST_ROW, OLDER_LIST_ROW] if list_rows is None else list_rows,
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS WHERE run_id",
            (
                "RUN_ID",
                "OPPORTUNITY_ID",
                "OPPORTUNITY_VERSION",
                "SUPPLIER_PROFILE_ID",
                "POLICY_VERSION",
                "PROVIDER",
                "STATE",
                "CREATED_AT",
                "TRACE",
                "SUPPLIER_PROFILE_VERSION",
            ),
            [
                (
                    RUN_ID,
                    "opp-1",
                    "v1",
                    "supplier-1",
                    "2026-08-02.v1",
                    "CORTEX_CODE_CLI",
                    "COMPLETED",
                    CREATED_AT_RAW,
                    TRACE,
                    "fixture-v1",
                )
            ],
        ),
        (
            "SELECT o.*",
            ("OPPORTUNITY_ID", "TITLE", "BUYER_OBJECTIVE", "SCOPE", "SOURCE_STATUS"),
            [
                (
                    "opp-1",
                    "Public data quality service",
                    "Improve public-data reliability.",
                    "Data quality remediation",
                    "historical-demo-replay",
                )
            ],
        ),
        (
            "SELECT p.*",
            ("SUPPLIER_PROFILE_ID", "SUPPLIER_NAME"),
            [("supplier-1", "Northstar Systems")],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS",
            ("RUN_ID", "STATUS", "MISSING_ELIGIBILITY", "CAPACITY_GAP_HOURS"),
            [(RUN_ID, "PURSUE", "[]", 0)],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES",
            (
                "RUN_ID",
                "STRATEGY_ID",
                "TITLE",
                "STATEMENT",
                "SELECTED",
                "PROOF_CARDS",
                "WEAKNESS",
                "MITIGATION",
            ),
            [
                (
                    RUN_ID,
                    "s-1",
                    "Proven data quality operations",
                    "Win on recorded defect reduction.",
                    True,
                    '[{"project": "City Open Data", "relevance": "Reduced recurring defects"}]',
                    "No prior engagement with this buyer.",
                    "Transferable evidence from City Open Data.",
                ),
                (
                    RUN_ID,
                    "s-2",
                    "Zero-interruption continuity",
                    "Win on uninterrupted service.",
                    False,
                    "[]",
                    None,
                    None,
                ),
                (
                    RUN_ID,
                    "s-3",
                    "Capacity surplus",
                    "Win on available hours.",
                    False,
                    "[]",
                    None,
                    None,
                ),
            ],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.RUBRIC_RESPONSE_PLANS",
            ("RUN_ID", "CRITERION_NAME", "WEIGHT", "ASSETS", "CLAIM", "OWNER"),
            [
                (
                    RUN_ID,
                    "Technical approach",
                    60,
                    '["City Open Data"]',
                    "Deliver a measured data-quality improvement.",
                    "Solution lead",
                ),
                (
                    RUN_ID,
                    "Price",
                    40,
                    '["availability:900h"]',
                    "Price against the delivery envelope.",
                    "Commercial lead",
                ),
            ],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS",
            ("RUN_ID", "TASK_ID", "TASK_NAME", "OWNER", "STATUS"),
            [
                (
                    RUN_ID,
                    "rt-scope-creep-check",
                    "Confirm the offer stays inside the tendered scope",
                    "Bid manager",
                    "COMPLETE",
                ),
                (
                    RUN_ID,
                    "t-1",
                    "Own the Price response",
                    "Commercial lead",
                    "COMPLETE",
                ),
                (
                    RUN_ID,
                    "t-2",
                    "Assemble the submission package",
                    "Bid manager",
                    "IN_PROGRESS",
                ),
            ],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_SECTIONS",
            ("RUN_ID", "SECTION_ID", "CRITERION_NAME", "SECTION_MARKDOWN"),
            [
                (
                    RUN_ID,
                    "sec-1",
                    "Technical approach",
                    (
                        "## Technical approach\n\nValidation: measured API regression.\n"
                        "Buyer outcome: sustained public-service reliability."
                    ),
                ),
                (
                    RUN_ID,
                    "sec-2",
                    "Price",
                    "## Price\n\nPriced against the delivery envelope.",
                ),
            ],
        ),
        (
            "AS is_complete",
            (
                "AGENT_COUNT",
                "DECISION_COUNT",
                "STRATEGY_COUNT",
                "SELECTED_STRATEGY_COUNT",
                "PLAN_COUNT",
                "SECTION_COUNT",
                "TASK_COUNT",
                "IS_COMPLETE",
            ),
            [(1, 1, 3, 1, 2, 2, 3, True)],
        ),
    ]


class FakeCursor:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.description: list[tuple] = []
        self.rows: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        if "CURRENT_ROLE()" in sql:
            self.description = [("CURRENT_ROLE",)]
            self.rows = [("BIDPILOT_READER",)]
            return
        for marker, description, rows in self.connection.responses:
            if marker in sql:
                self.description = [(name,) for name in description]
                self.rows = list(rows)
                return
        raise AssertionError(f"Unexpected SQL in fake Snowflake connection: {sql}")

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, responses: list[tuple]) -> None:
        self.responses = responses

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        pass


def product_app(monkeypatch) -> AppTest:
    monkeypatch.setenv("BIDPILOT_SNOWFLAKE_CONNECTION", "contest")
    st.cache_data.clear()
    app = AppTest.from_file(APP_PATH)
    app.query_params["walkthrough"] = "1"
    return app


def markdown_of(app: AppTest) -> str:
    return " ".join(item.value for item in app.markdown)


def opened_at(app: AppTest, stage: int, run_id: str = RUN_ID) -> AppTest:
    app.session_state[ui.STAGE_KEY] = stage
    app.session_state[ui.RUN_KEY] = run_id
    app.run(timeout=60)
    return app


# ---------------------------------------------------------------------------
# Production states
# ---------------------------------------------------------------------------


def test_missing_connection_is_a_configuration_error_with_a_recovery_instruction(
    monkeypatch,
) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    st.cache_data.clear()
    app = AppTest.from_file(APP_PATH)
    app.query_params["walkthrough"] = "1"
    app.run(timeout=60)

    assert not app.exception
    markdown = markdown_of(app)
    assert "BIDPILOT_SNOWFLAKE_CONNECTION" in markdown
    assert "does not fall back to local fixtures" in markdown
    assert "bidpilot-reader" in markdown
    # No tender is invented while the workspace is unconfigured.
    assert "Public data quality service" not in markdown


def test_connection_failure_stays_visible_and_offers_a_working_retry(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.side_effect = RuntimeError("network unreachable")
        app = product_app(monkeypatch)
        app.run(timeout=60)

        assert not app.exception
        assert "network unreachable" not in markdown_of(app)
        assert "temporarily unavailable" in markdown_of(app)
        assert "Snowflake could not be reached" in markdown_of(app)

        # The retry must re-query rather than replay the cached failure.
        connect.side_effect = None
        connect.return_value = FakeConnection(product_responses())
        app.button(key="bp-retry").click()
        app.run(timeout=60)

    assert not app.exception
    assert "Snowflake could not be reached" not in markdown_of(app)
    assert "Public data quality service" in markdown_of(app)


def test_no_complete_run_is_an_empty_state_that_invents_no_tender(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(
            product_responses(list_rows=[INCOMPLETE_LIST_ROW])
        )
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    markdown = markdown_of(app)
    assert "No tender has a completed analysis" in markdown
    assert "No tender is invented in the meantime." in markdown
    # The unfinished run is reported as unfinished, never opened as a tender.
    assert "Analyses that did not finish" in markdown
    assert not [
        button for button in app.button if button.label.startswith("Open bid decision")
    ]


def test_a_selected_run_that_vanishes_fails_closed_with_an_explanation(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.session_state[ui.STAGE_KEY] = 2
        app.session_state[ui.RUN_KEY] = OTHER_RUN_ID
        app.run(timeout=60)

    assert not app.exception
    assert app.session_state[ui.STAGE_KEY] == 0
    markdown = markdown_of(app)
    assert "That analysis is no longer available." in markdown
    assert "public opportunities dashboard" in markdown


def test_no_reference_only_control_reaches_production(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)
        first = markdown_of(app) + " ".join(button.label for button in app.button)
        opened_at(app, 3)
        fourth = markdown_of(app) + " ".join(button.label for button in app.button)

    assert not app.exception
    for forbidden in (
        "workspace state",
        "Detach recorded asset",
        "Reference control",
        "Loading state",
    ):
        assert forbidden not in first
        assert forbidden not in fourth


def test_verified_replay_is_one_result_page_without_stage_navigation(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    markdown = markdown_of(app)
    expected_order = (
        "Decision rationale",
        "Score-weighted Win Position",
        "Proposal &amp; red-team result",
        "Owned work",
        "Snowflake proof",
    )
    assert [markdown.index(label) for label in expected_order] == sorted(
        markdown.index(label) for label in expected_order
    )
    for forbidden in (
        "Analysis history",
        "Opportunities",
        "Stage 1 of 4",
        "1 · Public tender",
    ):
        assert forbidden not in markdown
    assert len(app.text_area) == 1
    assert len(app.expander) == 1
    assert app.expander[0].label == "Snowflake proof"


# ---------------------------------------------------------------------------
# Stage 1 — Opportunities
# ---------------------------------------------------------------------------


def test_verified_replay_selects_only_the_latest_complete_analysis(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    markdown = markdown_of(app)
    assert "Public data quality service" in markdown
    assert RUN_ID in markdown
    assert "2 August 2026" in markdown
    assert OLDER_RUN_ID not in markdown
    assert app.session_state[ui.RUN_KEY] == RUN_ID


def test_complete_replay_opens_directly_as_one_result_page(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    assert app.session_state[ui.RUN_KEY] == RUN_ID
    assert "Decision rationale" in markdown_of(app)


# ---------------------------------------------------------------------------
# Stage 2 — Bid decision
# ---------------------------------------------------------------------------


def test_bid_decision_is_settled_while_only_the_proposal_is_editable(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        opened_at(app, 1)

    assert not app.exception
    markdown = markdown_of(app)
    assert "PURSUE" in markdown
    assert "Public data quality service" in markdown
    assert "Improve public-data reliability." in markdown
    assert "Northstar Systems" in markdown
    # Recorded versions and provenance sit beside the answer, not inside it.
    for identifier in (
        "Tender version",
        "Supplier profile version",
        "Policy version",
        "Analysis run",
    ):
        assert identifier in markdown
    assert "historical demo replay" in markdown
    # The run's own recorded completion is what the word "Completed" names.
    assert "2 August 2026" in markdown
    # Plain language, over the two recorded policy facts.
    assert "every recorded eligibility requirement was met" in markdown
    # Settled fields are records; the proposal is the only editable surface.
    assert len(app.text_area) == 1
    assert app.text_area[0].label == "Proposal draft"
    assert not app.radio
    assert not app.selectbox
    assert not app.text_input


def test_bid_room_first_viewport_uses_only_the_selected_persisted_run(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    markdown = markdown_of(app)
    assert 'data-workspace-view="bid-room"' in markdown
    for recorded_value in (
        "PURSUE",
        "60 points",
        "1 cited · 0 open gaps",
        "Proven data quality operations",
        "Assemble the submission package",
        "Bid manager",
        RUN_ID,
    ):
        assert recorded_value in markdown


def test_bid_room_first_viewport_is_absent_without_persisted_run_data(
    monkeypatch,
) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    st.cache_data.clear()
    app = AppTest.from_file(APP_PATH)
    app.query_params["walkthrough"] = "1"
    app.run(timeout=60)

    assert not app.exception
    assert 'data-workspace-view="bid-room"' not in markdown_of(app)
    assert "Proven data quality operations" not in markdown_of(app)


def test_policy_dimensions_state_every_result_in_words(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        opened_at(app, 1)

    markdown = markdown_of(app)
    for name in ("Eligibility", "Delivery capacity", "Comparable delivery"):
        assert name in markdown
    assert "3 of 3 passed" in markdown
    assert "0 hours" in markdown
    assert "Passed" in markdown


# ---------------------------------------------------------------------------
# Stage 3 — Win plan
# ---------------------------------------------------------------------------


def test_win_plan_shows_the_official_weights_and_every_criterion_fact(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        opened_at(app, 2)

    assert not app.exception
    markdown = markdown_of(app)
    assert "Official score map" in markdown
    assert "Weights are fixed by the tender and total 100." in markdown
    for fact in (
        "Technical approach",
        "Price",
        "City Open Data",
        "Solution lead",
        "Commercial lead",
    ):
        assert fact in markdown
    # The gap state is named, never signalled by colour alone.
    assert "Covered" in markdown


def test_persisted_strategies_are_comparative_records_not_editable_inputs(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        opened_at(app, 2)

    assert not app.exception
    markdown = markdown_of(app)
    # All three recorded positions are shown, with exactly one selected.
    for title in (
        "Proven data quality operations",
        "Zero-interruption continuity",
        "Capacity surplus",
    ):
        assert title in markdown
    assert markdown.count(">Selected<") == 1
    assert markdown.count("Comparative record") == 2
    assert "The submitted analysis is immutable" in markdown
    # The immutable record offers no way to re-select a position.
    assert not app.radio
    assert not app.selectbox
    # Only the selected position flows onward.
    assert "Proven data quality operations" in markdown


# ---------------------------------------------------------------------------
# Stage 4 — Proposal room
# ---------------------------------------------------------------------------


def test_proposal_room_composes_the_persisted_fragments_under_their_criteria(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        opened_at(app, 3)

    assert not app.exception
    draft = app.text_area(key=f"bp-draft::{RUN_ID}").value
    assert "## Technical approach" in draft
    assert "## Price" in draft
    assert "Validation: measured API regression." in draft
    markdown = markdown_of(app)
    # Every persisted task is listed with the role that owns it.
    for task in (
        "Confirm the offer stays inside the tendered scope",
        "Own the Price response",
        "Assemble the submission package",
    ):
        assert task in markdown
    assert "3 recorded tasks" in markdown
    assert "Review passed" in markdown
    assert not app.download_button[0].disabled


def test_editing_the_draft_reruns_the_review_and_closes_and_reopens_the_download(
    monkeypatch,
) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        opened_at(app, 3)
        assert not app.download_button[0].disabled

        # Dropping a score-bearing section's recorded asset must fail review.
        broken = (
            "## Technical approach\n\nNothing recorded here.\n\n## Price\n\nPriced.\n"
        )
        app.text_area(key=f"bp-draft::{RUN_ID}").set_value(broken)
        app.run(timeout=60)
        assert "Review failed" in markdown_of(app)
        assert app.download_button[0].disabled

        # Repairing it reopens the download with the exact edited text.
        repaired = (
            "## Technical approach\n\nCity Open Data.\n"
            "Validation: measured API regression.\nBuyer outcome: sustained reliability.\n\n"
            "## Price\n\nPriced against availability:900h.\n"
        )
        app.text_area(key=f"bp-draft::{RUN_ID}").set_value(repaired)
        app.run(timeout=60)

    assert not app.exception
    assert "Review passed" in markdown_of(app)
    download = app.download_button[0]
    assert not download.disabled
    # The download carries the edited text, not the composed original: the
    # media URL is the content's own identity.
    identity = _calculate_file_id(repaired.encode(), "text/markdown", f"{RUN_ID}.md")
    assert download.proto.url.endswith(f"/{identity}.md")
    # The composed original no longer identifies the download.
    stale = _calculate_file_id(broken.encode(), "text/markdown", f"{RUN_ID}.md")
    assert stale not in download.proto.url
    assert app.session_state[f"bp-draft::{RUN_ID}"] == repaired


def test_execution_provenance_stays_in_one_collapsed_section(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        opened_at(app, 3)

    assert not app.exception
    expanders = [item for item in app.expander]
    assert len(expanders) == 1
    assert expanders[0].label == "Snowflake proof"
    assert expanders[0].proto.expanded is False
    # The evidence itself is inside it, not spread across the screen.
    assert "session-1" in markdown_of(app)
    assert "q-1" in markdown_of(app)


def test_working_screens_keep_internal_store_names_out_of_sight(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        for stage in (0, 1, 2):
            opened_at(app, stage)
            markdown = markdown_of(app)
            for name in STORE_NAMES:
                assert name not in markdown, f"{name} reached stage {stage + 1}"


# ---------------------------------------------------------------------------
# Shell and accessibility contract
# ---------------------------------------------------------------------------


def test_one_page_announces_every_progressive_result_section(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    markdown = markdown_of(app)
    for name in (
        "Decision rationale",
        "Score-weighted Win Position",
        "Proposal &amp; red-team result",
        "Owned work",
        "Snowflake proof",
    ):
        assert name in markdown


def test_result_page_has_no_competing_stage_stepper(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    assert not [button for button in app.button if button.key.startswith("bp-step-")]


# ---------------------------------------------------------------------------
# Projection — no widget needed
# ---------------------------------------------------------------------------


def test_display_date_reads_stored_timestamps_without_shifting_them() -> None:
    assert ui.display_date(CREATED_AT_RAW) == "1 August 2026"
    assert (
        ui.display_date(
            dt.datetime(2026, 8, 1, 17, 9, tzinfo=dt.timezone(dt.timedelta(hours=-7)))
        )
        == "1 August 2026"
    )
    assert ui.display_date(dt.date(2026, 8, 1)) == "1 August 2026"
    # Anything unparseable is shown exactly as stored rather than hidden.
    assert ui.display_date("first quarter 2026") == "first quarter 2026"
    assert ui.display_date(None) == ""


def test_group_by_opportunity_keeps_the_newest_analysis_current() -> None:
    groups = ui.group_by_opportunity(
        [
            {"run_id": "b", "opportunity_id": "opp-1"},
            {"run_id": "a", "opportunity_id": "opp-1"},
            {"run_id": "c", "opportunity_id": "opp-2"},
        ]
    )
    assert [group["opportunity_id"] for group in groups] == ["opp-1", "opp-2"]
    assert groups[0]["current"]["run_id"] == "b"
    assert [run["run_id"] for run in groups[0]["history"]] == ["a"]
    assert groups[1]["history"] == []


@pytest.mark.parametrize(
    ("missing", "gap", "status", "expected"),
    [
        ([], 0.0, "PURSUE", "every recorded eligibility requirement was met"),
        (["ISO 27001"], 0.0, "NO-GO", "1 eligibility requirement is still unmet"),
        ([], 120.0, "NO-GO", "delivery capacity is 120 hours short"),
    ],
)
def test_decision_summary_states_the_recorded_facts(
    missing, gap, status, expected
) -> None:
    view = {
        "decision": {"status": status},
        "missing_eligibility": missing,
        "capacity_gap_hours": gap,
        "status": status,
    }
    assert expected in ui.decision_summary(view)


def test_policy_dimensions_only_claim_comparable_delivery_on_a_pursue_verdict() -> None:
    pursue = ui.policy_dimensions(
        {"missing_eligibility": [], "capacity_gap_hours": 0.0, "status": "PURSUE"}
    )
    assert [item["name"] for item in pursue] == [
        "Eligibility",
        "Delivery capacity",
        "Comparable delivery",
    ]
    assert all(item["state"] == "pass" for item in pursue)

    blocked = ui.policy_dimensions(
        {
            "missing_eligibility": ["ISO 27001"],
            "capacity_gap_hours": 40.0,
            "status": "NO-GO",
        }
    )
    assert [item["name"] for item in blocked] == ["Eligibility", "Delivery capacity"]
    assert all(item["state"] == "open" for item in blocked)
    assert "ISO 27001" in blocked[0]["detail"]


def test_completion_date_comes_from_the_run_not_from_the_row_that_stored_it() -> None:
    stored = {
        "run": {
            "run_id": RUN_ID,
            "created_at": CREATED_AT_RAW,
            "trace": {"completed_at": "2026-08-02T00:01:00Z"},
        },
        "opportunity": {},
        "supplier": {},
        "decision": {},
        "strategies": [],
        "blueprint": [],
        "sections": [],
        "tasks": [],
    }
    view = ui.build_run_view(stored, RUN_ID)
    assert view["completed_on"] == "2 August 2026"
    assert view["recorded_on"] == "1 August 2026"

    # A run with no recorded completion claims none.
    stored["run"]["trace"] = {}
    bare = ui.build_run_view(stored, RUN_ID)
    assert bare["completed_on"] == ""
    assert bare["recorded_on"] == "1 August 2026"


def test_build_run_view_reports_coverage_without_supplying_a_missing_asset() -> None:
    view = ui.build_run_view(
        {
            "run": {"run_id": RUN_ID, "opportunity_id": "opp-1", "trace": {}},
            "opportunity": {"title": "Public data quality service"},
            "supplier": {"supplier_name": "Northstar Systems"},
            "decision": {
                "status": "PURSUE",
                "missing_eligibility": "[]",
                "capacity_gap_hours": 0,
            },
            "strategies": [
                {"strategy_id": "s-1", "title": "Selected", "selected": True}
            ],
            "blueprint": [
                {
                    "criterion_name": "Technical approach",
                    "weight": "60.00",
                    "assets": '["City Open Data"]',
                },
                {"criterion_name": "Price", "weight": "40.00", "assets": "[]"},
            ],
            "sections": [],
            "tasks": [],
        },
        RUN_ID,
    )
    assert view["total_weight"] == 100
    assert view["covered_weight"] == 60
    assert view["open_weight"] == 40
    assert [item["gap"] for item in view["criteria"]] == ["covered", "uncovered"]
    assert view["criteria"][1]["assets"] == []
    assert view["headline"] == "Public data quality service"


def test_record_helpers_never_expose_a_serialised_row() -> None:
    assert (
        ui.record_label({"project": "City Open Data", "relevance": "Reduced defects"})
        == "City Open Data"
    )
    assert (
        ui.record_detail({"project": "City Open Data", "relevance": "Reduced defects"})
        == "Reduced defects"
    )
    assert ui.as_records('["a", "b"]') == ["a", "b"]
    assert ui.as_records(None) == []
    assert ui.humanise("historical-demo-replay") == "historical demo replay"


def test_loading_states_say_what_snowflake_step_is_being_waited_on() -> None:
    from bidpilot.ui import loading_markup

    listing = loading_markup("listing")
    detail = loading_markup("detail")

    for markup in (listing, detail):
        assert 'role="status"' in markup
        assert "Snowflake" in markup
        assert "BIDPILOT_READER" in markup
    assert "Connecting to Snowflake" in listing
    assert "cortex" not in listing.lower()
    assert "Reading the selected run" in detail
