from __future__ import annotations

from bidpilot.refinement_app import (
    DEFAULT_WORKSPACE,
    curated_tender_view,
    resolve_workspace,
    synthetic_demo_result,
)


def test_default_workspace_preserves_the_authenticated_bid_room() -> None:
    assert DEFAULT_WORKSPACE == "bid-room"
    assert resolve_workspace(None) == "bid-room"


def test_workspace_query_accepts_only_the_three_public_routes() -> None:
    assert resolve_workspace("tender-intake") == "tender-intake"
    assert resolve_workspace(["synthetic-simulation"]) == "synthetic-simulation"
    assert resolve_workspace("invented") == "bid-room"


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
