"""The public entry is a landing page in the SEAL grammar; the workspace sits behind it."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from bidpilot import refinement_app
from bidpilot.landing_ui import landing_css, landing_page
from bidpilot.tender_catalog import load_public_tender_catalog

CLOCK = datetime.fromisoformat("2026-09-03T15:40:00+09:00")


def test_landing_opens_cinematic_hero_then_story_bands_then_footer_cta() -> None:
    markup = landing_page(load_public_tender_catalog(), now=CLOCK)

    order = [
        markup.index('class="nav"'),
        markup.index('class="cine"'),
        markup.index("Decide the bid"),
        markup.index('class="pipe"'),
        markup.index('id="problem"'),
        markup.index('id="how"'),
        markup.index('id="proof"'),
        markup.index('id="agents"'),
        markup.index('class="footcta'),
        markup.index("<footer"),
    ]
    assert order == sorted(order)
    assert markup.count('class="pnode"') == 6
    assert "cortex-final-20260802-a" in markup
    for count in (
        "3 strategies",
        "4 weighted plans",
        "8 proposal sections",
        "12 owned tasks",
    ):
        assert count in markup
    assert "R26BK01680611-000" in markup
    assert "REVIEW" in markup and "16:00 KST" in markup


def test_landing_routes_into_the_workspace_and_the_agents() -> None:
    markup = landing_page(load_public_tender_catalog(), now=CLOCK)

    assert 'href="?view=opportunities"' in markup
    assert 'href="?tender=R26BK01680611-000"' in markup
    assert 'href="?walkthrough=1"' in markup
    assert "https://bidpilot-api-164282963747.us-central1.run.app/mcp" in markup
    assert "skills/bidpilot" in markup
    assert "<script" not in markup
    css = landing_css()
    assert "prefers-reduced-motion" in css
    assert "@media (max-width: 860px)" in css or "@media(max-width:860px)" in css


def _calls(monkeypatch, query_params):
    calls: list[str] = []
    monkeypatch.setattr(
        refinement_app, "st", SimpleNamespace(query_params=query_params)
    )
    monkeypatch.setattr(
        refinement_app, "render_markup", lambda m: calls.append("markup")
    )
    monkeypatch.setattr(refinement_app, "load_public_tender_catalog", lambda: [])
    monkeypatch.setattr(
        refinement_app,
        "landing_page",
        lambda rows, *, now: calls.append("landing") or "",
    )
    monkeypatch.setattr(
        refinement_app,
        "koat_dashboard",
        lambda rows, *, now: calls.append("dashboard") or "",
    )
    return calls


def test_bare_url_shows_the_landing_and_view_opportunities_shows_the_dashboard(
    monkeypatch,
) -> None:
    calls = _calls(monkeypatch, {})
    refinement_app.render()
    assert "landing" in calls and "dashboard" not in calls

    calls = _calls(monkeypatch, {"view": "opportunities"})
    refinement_app.render()
    assert "dashboard" in calls and "landing" not in calls
