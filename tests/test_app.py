from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parents[1] / "app.py"


def app_module(monkeypatch, tmp_path: Path):
    """Load app.py as a module so its presentation helpers can be unit-tested.

    The script renders on import, so it runs in a temporary directory and
    without a configured connection: the local simulation path touches no
    Snowflake session and leaves nothing in the repository.
    """
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location("bidpilot_app_under_test", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except BaseException as error:
        # st.stop() ends a Streamlit script by raising. Every helper is
        # already defined by then; anything else is a real failure.
        if type(error).__name__ not in ("StopException", "RerunException"):
            raise
    return module


def test_bid_room_reopens_latest_matching_persisted_run(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    monkeypatch.chdir(tmp_path)

    first = AppTest.from_file(APP_PATH)
    first.run(timeout=30)
    first.button[0].click()
    first.run(timeout=30)
    assert any("Bid Room run saved:" in item.value for item in first.success)

    reopened = AppTest.from_file(APP_PATH)
    reopened.run(timeout=30)
    assert any("Bid Room run saved:" in item.value for item in reopened.success)


# ---------------------------------------------------------------------------
# Public product mode. The Snowflake connector is faked at the same seam the
# store tests use, so the four-screen navigation is exercised without live
# credentials and without the app ever touching a fixture path.
# ---------------------------------------------------------------------------

RUN_ID = "run-app-1"
OLDER_RUN_ID = "run-app-0"

# Every internal store name that must not reach the working screens. They are
# allowed only inside the Proposal Room's collapsed Run proof disclosure.
STORE_NAMES = (
    "AGENT_RUNS",
    "PURSUIT_DECISIONS",
    "OPPORTUNITIES",
    "SUPPLIER_PROFILES",
    "RUBRIC_RESPONSE_PLANS",
    "WIN_STRATEGIES",
    "PROPOSAL_SECTIONS",
    "PURSUIT_TASKS",
)

TRACE = json.dumps(
    {
        "execution_provenance": {
            "cortex_session_id": "session-1",
            "cortex_write_query_ids": ["q-1", "q-2"],
        }
    }
)

# Two completed analyses of the same opportunity, newest first, exactly as the
# store returns them. The newest is the opportunity's active analysis.
# CREATED_AT is stored exactly as Snowflake returns it, offset and all. The
# card must show it as a date a person can read.
CREATED_AT_RAW = "2026-08-01 17:09:33.705000-07:00"

LIST_ROW = (
    RUN_ID, "opp-1", "v1", "supplier-1", "2026-08-02.v1", "CORTEX_CODE_CLI",
    "COMPLETED", CREATED_AT_RAW, 1, 1, 2, 1, 2, 2, 2, True,
)

OLDER_LIST_ROW = (
    OLDER_RUN_ID, "opp-1", "v1", "supplier-1", "2026-08-02.v1", "CORTEX_CODE_CLI",
    "COMPLETED", "2026-08-01", 1, 1, 2, 1, 2, 2, 2, True,
)

LIST_COLUMNS = (
    "RUN_ID", "OPPORTUNITY_ID", "OPPORTUNITY_VERSION", "SUPPLIER_PROFILE_ID",
    "POLICY_VERSION", "PROVIDER", "STATE", "CREATED_AT", "AGENT_COUNT",
    "DECISION_COUNT", "STRATEGY_COUNT", "SELECTED_STRATEGY_COUNT", "PLAN_COUNT",
    "SECTION_COUNT", "TASK_COUNT", "IS_COMPLETE",
)


def product_responses() -> list[tuple]:
    """Fake result sets for the complete runs, in store query order."""
    return [
        ("SELECT a.run_id", LIST_COLUMNS, [LIST_ROW, OLDER_LIST_ROW]),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS WHERE run_id",
            ("RUN_ID", "OPPORTUNITY_ID", "OPPORTUNITY_VERSION", "SUPPLIER_PROFILE_ID",
             "POLICY_VERSION", "PROVIDER", "STATE", "CREATED_AT", "TRACE"),
            [(RUN_ID, "opp-1", "v1", "supplier-1", "2026-08-02.v1", "CORTEX_CODE_CLI",
              "COMPLETED", "2026-08-02", TRACE)],
        ),
        (
            "SELECT o.*",
            ("OPPORTUNITY_ID", "TITLE", "BUYER_OBJECTIVE"),
            [("opp-1", "Public data quality service", "Improve public-data reliability")],
        ),
        ("SELECT p.*", ("SUPPLIER_PROFILE_ID", "SUPPLIER_NAME"), [("supplier-1", "Northstar Systems")]),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS",
            ("RUN_ID", "STATUS", "MISSING_ELIGIBILITY", "CAPACITY_GAP_HOURS"),
            [(RUN_ID, "PURSUE", "[]", 0)],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES",
            ("RUN_ID", "STRATEGY_ID", "TITLE", "STATEMENT", "SELECTED", "PROOF_CARDS",
             "WEAKNESS", "MITIGATION"),
            [
                (RUN_ID, "s-1", "Technical approach", "Win technical approach.", True,
                 '[{"kind": "past project", "label": "City Open Data"}]',
                 "No public-sector API reference", "Name the delivery lead"),
                (RUN_ID, "s-2", "Operational continuity", "Win operational continuity.", False,
                 "[]", None, None),
            ],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.RUBRIC_RESPONSE_PLANS",
            ("RUN_ID", "CRITERION_NAME", "WEIGHT", "ASSETS", "CLAIM", "OWNER"),
            [
                (RUN_ID, "Technical approach", 60, '["City Open Data"]',
                 "Deliver a measured data-quality improvement.", "Solution lead"),
                (RUN_ID, "Price", 40, "[]", "Price against the delivery envelope.", "Bid manager"),
            ],
        ),
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS",
            ("RUN_ID", "TASK_ID", "TASK_NAME", "OWNER", "STATUS"),
            [
                (RUN_ID, "rt-1-tech", "Add validation detail to the technical response",
                 "Solution lead", "OPEN"),
                # A real red-team control: it reviews the whole proposal and
                # maps to no single scored criterion.
                (RUN_ID, "rt-scope-creep-check", "Confirm the offer stays inside the tendered scope",
                 "Bid manager", "OPEN"),
                (RUN_ID, "t-1", "Own the Price response", "Bid manager", "OPEN"),
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
                (RUN_ID, "sec-2", "Price", "## Price\n\nPriced against the delivery envelope."),
            ],
        ),
        (
            "AS is_complete",
            ("AGENT_COUNT", "DECISION_COUNT", "STRATEGY_COUNT", "SELECTED_STRATEGY_COUNT",
             "PLAN_COUNT", "SECTION_COUNT", "TASK_COUNT", "IS_COMPLETE"),
            [(1, 1, 2, 1, 2, 2, 2, True)],
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
    return AppTest.from_file(APP_PATH)


def test_public_mode_enters_the_product_without_the_development_selector(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    workflow_labels = [option for widget in app.radio for option in widget.options]
    assert "Tender intake" not in workflow_labels
    assert "Bid Room replay" not in workflow_labels
    # The primary state carries the current stage. The labels stay bare.
    stage_labels = [button.label for button in app.button]
    for label in ("01 · Opportunities", "02 · Bid Decision", "03 · Win Plan", "04 · Proposal Room"):
        assert label in stage_labels
    assert not any("current stage" in label for label in stage_labels)
    assert any("Open bid decision" == button.label for button in app.button)


def test_opportunities_screen_reads_as_a_tender_choice_not_a_run_table(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    markdown = " ".join(item.value for item in app.markdown)
    assert "Choose an opportunity" in markdown
    assert "Opportunities with a persisted run" not in markdown
    # The opportunity names itself with its stored title and objective.
    assert "Public data quality service" in markdown
    assert "Improve public-data reliability" in markdown
    assert "Northstar Systems" in markdown
    # The run ID is provenance, never the visible label of the choice.
    assert RUN_ID not in markdown
    # No account inventory, no connection or role on the working screen.
    assert "recorded in this account" not in markdown
    assert "BIDPILOT_READER" not in markdown


def test_opportunities_screen_keeps_older_analyses_under_a_disclosure(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    # Two completed runs, one opportunity: the latest is active, the earlier
    # one stays reachable rather than competing as a second choice.
    assert app.session_state["product_run_id"] == RUN_ID
    assert any("Previous analyses (1)" in item.label for item in app.expander)
    assert app.button(key=f"open-analysis-{OLDER_RUN_ID}")


def test_working_screens_carry_no_internal_store_names(monkeypatch) -> None:
    """Stages 0 to 2 speak product language. Store names live in Run proof."""
    for stage in (0, 1, 2):
        with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
            connect.return_value = FakeConnection(product_responses())
            app = product_app(monkeypatch)
            app.session_state["product_stage"] = stage
            app.session_state["product_run_id"] = RUN_ID
            app.run(timeout=60)

        assert not app.exception
        markdown = " ".join(item.value for item in app.markdown)
        for name in STORE_NAMES:
            assert name not in markdown, f"{name} leaked onto stage {stage}"


def test_public_mode_walks_the_four_stages_of_one_persisted_run(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

        app.button(key="open-bid-decision").click()
        app.run(timeout=60)
        assert app.session_state["product_stage"] == 1
        decision_markdown = " ".join(item.value for item in app.markdown)
        assert "Why this is the decision" in decision_markdown
        # Concise natural English, and no repeated "recorded".
        assert "No eligibility gaps and no capacity shortfall." in decision_markdown
        assert "no missing eligibility recorded" not in decision_markdown
        # The header already names the opportunity and the supplier.
        assert "Opportunity and supplier in context" not in decision_markdown

        app.button(key="forward-to-2").click()
        app.run(timeout=60)
        assert app.session_state["product_stage"] == 2
        assert any("Official weighted evaluation score map" in item.value for item in app.markdown)
        assert any("Selected Win Position" in item.value for item in app.markdown)

        app.button(key="forward-to-3").click()
        app.run(timeout=60)
        assert app.session_state["product_stage"] == 3

    assert not app.exception
    draft = app.text_area(key=f"authenticated-draft::{RUN_ID}")
    assert "## Technical approach" in draft.value
    assert app.download_button


def test_proposal_room_renders_review_findings_as_readable_cards(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.session_state["product_stage"] = 3
        app.session_state["product_run_id"] = RUN_ID
        app.run(timeout=60)

    assert not app.exception
    markdown = " ".join(item.value for item in app.markdown)
    # Stacked cards, not a three-column table that shreds Owner and Status.
    assert 'class="br-find"' in markdown
    assert "Finding and closure action" not in markdown
    # Every persisted finding stays visible with its owner and its status.
    assert "Add validation detail to the technical response" in markdown
    assert "Owner · Solution lead" in markdown
    # The rt-N-<slug> convention still names the criterion the finding is on.
    assert "Technical approach" in markdown
    # A control over the whole proposal is labelled for what it is, not as a
    # gap in the record.
    assert "Confirm the offer stays inside the tendered scope" in markdown
    assert "Cross-cutting review" in markdown
    assert "Criterion not recorded" not in markdown
    # Owned work keeps its own zone in the same column.
    assert "Own the Price response" in markdown


def test_proposal_room_titles_the_work_as_turning_the_plan_into_a_proposal(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.session_state["product_stage"] = 3
        app.session_state["product_run_id"] = RUN_ID
        app.run(timeout=60)

    assert not app.exception
    markdown = " ".join(item.value for item in app.markdown)
    assert "Turn the win plan into a proposal" in markdown
    assert "Write the proposal this bid earned" not in markdown
    # The explanatory sentence stays with it.
    assert "Sections are composed from the stored plan and its written fragments." in markdown


def test_opportunity_card_shows_a_readable_date_and_ranks_its_facts(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.run(timeout=60)

    assert not app.exception
    card = next(item.value for item in app.markdown if 'class="br-opp__t"' in item.value)
    # The raw stored timestamp never reaches the card.
    assert "Aug 1, 2026" in card
    assert CREATED_AT_RAW not in card
    # Supplier and Mapped score lead; the rest is marked secondary so it can
    # stand down below 640px without leaving the DOM.
    assert "br-facts--opp" in card
    assert card.index("Supplier") < card.index("Latest analysis")
    for secondary in ("Latest analysis", "Proposal sections", "Owned work"):
        head = card[: card.index(secondary)]
        assert head.rindex("br-fact--secondary") > head.rindex('class="br-fact"')


def test_display_date_reads_stored_timestamps_without_shifting_them(monkeypatch, tmp_path: Path) -> None:
    module = app_module(monkeypatch, tmp_path)
    # An offset timestamp keeps the date its own offset records, even though
    # the same instant is the next day in UTC.
    assert module.display_date(CREATED_AT_RAW) == "Aug 1, 2026"
    assert module.display_date(
        dt.datetime(2026, 8, 1, 17, 9, tzinfo=dt.timezone(dt.timedelta(hours=-7)))
    ) == "Aug 1, 2026"
    assert module.display_date(dt.date(2026, 8, 1)) == "Aug 1, 2026"
    # Anything unparseable is shown exactly as stored rather than hidden.
    assert module.display_date("first quarter 2026") == "first quarter 2026"
    assert module.display_date(None) == ""


def test_cross_cutting_label_covers_every_real_red_team_task(monkeypatch, tmp_path: Path) -> None:
    """The four authored controls map to no criterion, and none is invented."""
    module = app_module(monkeypatch, tmp_path)
    criteria = ["Technical approach", "Comparable delivery", "Delivery team", "Price"]
    for task_id in (
        "rt-capacity-overcommit",
        "rt-credential-drift",
        "rt-hallucination-audit",
        "rt-scope-creep-check",
    ):
        task = {"task_id": task_id, "task_name": "Recorded control", "owner": "Bid manager"}
        assert module.finding_criterion(task, criteria) == ""
        card = module.review_finding_card(task, criteria)
        assert "Cross-cutting review" in card
        assert 'data-missing="false"' in card
    # A criterion-bearing identifier is still named by its criterion.
    assert module.finding_criterion({"task_id": "rt-1-tech"}, criteria) == "Technical approach"


def test_public_mode_download_follows_the_edited_draft_review(monkeypatch) -> None:
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        app = product_app(monkeypatch)
        app.session_state["product_stage"] = 3
        app.session_state["product_run_id"] = RUN_ID
        app.run(timeout=60)

        assert any("Review passed" in item.value for item in app.markdown)

        app.text_area(key=f"authenticated-draft::{RUN_ID}").set_value("## Price\n\nNothing else.")
        app.run(timeout=60)

    assert not app.exception
    assert any("Review failed" in item.value for item in app.markdown)
    assert app.download_button[0].disabled
