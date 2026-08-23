"""Escaped, deterministic HTML atoms for the BidPilot workspace shell.

These atoms do not know about domain objects, Streamlit session state, or
Snowflake.  Their only job is to preserve an evidence-first reading order when
the integration layer supplies real values.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from html import escape

PRODUCT_STATES = frozenset({"loading", "empty", "error", "incomplete", "disconnected"})
DECISION_PATH_LABELS = ("Decision", "Official weight", "Evidence state", "Owned action")


def esc(value: object) -> str:
    """Escape text that may originate in a tender, supplier profile, or run."""
    return escape(str(value if value is not None else "Not recorded"), quote=True)


def badge(label: object, tone: str = "neutral") -> str:
    """Return one compact WDS-informed state badge."""
    allowed = {"brand", "positive", "caution", "negative", "neutral", "outline"}
    if tone not in allowed:
        raise ValueError(f"Unknown badge tone: {tone}")
    return f'<span class="bpw-badge bpw-badge--{tone}">{esc(label)}</span>'


def fact_receipt(items: Iterable[tuple[object, object, object]]) -> str:
    """Render source or review facts as a numbered, wrapping receipt."""
    rows = []
    for index, (label, value, detail) in enumerate(items, start=1):
        rows.append(
            '<div class="bpw-receipt__item">'
            f'<span class="bpw-receipt__number" aria-hidden="true">{index:02d}</span>'
            '<div class="bpw-receipt__copy">'
            f'<p class="bpw-overline">{esc(label)}</p>'
            f'<p class="bpw-receipt__value">{esc(value)}</p>'
            f'<p class="bpw-caption">{esc(detail)}</p>'
            "</div></div>"
        )
    return '<div class="bpw-receipt">' + "".join(rows) + "</div>"


def decision_path(items: Sequence[tuple[object, object, object]]) -> str:
    """Render the non-negotiable decision-to-owner causal path."""
    labels = tuple(str(item[0]) for item in items)
    if labels != DECISION_PATH_LABELS:
        raise ValueError(
            "Decision path must be Decision, Official weight, Evidence state, Owned action"
        )
    cells = []
    for index, (label, value, detail) in enumerate(items, start=1):
        normalized = str(value).strip().upper()
        if index == 1:
            tone = {
                "PURSUE": "positive",
                "REVIEW": "caution",
                "NO-GO": "negative",
            }.get(normalized, "caution")
        elif index == 3:
            tone = "positive" if "0 OPEN" in normalized else "caution"
        else:
            tone = "brand"
        cells.append(
            f'<section class="bpw-path__item" data-step="{index:02d}">'
            '<div class="bpw-path__label">'
            f'<span aria-hidden="true">{index:02d}</span><span>{esc(label)}</span>'
            "</div>"
            f'<p class="bpw-path__value bpw-path__value--{tone}">{esc(value)}</p>'
            f'<p class="bpw-caption">{esc(detail)}</p>'
            "</section>"
        )
    return (
        '<div class="bpw-path" aria-label="Decision, official weight, evidence, and action">'
        + "".join(cells)
        + "</div>"
    )


def boundary_panel(title: object, detail: object, *, tone: str = "brand") -> str:
    """Render a persistent trust-boundary statement."""
    if tone not in {"brand", "caution", "neutral"}:
        raise ValueError(f"Unknown boundary tone: {tone}")
    return (
        f'<aside class="bpw-boundary bpw-boundary--{tone}" aria-label="Trust boundary">'
        '<span class="bpw-boundary__mark" aria-hidden="true"></span>'
        "<div>"
        f'<p class="bpw-boundary__title">{esc(title)}</p>'
        f'<p class="bpw-caption">{esc(detail)}</p>'
        "</div></aside>"
    )


def state_panel(
    state: str,
    *,
    title: object,
    detail: object,
    recovery_label: object | None = None,
    recovery_href: str | None = None,
) -> str:
    """Render an honest product state without replacing missing evidence."""
    if state not in PRODUCT_STATES:
        raise ValueError(f"Unknown product state: {state}")
    if bool(recovery_label) != bool(recovery_href):
        raise ValueError("Recovery label and href must be supplied together")

    role = "alert" if state in {"error", "disconnected"} else "status"
    action = ""
    if recovery_label and recovery_href:
        action = (
            f'<a class="bpw-state__action" href="{esc(recovery_href)}">'
            f"{esc(recovery_label)}</a>"
        )
    skeleton = (
        '<span class="bpw-state__skeleton" aria-hidden="true"><i></i><i></i><i></i></span>'
        if state == "loading"
        else '<span class="bpw-state__glyph" aria-hidden="true"></span>'
    )
    return (
        f'<section class="bpw-state bpw-state--{state}" data-state="{state}" '
        f'role="{role}" aria-live="polite">'
        f"{skeleton}<div>"
        f'<p class="bpw-overline">{esc(state)}</p>'
        f'<p class="bpw-state__title">{esc(title)}</p>'
        f'<p class="bpw-caption">{esc(detail)}</p>'
        f"{action}</div></section>"
    )


def section_heading(number: int, title: object, summary: object) -> str:
    """Return a KOAT-informed numbered section heading without KOAT branding."""
    return (
        '<header class="bpw-section-heading">'
        f'<span class="bpw-section-heading__number">{number:02d}</span>'
        "<div>"
        f"<h2>{esc(title)}</h2>"
        f"<p>{esc(summary)}</p>"
        "</div></header>"
    )
