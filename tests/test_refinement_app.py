from __future__ import annotations

from types import SimpleNamespace

from bidpilot import refinement_app
from bidpilot.refinement_app import (
    DEFAULT_WORKSPACE,
    curated_tender_view,
    resolve_walkthrough,
    resolve_workspace,
    synthetic_demo_result,
)


def _record_render_calls(monkeypatch, query_params: dict[str, str]) -> list[str]:
    calls: list[str] = []
    monkeypatch.setattr(
        refinement_app,
        "st",
        SimpleNamespace(query_params=query_params),
    )
    monkeypatch.setattr(
        refinement_app,
        "_render_navigation",
        lambda workspace: calls.append(f"navigation:{workspace}"),
    )
    monkeypatch.setattr(
        refinement_app,
        "_render_tender_intake",
        lambda: calls.append("tender-intake"),
    )
    monkeypatch.setattr(
        refinement_app,
        "_render_synthetic_simulation",
        lambda: calls.append("synthetic-simulation"),
    )
    monkeypatch.setattr(refinement_app.ui, "render", lambda: calls.append("bid-room"))
    monkeypatch.setattr(
        refinement_app,
        "load_public_tender_catalog",
        lambda: calls.append("catalogue-load") or [],
    )
    monkeypatch.setattr(
        refinement_app,
        "render_markup",
        lambda markup: calls.append("dashboard-markup"),
    )
    return calls


def test_default_workspace_preserves_the_authenticated_bid_room() -> None:
    assert DEFAULT_WORKSPACE == "bid-room"
    assert resolve_workspace(None) == "bid-room"


def test_workspace_query_accepts_only_the_three_public_routes() -> None:
    assert resolve_workspace("tender-intake") == "tender-intake"
    assert resolve_workspace(["synthetic-simulation"]) == "synthetic-simulation"
    assert resolve_workspace("invented") == "bid-room"


def test_explicit_tender_intake_workspace_renders_navigation_and_intake(
    monkeypatch,
) -> None:
    calls = _record_render_calls(monkeypatch, {"workspace": "tender-intake"})

    refinement_app.render()

    assert calls == ["navigation:tender-intake", "tender-intake"]


def test_explicit_bid_room_workspace_renders_navigation_and_authenticated_ui(
    monkeypatch,
) -> None:
    calls = _record_render_calls(monkeypatch, {"workspace": "bid-room"})

    refinement_app.render()

    assert calls == ["navigation:bid-room", "bid-room"]


def test_explicit_synthetic_workspace_renders_navigation_and_isolated_view(
    monkeypatch,
) -> None:
    calls = _record_render_calls(monkeypatch, {"workspace": "synthetic-simulation"})

    refinement_app.render()

    assert calls == ["navigation:synthetic-simulation", "synthetic-simulation"]


def test_missing_or_invalid_workspace_preserves_the_koat_dashboard(monkeypatch) -> None:
    for query_params in ({}, {"workspace": "invented"}):
        calls = _record_render_calls(monkeypatch, query_params)

        refinement_app.render()

        assert calls == ["catalogue-load", "dashboard-markup", "dashboard-markup"]


def test_walkthrough_keeps_precedence_over_workspace_routing(monkeypatch) -> None:
    calls = _record_render_calls(
        monkeypatch,
        {"walkthrough": "1", "workspace": "tender-intake"},
    )

    refinement_app.render()

    assert calls == ["dashboard-markup", "bid-room"]


def test_tender_detail_keeps_precedence_over_workspace_routing(monkeypatch) -> None:
    calls = _record_render_calls(
        monkeypatch,
        {"tender": "NOTICE-1", "workspace": "synthetic-simulation"},
    )
    monkeypatch.setattr(
        refinement_app,
        "load_public_tender_catalog",
        lambda: (
            calls.append("catalogue-load")
            or [{"notice_number": "NOTICE-1", "evidence_level": "source-found"}]
        ),
    )

    refinement_app.render()

    assert calls == ["catalogue-load", "dashboard-markup", "dashboard-markup"]


def test_curated_tender_view_uses_the_verified_public_manifest() -> None:
    view = curated_tender_view()

    assert view["notice_number"] == "R26BK01680611-000"
    assert (
        view["source_sha256"]
        == "d196bed74cc66e9ce95331bdf0aef825f87b39ec1a85738d425b2dc4d48b476c"
    )
    assert view["evaluation_total"] == "Technical 90 · Price 10"
    assert view["supplier_boundary"] == "Synthetic demo supplier profile"
    assert view["analysis_gate"] == "Operator review required"


def test_synthetic_demo_result_is_local_and_never_persisted() -> None:
    result = synthetic_demo_result("missing-eligibility")

    assert result["verdict"] == "NO-GO"
    assert result["persisted"] is False
    assert result["provider"] == "LOCAL_PYTHON_POLICY"


def test_walkthrough_is_opt_in_so_the_public_first_paint_never_waits_for_snowflake() -> (
    None
):
    assert resolve_walkthrough(None) is False
    assert resolve_walkthrough("0") is False
    assert resolve_walkthrough(["1"]) is True
    assert resolve_walkthrough("true") is True


def test_curated_tender_view_carries_the_decision_package_facts() -> None:
    view = curated_tender_view()

    assert view["notice_number"] == "R26BK01680611-000"
    assert view["contract_value"] == "KRW 250M"
    assert view["technical_weight"] == "90"
    assert view["price_weight"] == "10"
    assert view["eligibility_count"] == "4"
