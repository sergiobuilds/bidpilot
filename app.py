"""BidPilot's judge-facing decision-to-action workbench."""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

import streamlit as st

from bidpilot.bid_room import BidRoomStore
from bidpilot.engine import create_proposal_tasks, evaluate_bid
from bidpilot.fixtures import COMPANY, RFPS, SUPPLIER_PROFILES, TENDERS
from bidpilot.intake import (
    TenderIntakeError,
    build_pursuit_tender,
    intake_tender_bytes,
    intake_tender_url,
    review_tender_snapshot,
)
from bidpilot.proposal_writer import (
    compose_persisted_proposal,
    red_team_persisted_draft,
    red_team_proposal,
    red_team_tasks,
    write_strategy_proposal,
)
from bidpilot.pursuit import build_pursuit_brief, select_win_position
from bidpilot.snowflake_store import (
    EXPECTED_READER_ROLE,
    SnowflakeBidRoomError,
    SnowflakeBidRoomStore,
    configured_connection_name,
)

st.set_page_config(page_title="BidPilot · Bid Decision Workbench", page_icon="◈", layout="wide")

# The replay, intake and simulation surfaces keep their existing stylesheet.
# The authenticated surface has its own sheet further down; exactly one of the
# two is emitted per run so neither view inherits the other's rules.
LOCAL_STYLE = """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
      :root {
        --ink: #112620;
        --ink-soft: #4a635b;
        --paper: #f4f0e6;
        --paper-lift: #fbf8f0;
        --lime: #ccff00;
        --clay: #b8431f;
        --clay-wash: #f6cbba;
        --line: #c6bfb0;
        --serif: 'Fraunces', 'Iowan Old Style', Georgia, 'Times New Roman', serif;
        --mono: 'DM Mono', 'SFMono-Regular', 'Roboto Mono', Menlo, Consolas, monospace;
      }
      .stApp { background: var(--paper); color: var(--ink); }
      .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px; }
      h1, h2, h3, h4 { font-family: var(--serif) !important; color: var(--ink); letter-spacing: -.02em; }
      p, span, li, label, div, .stMarkdown { font-family: var(--mono); }
      hr { border-color: var(--line); }

      /* status rail */
      .bp-rail { display: flex; flex-wrap: wrap; align-items: baseline; gap: .35rem 2rem;
        border-top: 3px solid var(--ink); border-bottom: 1px solid var(--ink); padding: .55rem 0; margin-bottom: 1.35rem; }
      .bp-rail-item { display: flex; align-items: baseline; gap: .5rem; }
      .bp-rail-key { font-size: .63rem; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-rail-val { font-size: .8rem; font-weight: 500; }
      .bp-rail-mode { margin-left: auto; font-size: .63rem; letter-spacing: .13em; text-transform: uppercase;
        color: var(--ink-soft); border: 1px solid var(--line); padding: .18rem .5rem; }

      /* masthead */
      .bp-mast { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 1rem 2.5rem; margin-bottom: .5rem; }
      .bp-mast-left { max-width: 36rem; flex: 1 1 24rem; }
      .bp-kicker { font-size: .65rem; letter-spacing: .15em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-title { font-family: var(--serif); font-weight: 700; font-size: clamp(2.6rem, 5.4vw, 4.3rem);
        line-height: .86; letter-spacing: -.055em; margin: .3rem 0 .5rem; }
      .bp-lede { font-size: .82rem; line-height: 1.62; }
      .bp-mast-right { flex: 0 1 17rem; font-size: .72rem; line-height: 1.75; color: var(--ink-soft);
        border-left: 1px solid var(--line); padding-left: 1.1rem; }
      .bp-mast-right b { color: var(--ink); font-weight: 500; }

      /* section headers */
      .bp-sec { display: flex; flex-wrap: wrap; align-items: baseline; gap: .3rem .8rem;
        border-bottom: 1px solid var(--ink); padding-bottom: .3rem; margin: 1.5rem 0 .85rem; }
      .bp-sec-n { font-size: .65rem; letter-spacing: .12em; color: var(--ink-soft); }
      .bp-sec-t { font-family: var(--serif); font-weight: 600; font-size: 1.1rem; letter-spacing: -.02em; }
      .bp-sec-r { margin-left: auto; font-size: .65rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-soft); }

      /* decision block */
      .bp-decision { border: 2px solid var(--ink); padding: 1.05rem 1.1rem 1rem; }
      .bp-decision.is-bid { background: var(--lime); }
      .bp-decision.is-nobid { background: var(--clay-wash); }
      .bp-dec-top { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem;
        font-size: .63rem; letter-spacing: .14em; text-transform: uppercase; }
      .bp-dec-word { font-family: var(--serif); font-weight: 700; font-size: clamp(2.9rem, 6vw, 4rem);
        line-height: .88; letter-spacing: -.05em; margin: .25rem 0 .4rem; }
      .bp-dec-line { font-size: .81rem; line-height: 1.55; border-top: 1px solid rgba(17,38,32,.35); padding-top: .5rem; }
      .bp-dec-tally { display: flex; flex-wrap: wrap; gap: .25rem .9rem; margin-top: .45rem; font-size: .69rem; letter-spacing: .04em; }

      /* rationale + notes */
      .bp-reason { border-left: 3px solid var(--ink); padding: .1rem 0 .1rem .85rem; margin: .5rem 0; font-size: .81rem; line-height: 1.55; }
      .bp-note { font-size: .73rem; color: var(--ink-soft); line-height: 1.6; }

      /* trace */
      .bp-trace { font-size: .705rem; line-height: 1.72; white-space: pre-wrap; word-break: break-word;
        background: var(--paper-lift); border: 1px solid var(--line); border-left: 3px solid var(--ink);
        padding: .75rem .85rem; margin: 0; color: var(--ink); font-family: var(--mono); }

      /* scorecard */
      .bp-score { display: grid; grid-template-columns: repeat(auto-fit, minmax(8.4rem, 1fr));
        border-top: 2px solid var(--ink); border-left: 1px solid var(--line); }
      .bp-score-cell { border-right: 1px solid var(--line); border-bottom: 1px solid var(--line);
        padding: .6rem .7rem .65rem; background: rgba(255,255,255,.34); }
      .bp-score-k { font-size: .6rem; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-score-v { font-family: var(--serif); font-weight: 600; font-size: 1.42rem; line-height: 1.2; letter-spacing: -.03em; margin-top: .15rem; }
      .bp-score-v.is-neg { color: var(--clay); }
      .bp-score-s { font-size: .65rem; color: var(--ink-soft); }

      /* gate evidence */
      .bp-gate { border-top: 2px solid var(--ink); }
      .bp-gate-row { display: grid; grid-template-columns: minmax(6rem, .75fr) minmax(8rem, 1.7fr) auto;
        gap: .2rem .8rem; align-items: baseline; border-bottom: 1px solid var(--line); padding: .58rem 0 .6rem; }
      .bp-gate-name { font-size: .74rem; font-weight: 500; }
      .bp-gate-test { font-size: .71rem; line-height: 1.5; color: var(--ink-soft); }
      .bp-gate-test b { color: var(--ink); font-weight: 500; }
      .bp-gate-flag { font-size: .65rem; font-weight: 500; letter-spacing: .12em; padding: .16rem .45rem;
        justify-self: end; white-space: nowrap; }
      .bp-gate-flag.pass { background: var(--lime); color: var(--ink); border: 1px solid var(--ink); }
      .bp-gate-flag.fail { background: var(--clay-wash); color: var(--ink); border: 1px solid var(--clay); }
      .bp-gate-flag.info { background: transparent; color: var(--ink-soft); border: 1px solid var(--line); }

      /* work plan */
      .bp-work { border-top: 2px solid var(--ink); }
      .bp-work-row { display: grid; grid-template-columns: 1.6rem minmax(9rem, 1.7fr) minmax(6rem, .9fr) auto;
        gap: .25rem 1rem; align-items: baseline; border-bottom: 1px solid var(--line); padding: .6rem 0; font-size: .78rem; }
      .bp-work-n { color: var(--ink-soft); font-size: .67rem; }
      .bp-work-task b { font-weight: 500; }
      .bp-work-sub { display: block; font-size: .68rem; color: var(--ink-soft); line-height: 1.5; margin-top: .12rem; }
      .bp-work-owner { color: var(--ink-soft); font-size: .72rem; }
      .bp-work-due { font-weight: 500; letter-spacing: .04em; justify-self: end; }
      .bp-work-empty { border: 1px dashed var(--line); padding: .85rem; font-size: .76rem; color: var(--ink-soft); line-height: 1.6; }
      .bp-handoff { border: 2px solid var(--ink); background: var(--paper-lift); padding: .9rem 1rem; }
      .bp-handoff-k { font-size: .62rem; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-handoff-v { font-family: var(--serif); font-weight: 600; font-size: 1.22rem; letter-spacing: -.02em; margin: .2rem 0 .35rem; }
      .bp-handoff-p { font-size: .77rem; line-height: 1.6; }

      .bp-foot { border-top: 1px solid var(--ink); margin-top: 2rem; padding-top: .8rem;
        font-size: .71rem; line-height: 1.65; color: var(--ink-soft); }
      .bp-foot b { color: var(--ink); font-weight: 500; }

      /* streamlit chrome */
      .stButton button { background: var(--ink); color: var(--paper); border: 0; border-radius: 0;
        font-family: var(--mono); font-weight: 500; letter-spacing: .06em; text-transform: uppercase;
        font-size: .73rem; width: 100%; min-height: 2.9rem; }
      .stButton button:hover, .stButton button:focus { background: var(--clay); color: #fff; border: 0; }
      .stButton button:focus-visible { outline: 3px solid var(--ink); outline-offset: 2px; }
      section[data-testid="stSidebar"] { background: var(--paper-lift); border-right: 1px solid var(--ink); }
      section[data-testid="stSidebar"] .stRadio label { font-family: var(--mono); font-size: .77rem; }
      div[data-baseweb="select"] > div { border-radius: 0; border-color: var(--ink); background: var(--paper-lift); }
      @media (max-width: 900px) {
        .bp-mast-right { border-left: 0; border-top: 1px solid var(--line); padding: .8rem 0 0; }
        .bp-gate-row, .bp-work-row { grid-template-columns: 1fr auto; }
      }
    </style>
    """


# ---------------------------------------------------------------------------
# Authenticated product stylesheet.
#
# One design system only. These are the resolved light-mode tokens of the
# design system pinned by .design-system: cobalt as the single action colour,
# blue-tinted cool neutrals, pale blue contextual surfaces, solid hairline
# dividers, a compact fixed type scale and a 4px spacing rhythm. No font,
# image or script is fetched from the network; the brand face is replaced by
# the platform stack so nothing outside BidPilot is named on screen. Every
# table collapses into labelled cards below 720px, which is what keeps 390px
# free of horizontal overflow.
# ---------------------------------------------------------------------------

PRODUCT_STYLE = """
    <style>
      :root {
        --br-blue-40:#0054d1; --br-blue-45:#005eeb; --br-blue-50:#0066ff;
        --br-blue-80:#9ec5ff; --br-blue-90:#c9defe; --br-blue-95:#eaf2fe; --br-blue-99:#f7fbff;
        --br-cn-70:#989ba2; --br-cn-90:#c2c4c8; --br-cn-96:#e1e2e4; --br-cn-97:#eaebec;
        --br-cn-98:#f4f4f5; --br-cn-99:#f7f7f8;
        --br-green-40:#009632; --br-green-95:#d9ffe6;
        --br-orange-39:#d17600; --br-orange-95:#fef4e6;
        --br-red-40:#e52222; --br-red-95:#feecec;
        --br-label:#171719; --br-label-strong:#000;
        --br-label-neutral:rgba(46,47,51,.88); --br-label-alt:rgba(55,56,60,.61);
        --br-label-assistive:rgba(55,56,60,.28); --br-label-disable:rgba(55,56,60,.16);
        --br-line:#e1e2e4; --br-line-soft:#f4f4f5; --br-line-normal:rgba(112,115,124,.22);
        --br-fill:rgba(112,115,124,.08); --br-fill-soft:rgba(112,115,124,.05);
        --br-bg:#fff; --br-bg-alt:#f7f7f8;
        --br-shadow-xs:0 1px 2px -1px rgba(23,23,23,.1);
        --br-shadow-sm:0 2px 4px -2px rgba(23,23,23,.06), 0 4px 6px -1px rgba(23,23,23,.06);
        --br-s2:2px; --br-s4:4px; --br-s6:6px; --br-s8:8px; --br-s10:10px; --br-s12:12px;
        --br-s14:14px; --br-s16:16px; --br-s20:20px; --br-s24:24px; --br-s32:32px; --br-s40:40px;
        --br-r6:6px; --br-r8:8px; --br-r12:12px; --br-r16:16px; --br-r20:20px; --br-pill:1000px;
        --br-ease:cubic-bezier(.4,0,.2,1); --br-dur:220ms;
        --br-sans:"Pretendard JP Variable", -apple-system, BlinkMacSystemFont, system-ui,
          "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
        --br-mono: ui-monospace, "SF Mono", "JetBrains Mono", "Cascadia Mono", "Roboto Mono",
          Menlo, Consolas, monospace;
      }

      /* app frame ---------------------------------------------------------- */
      .stApp { background: var(--br-bg-alt); color: var(--br-label); }
      .stApp, .stApp p, .stApp li, .stApp label, .stApp div, .stApp button, .stApp input,
      .stApp select, .stApp textarea { font-family: var(--br-sans); }
      .block-container { padding-top: var(--br-s24); padding-bottom: var(--br-s40); max-width: 1180px; }
      .br-num { font-family: var(--br-mono); font-variant-numeric: tabular-nums; }
      .br-mono { font-family: var(--br-mono); overflow-wrap: anywhere; }

      /* Streamlit development chrome. The header element and its sidebar
         collapse control stay: at 390px it is the only route to the stage
         navigation. Only the toolbar, menu and footer are hidden. */
      div[data-testid="stToolbar"], #MainMenu, footer, div[data-testid="stDecoration"] { display: none; }
      header[data-testid="stHeader"] { background: transparent; }

      /* sidebar ------------------------------------------------------------ */
      section[data-testid="stSidebar"] { background: var(--br-bg); border-right: 1px solid var(--br-line); }
      /* Deliberate side padding on both edges of the rail, stated here rather
         than inherited, so no content sits against or beyond the edge. */
      section[data-testid="stSidebar"] .block-container { padding: var(--br-s16) var(--br-s24) var(--br-s32); }
      .br-brand { display: flex; align-items: center; gap: var(--br-s10); }
      .br-mark { position: relative; width: 26px; height: 26px; flex: none; border-radius: var(--br-r8);
        background: var(--br-blue-50); box-shadow: 0 4px 10px -2px rgba(0,102,255,.45); }
      .br-mark::after { content: ""; position: absolute; inset: 8px 8px auto 8px; height: 10px;
        border-radius: 1px; background: #fff; clip-path: polygon(0 100%, 50% 0, 100% 100%, 50% 72%); }
      .br-brand__name { font-size: 20px; line-height: 28px; font-weight: 600; letter-spacing: -.02em;
        color: var(--br-label-strong); }
      .br-status { display: inline-flex; align-items: center; gap: var(--br-s8); margin-top: var(--br-s12);
        padding: var(--br-s6) var(--br-s10); border-radius: var(--br-pill); font-size: 12px; line-height: 16px;
        font-weight: 600; max-width: 100%; }
      .br-status[data-tone="live"] { background: var(--br-green-95); color: var(--br-green-40); }
      .br-status[data-tone="down"] { background: var(--br-red-95); color: var(--br-red-40); }
      .br-status__dot { width: 6px; height: 6px; flex: none; border-radius: 50%; background: currentColor; }
      .br-status__text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .br-railkey { display: block; margin: var(--br-s20) 0 var(--br-s8); font-size: 11px; line-height: 14px;
        letter-spacing: .031em; text-transform: uppercase; font-weight: 600; color: var(--br-label-alt); }
      .br-context { padding: var(--br-s12) var(--br-s14); border-radius: var(--br-r12);
        background: var(--br-blue-95); }
      /* Key above value, not beside it: the context now carries a full tender
         title, which a fixed-width key column would shred into five lines. */
      .br-context__row { display: flex; flex-direction: column; gap: var(--br-s2); }
      .br-context__row + .br-context__row { margin-top: var(--br-s10); }
      .br-context__k { font-size: 11px; line-height: 14px; letter-spacing: .031em;
        text-transform: uppercase; font-weight: 600; color: var(--br-label-alt); }
      .br-context__v { font-size: 13px; line-height: 18px; color: var(--br-label-neutral);
        overflow-wrap: anywhere; }
      /* One quiet line, not a card: the boundary is a standing fact, not a
         thing the user has to read again on every screen. */
      .br-boundary { margin: var(--br-s20) 0 0; padding-top: var(--br-s12);
        border-top: 1px solid var(--br-line-soft); font-size: 11px; line-height: 16px;
        color: var(--br-label-alt); }

      /* page header -------------------------------------------------------- */
      .br-page { position: relative; overflow: hidden; padding: var(--br-s24) var(--br-s32);
        border-radius: var(--br-r20); border: 1px solid var(--br-line); background: var(--br-bg);
        box-shadow: var(--br-shadow-sm); }
      /* the one atmospheric moment on the surface, confined to this header */
      .br-page::before { content: ""; position: absolute; inset: -180px -160px auto 34%; height: 300px;
        background: conic-gradient(from 210deg at 60% 50%, rgba(0,102,255,.11), rgba(101,65,242,.08),
          rgba(0,152,178,.09), rgba(0,102,255,.11)); filter: blur(70px); pointer-events: none; }
      .br-page > * { position: relative; }
      .br-kicker { display: flex; flex-wrap: wrap; align-items: center; gap: var(--br-s8) var(--br-s12);
        margin: 0 0 var(--br-s12); font-size: 12px; line-height: 16px; letter-spacing: .025em;
        text-transform: uppercase; font-weight: 600; color: var(--br-label-alt); }
      .br-kicker b { color: var(--br-blue-45); font-weight: 600; }
      .br-kicker code { font-family: var(--br-mono); text-transform: none; letter-spacing: 0; }
      .br-page__grid { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: var(--br-s32);
        align-items: stretch; }
      .br-page__title { margin: 0; max-width: 34ch; font-size: 32px; line-height: 44px; font-weight: 700;
        letter-spacing: -.025em; color: var(--br-label-strong); }
      .br-page__sub { margin: var(--br-s12) 0 0; max-width: 60ch; font-size: 16px; line-height: 26px;
        color: var(--br-label-neutral); }
      .br-page__meta { margin: var(--br-s12) 0 0; font-size: 14px; line-height: 20px; color: var(--br-label-alt); }
      .br-page__meta b { color: var(--br-label-neutral); font-weight: 600; }

      /* verdict ------------------------------------------------------------ */
      .br-verdict { min-width: 232px; display: flex; flex-direction: column; justify-content: center;
        padding: var(--br-s20) var(--br-s24); border-radius: var(--br-r16); border: 1px solid var(--br-line);
        background: var(--br-bg); box-shadow: var(--br-shadow-xs); }
      .br-verdict__k { margin: 0 0 var(--br-s6); font-size: 12px; line-height: 16px; letter-spacing: .025em;
        text-transform: uppercase; font-weight: 600; color: var(--br-label-alt); }
      .br-verdict__v { margin: 0; display: flex; align-items: center; gap: var(--br-s10);
        font-size: 36px; line-height: 48px; font-weight: 700; letter-spacing: -.027em;
        color: var(--br-label-neutral); }
      .br-verdict__v::before { content: ""; width: 10px; height: 10px; flex: none; border-radius: 50%;
        background: currentColor; }
      .br-verdict[data-tone="positive"] .br-verdict__v { color: var(--br-green-40); }
      .br-verdict[data-tone="cautionary"] .br-verdict__v { color: var(--br-orange-39); }
      .br-verdict[data-tone="negative"] .br-verdict__v { color: var(--br-red-40); }
      .br-verdict__n { margin: var(--br-s8) 0 0; font-family: var(--br-mono); font-size: 11px;
        line-height: 16px; color: var(--br-label-alt); overflow-wrap: anywhere; }

      /* summary strip ------------------------------------------------------ */
      .br-summary { display: grid; grid-template-columns: repeat(3, minmax(0,1fr));
        margin-top: var(--br-s24); border-top: 1px solid var(--br-line); }
      .br-summary__cell { padding: var(--br-s16) var(--br-s24) var(--br-s4) 0; min-width: 0; }
      .br-summary__cell + .br-summary__cell { padding-left: var(--br-s24); border-left: 1px solid var(--br-line); }
      .br-summary__k { margin: 0 0 var(--br-s8); font-size: 12px; line-height: 16px; letter-spacing: .025em;
        text-transform: uppercase; font-weight: 600; color: var(--br-label-alt); }
      .br-summary__v { margin: 0; font-size: 18px; line-height: 26px; font-weight: 600; letter-spacing: -.015em;
        color: var(--br-label-strong); overflow-wrap: anywhere; }
      .br-summary__sub { margin: var(--br-s6) 0 0; font-size: 14px; line-height: 20px; color: var(--br-label-neutral); }

      /* section head and card ---------------------------------------------- */
      .br-sec { display: grid; grid-template-columns: 40px minmax(0,1fr); gap: 0 var(--br-s16);
        align-items: baseline; margin: var(--br-s24) 0 var(--br-s14); }
      .br-sec__i { font-family: var(--br-mono); font-size: 12px; letter-spacing: .06em;
        color: var(--br-blue-50); padding-top: 4px; }
      .br-sec__t { margin: 0; font-size: 22px; line-height: 30px; font-weight: 700; letter-spacing: -.018em;
        color: var(--br-label-strong); }
      .br-sec__src { grid-column: 2; margin: var(--br-s4) 0 0; font-family: var(--br-mono); font-size: 11px;
        line-height: 16px; color: var(--br-label-alt); }
      .br-card { border-radius: var(--br-r16); border: 1px solid var(--br-line); background: var(--br-bg);
        box-shadow: var(--br-shadow-xs); overflow: hidden; }
      .br-card + .br-card { margin-top: var(--br-s16); }
      .br-card__body { padding: var(--br-s20) var(--br-s24); }
      .br-card__body + .br-card__body { border-top: 1px solid var(--br-line-soft); }
      .br-card__body--flush { padding-inline: 0; padding-bottom: 0; }

      /* facts -------------------------------------------------------------- */
      .br-facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 1px;
        background: var(--br-line-soft); border: 1px solid var(--br-line-soft); border-radius: var(--br-r12);
        overflow: hidden; }
      .br-fact { background: var(--br-bg); padding: var(--br-s14) var(--br-s20); }
      .br-fact__k { margin: 0 0 var(--br-s6); font-size: 12px; line-height: 16px; letter-spacing: .025em;
        text-transform: uppercase; color: var(--br-label-alt); }
      .br-fact__v { margin: 0; font-size: 15px; line-height: 22px; font-weight: 600; color: var(--br-label-strong);
        overflow-wrap: anywhere; }
      .br-fact__v[data-tone="positive"] { color: var(--br-green-40); }
      .br-fact__v[data-tone="cautionary"] { color: var(--br-orange-39); }
      .br-fact__v[data-tone="negative"] { color: var(--br-red-40); }
      .br-fact__v[data-missing="true"] { color: var(--br-label-alt); font-weight: 400; }

      /* lists, notes, empties ---------------------------------------------- */
      .br-lines { margin: var(--br-s16) 0 0; padding: 0; list-style: none; display: flex;
        flex-direction: column; gap: var(--br-s8); }
      .br-lines li { display: flex; gap: var(--br-s10); font-size: 15px; line-height: 24px;
        color: var(--br-label-neutral); }
      .br-lines li::before { content: ""; flex: none; width: 5px; height: 5px; margin-top: 9px;
        border-radius: 50%; background: var(--br-blue-50); }
      .br-empty { padding: var(--br-s16) var(--br-s20); border-radius: var(--br-r12);
        background: var(--br-fill-soft); font-size: 14px; line-height: 21px; color: var(--br-label-neutral); }
      .br-note { margin: var(--br-s16) 0 0; font-size: 13px; line-height: 19px; color: var(--br-label-alt); }
      .br-missing { color: var(--br-label-assistive); }

      /* badges ------------------------------------------------------------- */
      .br-badge { display: inline-flex; align-items: center; gap: var(--br-s6); height: 24px;
        padding: 0 var(--br-s10); border-radius: var(--br-pill); font-size: 12px; line-height: 16px;
        font-weight: 600; white-space: nowrap; background: var(--br-fill); color: var(--br-label-neutral); }
      .br-badge::before { content: ""; width: 6px; height: 6px; flex: none; border-radius: 50%;
        background: currentColor; }
      .br-badge[data-tone="positive"] { background: var(--br-green-95); color: var(--br-green-40); }
      .br-badge[data-tone="cautionary"] { background: var(--br-orange-95); color: var(--br-orange-39); }
      .br-badge[data-tone="negative"] { background: var(--br-red-95); color: var(--br-red-40); }
      .br-badge[data-tone="accent"] { background: var(--br-blue-95); color: var(--br-blue-45); }

      /* coverage bar: one segment per criterion, width is its weight -------- */
      .br-cover { display: flex; gap: 5px; height: 18px; }
      .br-cover__seg { border-radius: var(--br-r6); min-width: 4px; }
      .br-cover__seg[data-tone="evidenced"] { background: var(--br-blue-50); }
      .br-cover__seg[data-tone="open"] { background: var(--br-cn-90); }
      .br-scale { display: flex; gap: 5px; margin-top: var(--br-s8); }
      .br-tick { font-family: var(--br-mono); font-size: 11px; line-height: 14px; color: var(--br-label-alt);
        overflow: hidden; white-space: nowrap; }
      .br-legend { display: flex; flex-wrap: wrap; gap: var(--br-s8) var(--br-s20); margin-top: var(--br-s12);
        font-size: 14px; line-height: 20px; color: var(--br-label-neutral); }
      .br-legend span { display: inline-flex; align-items: center; gap: var(--br-s8); }
      .br-legend i { width: 8px; height: 8px; border-radius: 2px; }
      .br-legend i[data-tone="evidenced"] { background: var(--br-blue-50); }
      .br-legend i[data-tone="open"] { background: var(--br-cn-90); }

      /* tables ------------------------------------------------------------- */
      .br-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
      .br-table caption { caption-side: top; text-align: left; padding: 0 var(--br-s20) var(--br-s16);
        font-size: 13px; line-height: 20px; color: var(--br-label-neutral); max-width: 78ch; }
      .br-table thead th { text-align: left; padding: var(--br-s12) var(--br-s20);
        background: var(--br-bg-alt); border-bottom: 1px solid var(--br-line); font-size: 13px;
        line-height: 18px; letter-spacing: .019em; font-weight: 600; color: var(--br-label-alt); }
      .br-table tbody td { padding: var(--br-s16) var(--br-s20); vertical-align: top; font-size: 14px;
        line-height: 22px; color: var(--br-label-neutral); border-bottom: 1px solid var(--br-line-soft);
        overflow-wrap: anywhere; }
      .br-table tbody tr:last-child td { border-bottom: 0; }
      .br-table tbody tr.is-lead td, .br-table tbody tr[data-selected="true"] td { background: rgba(0,102,255,.028); }
      .br-table tbody tr.row-claim td { padding-top: 0; padding-bottom: var(--br-s20); }
      .br-claim { margin: 0; padding-left: var(--br-s14); border-left: 2px solid var(--br-blue-90);
        font-size: 14px; line-height: 22px; color: var(--br-label-neutral); }
      .br-claim b { color: var(--br-label); font-weight: 600; }
      .br-crit { display: block; font-size: 15px; line-height: 22px; font-weight: 600; color: var(--br-label-strong); }
      .br-sub { display: block; margin-top: var(--br-s4); font-size: 12px; line-height: 16px;
        color: var(--br-label-alt); }
      .br-weight { display: flex; align-items: center; gap: var(--br-s10); }
      .br-weight__track { flex: 1; min-width: 40px; height: 8px; border-radius: var(--br-pill);
        background: var(--br-fill); overflow: hidden; }
      .br-weight__fill { display: block; height: 100%; border-radius: var(--br-pill); background: var(--br-blue-50); }
      .br-weight__n { font-family: var(--br-mono); font-size: 13px; font-weight: 600;
        font-variant-numeric: tabular-nums; color: var(--br-label-strong); }
      .br-chips { display: flex; flex-wrap: wrap; gap: var(--br-s6); }
      .br-chip { display: inline-flex; align-items: center; height: 24px; padding: 0 var(--br-s10);
        border-radius: var(--br-pill); background: var(--br-fill); font-size: 12px; line-height: 16px;
        color: var(--br-label-neutral); }

      /* opportunity card (screen 1) ---------------------------------------- */
      .br-opp { padding: var(--br-s24); }
      .br-opp__t { margin: var(--br-s12) 0 0; font-size: 26px; line-height: 36px; font-weight: 700;
        letter-spacing: -.022em; color: var(--br-label-strong); }
      .br-opp__s { margin: var(--br-s10) 0 0; max-width: 62ch; font-size: 16px; line-height: 26px;
        color: var(--br-label-neutral); }
      .br-prev { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: var(--br-s8) var(--br-s16);
        align-items: center; padding: var(--br-s10) 0; border-bottom: 1px solid var(--br-line-soft); }
      .br-prev__t { font-size: 14px; line-height: 20px; color: var(--br-label-neutral); }
      .br-prev__s { display: block; margin-top: var(--br-s2); font-size: 12px; line-height: 16px;
        color: var(--br-label-alt); }

      /* stacked finding and task cards (screen 4) -------------------------- */
      /* A three-column table is unreadable in a side column: owner wraps one
         letter per line. Each finding is one card with its own hierarchy. */
      .br-finds { display: grid; gap: var(--br-s10); margin-top: var(--br-s10); }
      .br-find { padding: var(--br-s14) var(--br-s16); border-radius: var(--br-r12);
        border: 1px solid var(--br-line); background: var(--br-bg); box-shadow: var(--br-shadow-xs); }
      .br-find__top { display: flex; flex-wrap: wrap; align-items: center; gap: var(--br-s8);
        justify-content: space-between; }
      .br-find__crit { font-size: 11px; line-height: 16px; letter-spacing: .031em; text-transform: uppercase;
        font-weight: 600; color: var(--br-blue-45); overflow-wrap: anywhere; }
      .br-find__crit[data-missing="true"] { color: var(--br-label-alt); }
      .br-find__t { margin: var(--br-s8) 0 0; font-size: 14px; line-height: 21px; font-weight: 600;
        color: var(--br-label-strong); overflow-wrap: anywhere; }
      .br-find__m { margin: var(--br-s6) 0 0; font-size: 13px; line-height: 18px;
        color: var(--br-label-alt); overflow-wrap: anywhere; }
      .br-zonenote { margin: 0; font-size: 13px; line-height: 19px; color: var(--br-label-alt); }

      /* win position ------------------------------------------------------- */
      .br-pos { padding: var(--br-s24); }
      .br-pos__t { margin: var(--br-s10) 0 0; font-size: 24px; line-height: 32px; font-weight: 700;
        letter-spacing: -.018em; color: var(--br-label-strong); }
      .br-pos__s { margin: var(--br-s10) 0 0; max-width: 62ch; font-size: 16px; line-height: 26px;
        color: var(--br-label-neutral); }
      .br-proofhead { padding: var(--br-s24) var(--br-s24) 0; background: var(--br-bg-alt);
        border-top: 1px solid var(--br-line-soft); }
      .br-proofs { list-style: none; margin: var(--br-s12) 0 0; padding: 0 var(--br-s24) var(--br-s24);
        background: var(--br-bg-alt); display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
        gap: var(--br-s12); }
      .br-proof { padding: var(--br-s12) var(--br-s14); border-radius: var(--br-r12);
        border: 1px solid var(--br-line); background: var(--br-bg); }
      .br-proof__k { display: block; font-size: 11px; line-height: 14px; letter-spacing: .031em;
        text-transform: uppercase; font-weight: 600; color: var(--br-blue-45); }
      .br-proof__l { display: block; margin-top: var(--br-s4); font-size: 14px; line-height: 20px;
        font-weight: 600; color: var(--br-label-strong); }
      .br-proof__d { display: block; margin-top: var(--br-s4); font-size: 12px; line-height: 17px;
        color: var(--br-label-alt); }
      .br-risk { margin: var(--br-s16) 0 0; padding-top: var(--br-s12); border-top: 1px solid var(--br-line-soft);
        font-size: 14px; line-height: 21px; color: var(--br-label-neutral); }
      .br-risk b { color: var(--br-label-strong); font-weight: 600; }
      .br-alts { list-style: none; margin: 0; padding: 0; }
      .br-alt { padding: var(--br-s16) 0; border-bottom: 1px solid var(--br-line-soft); }
      .br-alt:first-child { padding-top: 0; }
      .br-alt:last-child { border-bottom: 0; padding-bottom: 0; }
      .br-alt__t { margin: 0; font-size: 15px; line-height: 22px; font-weight: 600; color: var(--br-label-neutral); }
      .br-alt__s { margin: var(--br-s4) 0 0; font-size: 14px; line-height: 22px; color: var(--br-label-alt); }

      /* review status ------------------------------------------------------ */
      .br-review { display: grid; grid-template-columns: 8px minmax(0,1fr); margin-top: var(--br-s16);
        border-radius: var(--br-r12); border: 1px solid var(--br-line); overflow: hidden; background: var(--br-bg); }
      .br-review__spine { background: var(--br-green-40); }
      .br-review[data-tone="negative"] .br-review__spine { background: var(--br-red-40); }
      .br-review__body { padding: var(--br-s16) var(--br-s20); }
      .br-review__t { margin: 0; font-size: 14px; line-height: 20px; font-weight: 600; color: var(--br-green-40); }
      .br-review[data-tone="negative"] .br-review__t { color: var(--br-red-40); }
      .br-review__n { margin: var(--br-s6) 0 0; font-size: 14px; line-height: 21px; color: var(--br-label-neutral); }

      /* criterion checklist (proposal room) -------------------------------- */
      .br-check { list-style: none; margin: 0; padding: 0; }
      .br-check li { padding: var(--br-s12) 0; border-bottom: 1px solid var(--br-line-soft); }
      .br-check li:last-child { border-bottom: 0; }
      .br-check__t { display: flex; align-items: baseline; justify-content: space-between; gap: var(--br-s8);
        font-size: 14px; line-height: 20px; font-weight: 600; color: var(--br-label-strong); }
      .br-check__w { font-family: var(--br-mono); font-size: 12px; color: var(--br-label-alt); flex: none; }
      .br-check__s { display: block; margin-top: var(--br-s6); font-size: 12px; line-height: 17px; }
      .br-check__s[data-tone="positive"] { color: var(--br-green-40); }
      .br-check__s[data-tone="negative"] { color: var(--br-red-40); }

      /* provenance --------------------------------------------------------- */
      .br-meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr));
        gap: var(--br-s16) var(--br-s24); }
      .br-meta__k { margin: 0 0 var(--br-s4); font-size: 11px; line-height: 14px; letter-spacing: .031em;
        text-transform: uppercase; color: var(--br-label-alt); }
      .br-meta__v { margin: 0; font-family: var(--br-mono); font-size: 13px; line-height: 20px;
        color: var(--br-label); word-break: break-word; }
      .br-steps { display: grid; gap: var(--br-s8); margin-top: var(--br-s16); }
      .br-step { display: grid; grid-template-columns: 26px minmax(0,1fr); gap: var(--br-s12);
        padding: var(--br-s12); border-radius: var(--br-r8); background: var(--br-fill-soft); }
      .br-step__n { font-family: var(--br-mono); font-size: 12px; line-height: 18px; font-weight: 600;
        color: var(--br-blue-45); }
      .br-step__t { font-size: 13px; line-height: 18px; font-weight: 600; color: var(--br-label-strong); }
      .br-step__d { display: block; margin-top: var(--br-s2); font-family: var(--br-mono); font-size: 12px;
        line-height: 18px; color: var(--br-label-alt); overflow-wrap: anywhere; }
      .br-foot { margin-top: var(--br-s24); padding-top: var(--br-s16); border-top: 1px solid var(--br-line);
        font-size: 13px; line-height: 19px; color: var(--br-label-alt); }

      /* Streamlit controls -------------------------------------------------- */
      .stButton button, .stDownloadButton button, .stFormSubmitButton button {
        border-radius: var(--br-r12); border: 1px solid var(--br-line-normal); background: var(--br-bg);
        color: var(--br-label-neutral); font-weight: 600; font-size: 15px; min-height: 44px;
        transition: background var(--br-dur) var(--br-ease), border-color var(--br-dur) var(--br-ease); }
      .stButton button:hover, .stDownloadButton button:hover { background: var(--br-fill-soft);
        border-color: var(--br-cn-70); color: var(--br-label); }
      .stButton button[kind="primary"], .stButton button[data-testid="stBaseButton-primary"],
      .stDownloadButton button[kind="primary"], .stDownloadButton button[data-testid="stBaseButton-primary"],
      .stDownloadButton button[data-testid="stBaseButton-primary"]:hover {
        background: var(--br-blue-50); border-color: transparent; color: #fff;
        box-shadow: 0 4px 12px -4px rgba(0,102,255,.5); }
      .stButton button[kind="primary"]:hover, .stButton button[data-testid="stBaseButton-primary"]:hover {
        background: var(--br-blue-45); border-color: transparent; color: #fff; }
      .stButton button:disabled, .stDownloadButton button:disabled,
      .stButton button:disabled:hover, .stDownloadButton button:disabled:hover {
        background: var(--br-cn-98); border-color: transparent; color: var(--br-label-disable);
        box-shadow: none; cursor: not-allowed; }
      .stButton button:focus-visible, .stDownloadButton button:focus-visible,
      .stTextArea textarea:focus-visible, .stSelectbox div[data-baseweb="select"]:focus-within,
      div[data-testid="stExpander"] summary:focus-visible, .stRadio input:focus-visible + div {
        outline: 2px solid var(--br-blue-50); outline-offset: 2px; }
      /* nothing focusable may lose its ring, including links inside markdown */
      .stApp :focus-visible, section[data-testid="stSidebar"] :focus-visible {
        outline: 2px solid var(--br-blue-50); outline-offset: 2px; border-radius: var(--br-r8); }
      section[data-testid="stSidebar"] .stButton button { width: 100%; text-align: left;
        justify-content: flex-start; min-height: 40px; font-size: 14px; }
      .stTextArea textarea { font-family: var(--br-mono); font-size: 13px; line-height: 24px;
        border-radius: var(--br-r12); border: 1px solid var(--br-line-normal); background: var(--br-bg);
        color: var(--br-label-neutral); }
      div[data-baseweb="select"] > div { border-radius: var(--br-r12); border-color: var(--br-line-normal);
        background: var(--br-bg); }
      div[data-testid="stExpander"] { border: 1px solid var(--br-line); border-radius: var(--br-r12);
        background: var(--br-bg); overflow: hidden; }
      div[data-testid="stExpander"] summary { font-weight: 600; font-size: 14px; }
      .stAlert { border-radius: var(--br-r12); }

      /* responsive ---------------------------------------------------------- */
      /* Streamlit columns are a flex row; let them wrap so the proposal
         workspace becomes one readable column on a narrow viewport. */
      @media (max-width: 900px) {
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
        div[data-testid="stColumn"] { min-width: min(100%, 320px); flex: 1 1 100%; }
        .br-page__grid { grid-template-columns: minmax(0,1fr); gap: var(--br-s20); }
        .br-verdict { min-width: 0; }
        .br-summary { grid-template-columns: minmax(0,1fr); }
        .br-summary__cell { padding: var(--br-s16) 0; border-bottom: 1px solid var(--br-line-soft); }
        .br-summary__cell + .br-summary__cell { padding-left: 0; border-left: 0; }
        .br-summary__cell:last-child { border-bottom: 0; }
      }
      /* Tables become labelled cards. One DOM, one reading order. */
      @media (max-width: 720px) {
        .br-table, .br-table tbody, .br-table tr, .br-table td { display: block; width: 100%; }
        .br-table { table-layout: auto; }
        .br-table thead { display: none; }
        .br-table caption { display: block; width: 100%; padding-inline: var(--br-s16); }
        .br-table colgroup, .br-table col { display: none; }
        .br-table tbody tr { padding: var(--br-s16); border-bottom: 1px solid var(--br-line-soft); }
        .br-table tbody tr:last-child { border-bottom: 0; }
        .br-table tbody td { padding: 0; border-bottom: 0; }
        .br-table tbody td + td { margin-top: var(--br-s12); }
        .br-table tbody td[data-label]::before { content: attr(data-label); display: block;
          margin-bottom: var(--br-s4); font-size: 11px; line-height: 14px; letter-spacing: .031em;
          text-transform: uppercase; font-weight: 600; color: var(--br-label-alt); }
        .br-table tbody tr.row-claim { margin-top: calc(var(--br-s16) * -1); padding-top: 0; }
        .br-table tbody tr.row-claim td { margin-top: var(--br-s12); }
      }
      @media (max-width: 640px) {
        .block-container { padding-left: var(--br-s16); padding-right: var(--br-s16); }
        .br-page { padding: var(--br-s20); border-radius: var(--br-r16); }
        .br-page__title { font-size: 26px; line-height: 34px; }
        /* The opportunity card keeps Supplier and Mapped score above the fold.
           Analysis date, section count and owned work are shown again inside
           the workflow, so they stand down rather than push the one action
           this screen offers below the first viewport. */
        .br-facts--opp .br-fact--secondary { display: none; }
        .br-facts--opp .br-fact { padding: var(--br-s12) var(--br-s16); }
        /* The section navigator becomes a compact two-column index. The live
           review state is already beside the editor and below it, so the
           repeated readiness sentence is the one thing that goes. */
        .br-check { display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr));
          column-gap: var(--br-s12); row-gap: var(--br-s4); }
        /* The row gap separates the entries. A per-entry rule would land under
           one bottom cell and not the other. */
        .br-check li { padding: var(--br-s10) 0; border-bottom: 0; }
        .br-check__t { display: block; }
        .br-check__w { display: block; margin-top: var(--br-s2); }
        .br-check__s { display: none; }
        .br-verdict__v { font-size: 30px; line-height: 40px; }
        .br-sec { grid-template-columns: 28px minmax(0,1fr); gap: 0 var(--br-s10); }
        .br-sec__src { grid-column: 1 / -1; }
        .br-card__body { padding: var(--br-s20) var(--br-s16); }
        .br-pos, .br-proofs, .br-proofhead { padding-inline: var(--br-s16); }
      }
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; }
      }
    </style>
    """


# ---------------------------------------------------------------------------
# Derived display signals. These mirror the engine's arithmetic exactly and are
# used for presentation only; the recommendation always comes from evaluate_bid.
# ---------------------------------------------------------------------------


def derive_signals(rfp: dict, company: dict) -> dict:
    required = list(rfp["required_capabilities"])
    missing = sorted(set(required) - set(company["capabilities"]))
    capacity_gap = max(0, rfp["required_hours"] - company["available_hours"])
    coverage = min(1.0, company["available_hours"] / rfp["required_hours"])
    estimated_cost = rfp.get(
        "estimated_delivery_cost",
        rfp["required_hours"] * company["loaded_hourly_cost"],
    )
    expected_margin = rfp["contract_value"] - estimated_cost
    margin_rate = expected_margin / rfp["contract_value"]
    floor = company["minimum_margin_rate"]

    gates = [
        {
            "key": "capability",
            "name": "Qualification",
            "ok": not missing,
            "test": (
                f"<b>{len(required) - len(missing)}/{len(required)}</b> mandatory capabilities held"
                + (f" · missing <b>{', '.join(missing)}</b>" if missing else " · no exclusion")
            ),
            "trace": (
                f"required{{{len(required)}}} ∩ company{{{len(company['capabilities'])}}} → "
                + (f"missing[{', '.join(missing)}]" if missing else "missing[none]")
            ),
        },
        {
            "key": "capacity",
            "name": "Delivery capacity",
            "ok": capacity_gap == 0,
            "test": (
                f"<b>{company['available_hours']:,} h</b> available vs "
                f"<b>{rfp['required_hours']:,} h</b> required"
                + (f" · <b>{capacity_gap:,} h</b> short" if capacity_gap else " · covered")
            ),
            "trace": (
                f"{rfp['required_hours']:,}h required − {company['available_hours']:,}h available → "
                + (f"{capacity_gap:,}h short" if capacity_gap else "0h short")
            ),
        },
        {
            "key": "margin",
            "name": "Minimum margin",
            "ok": margin_rate >= floor,
            "test": f"<b>{margin_rate:.1%}</b> expected against a <b>{floor:.0%}</b> policy floor",
            "trace": (
                f"({rfp['contract_value']:,.0f} − {estimated_cost:,.0f}) / {rfp['contract_value']:,.0f}"
                f" = {margin_rate:.1%} {'≥' if margin_rate >= floor else '<'} {floor:.1%} floor"
            ),
        },
    ]
    for gate in gates:
        gate["flag"] = "PASS" if gate["ok"] else "FAIL"

    return {
        "gates": gates,
        "gates_passed": sum(1 for gate in gates if gate["ok"]),
        "gate_total": len(gates),
        "capacity_gap": capacity_gap,
        "coverage": coverage,
        "estimated_cost": estimated_cost,
        "expected_margin": expected_margin,
        "margin_rate": margin_rate,
        "margin_floor": floor,
    }


def build_trace(rfp: dict, gates: list[dict], recommendation: str) -> str:
    lines = [f"input.rfp     {rfp['id']} · contract {rfp['contract_value']:,.0f} USD"]
    lines += [f"gate.{gate['key']:<9} {gate['trace']} → {gate['flag']}" for gate in gates]
    failed = [gate["key"] for gate in gates if not gate["ok"]]
    verdict = f"any_gate_failed[{', '.join(failed)}]" if failed else "all_gates_passed"
    lines.append(f"policy        {verdict} → {recommendation}")
    return "\n".join(lines)


def work_row(index: str, title: str, subtitle: str, meta: str, due: str) -> str:
    sub = f'<span class="bp-work-sub">{subtitle}</span>' if subtitle else ""
    return (
        f'<div class="bp-work-row"><span class="bp-work-n">{index}</span>'
        f'<span class="bp-work-task"><b>{title}</b>{sub}</span>'
        f'<span class="bp-work-owner">{meta}</span>'
        f'<span class="bp-work-due">{due}</span></div>'
    )


def section(number: str, title: str, right: str = "") -> str:
    return (
        f'<div class="bp-sec"><span class="bp-sec-n">{number}</span>'
        f'<span class="bp-sec-t">{title}</span>'
        f'<span class="bp-sec-r">{right}</span></div>'
    )


def render_bid_room() -> None:
    """Render the end-to-end tender, strategy, proposal, and persistent run surface."""
    st.sidebar.markdown('<div class="bp-kicker">Tender replay</div>', unsafe_allow_html=True)
    tenders = list(TENDERS)
    if "intake_tender" in st.session_state:
        tenders.append(st.session_state["intake_tender"])
    tender = st.sidebar.selectbox("Tender", tenders, format_func=lambda item: item["title"])
    supplier = st.sidebar.selectbox("Supplier profile", SUPPLIER_PROFILES, format_func=lambda item: item["name"])
    brief = build_pursuit_brief(tender, supplier)
    position_labels = [f"{position.title} — {position.statement}" for position in brief.win_positions]
    selected_index = st.sidebar.radio("Win Position", range(len(position_labels)), format_func=lambda index: position_labels[index])
    brief = select_win_position(brief, tender, supplier, selected_index)
    position = brief.win_positions[selected_index]
    opportunity_version = tender.get("source_snapshot", {}).get("sha256", f"fixture:{tender['id']}:v1")
    input_key = f"{tender['id']}:{supplier['id']}:{selected_index}:{opportunity_version}"

    state_class = "is-bid" if brief.status == "PURSUE" else "is-nobid"
    st.markdown(
        f'<div class="bp-rail"><span class="bp-rail-item"><span class="bp-rail-key">Tender</span><span class="bp-rail-val">{tender["id"]}</span></span>'
        f'<span class="bp-rail-item"><span class="bp-rail-key">Supplier</span><span class="bp-rail-val">{supplier["name"]}</span></span>'
        f'<span class="bp-rail-item"><span class="bp-rail-key">Profile capacity</span><span class="bp-rail-val">{supplier["available_hours"]} h</span></span>'
        '<span class="bp-rail-mode">Local replay adapter · authenticated mode is separate</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''<div class="bp-mast"><div class="bp-mast-left"><div class="bp-kicker">B2G Pursuit Agent</div>
        <div class="bp-title">Win the score,<br>then write the bid.</div><div class="bp-lede">BidPilot connects a tender evaluation matrix to the supplier profile, selects a Win Position, builds score-bearing proposal sections, and stores the result as a Bid Room run.</div></div>
        <div class="bp-mast-right"><b>{html.escape(tender["title"])}</b><br><br>{html.escape(tender["buyer_objective"])}</div></div>''',
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(
            f'<div class="bp-decision {state_class}"><div class="bp-dec-top"><span>Pursuit decision</span><span>{supplier["id"]}</span></div>'
            f'<div class="bp-dec-word">{brief.status}</div><div class="bp-dec-line">{html.escape(" ".join(brief.next_actions))}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(section("01", "Selected Win Position", "strategy before drafting"), unsafe_allow_html=True)
        st.markdown(f'<div class="bp-reason">{html.escape(position.statement)}</div>', unsafe_allow_html=True)
        for card in position.proof_cards:
            st.markdown(f'<div class="bp-reason"><b>{html.escape(card.label)}</b> · {html.escape(card.detail)}</div>', unsafe_allow_html=True)
        if position.weakness:
            st.warning(f"Weakness: {position.weakness} Mitigation: {position.mitigation}")
    with right:
        st.markdown(section("02", "Score Map", "where the proposal must win"), unsafe_allow_html=True)
        st.dataframe(brief.score_map, hide_index=True, width="stretch")
        st.markdown(section("03", "Proposal Blueprint", "criterion → claim → owner"), unsafe_allow_html=True)
        st.dataframe(
            [{"Criterion": item.criterion, "Weight": item.weight, "Claim": item.claim, "Owner": item.owner} for item in brief.proposal_blueprint],
            hide_index=True,
            width="stretch",
        )

    st.markdown(section("04", "Build and Red-team", "one persisted run"), unsafe_allow_html=True)
    if st.button("Build strategy-led proposal", type="primary", disabled=not brief.can_generate_proposal):
        draft = write_strategy_proposal(tender, supplier, brief)
        findings = red_team_proposal(brief, draft)
        store = BidRoomStore(Path(".bidpilot") / "bidpilot.sqlite")
        tasks = tuple(
            {"task": f"Develop {section.criterion} response", "owner": section.owner, "status": "OPEN"}
            for section in brief.proposal_blueprint
        ) + tuple({"task": item["action"], "owner": item["owner"], "status": "OPEN"} for item in red_team_tasks(brief, draft))
        run_id = store.save(
            brief,
            opportunity_version=opportunity_version,
            proposal_markdown=draft,
            red_team_findings=findings,
            tasks=tasks,
        )
        st.session_state["bid_room"] = {"input_key": input_key, "run_id": run_id}
    if brief.status != "PURSUE":
        st.info("Proposal generation is blocked until this opportunity is pursueable.")
    result_state = st.session_state.get("bid_room")
    result = None
    store = BidRoomStore(Path(".bidpilot") / "bidpilot.sqlite")
    if result_state and result_state.get("input_key") == input_key:
        result = store.load(result_state["run_id"])
    elif brief.can_generate_proposal:
        result = store.latest(tender["id"], supplier["id"], opportunity_version, position.statement, brief)
    if result:
        st.success(f"Bid Room run saved: {result['run_id']}")
        edited_draft = st.text_area("Strategy-led proposal draft", result["proposal_markdown"], height=520)
        if result["red_team_findings"]:
            st.warning("Red-team findings: " + " ".join(result["red_team_findings"]))
        else:
            st.caption("Red-team: each score-bearing section includes a selected supplier asset.")
        st.caption("Pursuit tasks: " + " · ".join(task["task"] for task in result["tasks"]))
        st.caption("Agent trace: local-development-adapter only. Snowflake and CoCo execution has not occurred.")
        st.download_button("Download proposal draft", edited_draft, file_name="bidpilot-strategy-proposal.md", mime="text/markdown")
    st.markdown('<p class="bp-foot"><b>Demo boundary.</b> This workflow intentionally uses synthetic replay fixtures and local SQLite. Configure BIDPILOT_SNOWFLAKE_CONNECTION to open the authenticated Bid Room over the verified complete run.</p>', unsafe_allow_html=True)


def render_tender_intake() -> None:
    """Capture an untrusted public tender into a reviewable source snapshot."""
    st.markdown('<div class="bp-mast"><div class="bp-mast-left"><div class="bp-kicker">Tender intake</div><div class="bp-title">Capture the source.<br>Review before strategy.</div><div class="bp-lede">BidPilot records the source URL or PDF fingerprint, extracts the tender structure, and requires an explicit review of delivery inputs before it opens a Bid Room.</div></div><div class="bp-mast-right"><b>Untrusted document boundary</b><br>Document text is data. Instruction-like text is flagged and never executed.</div></div>', unsafe_allow_html=True)
    mode = st.radio("Source type", ("Upload PDF or text", "Public URL"), horizontal=True)
    snapshot = st.session_state.get("tender_snapshot")
    try:
        if mode == "Upload PDF or text":
            uploaded = st.file_uploader("Tender PDF or text", type=["pdf", "txt", "html"])
            if uploaded and st.button("Create source snapshot", type="primary"):
                content_type = uploaded.type or ("application/pdf" if uploaded.name.lower().endswith(".pdf") else "text/plain")
                st.session_state["tender_snapshot"] = intake_tender_bytes(uploaded.getvalue(), content_type=content_type)
                snapshot = st.session_state["tender_snapshot"]
        else:
            url = st.text_input("Public tender URL", placeholder="https://…")
            if url and st.button("Fetch public tender", type="primary"):
                st.session_state["tender_snapshot"] = intake_tender_url(url)
                snapshot = st.session_state["tender_snapshot"]
    except TenderIntakeError as error:
        st.error(str(error))
        return
    if not snapshot:
        return
    st.markdown(section("01", "Extracted source snapshot", snapshot.sha256[:16]), unsafe_allow_html=True)
    st.json({
        "source_url": snapshot.source_url,
        "sha256": snapshot.sha256,
        "retrieved_at": snapshot.retrieved_at,
        "instruction_like_content": snapshot.has_instruction_like_content,
        "title": snapshot.tender["title"],
        "scope": snapshot.tender["scope"],
        "eligibility": snapshot.tender["eligibility_requirements"],
        "evaluation_criteria": snapshot.tender["evaluation_criteria"],
        "submission_items": snapshot.tender["submission_items"],
    })
    if snapshot.has_instruction_like_content:
        st.warning("Instruction-like text was detected. It remains source data and is not used as an instruction.")
    st.markdown(section("02", "Review before Bid Room", "required operator confirmation"), unsafe_allow_html=True)
    reviewed_scope = st.text_area("Tender scope", snapshot.tender["scope"], height=90)
    reviewed_objective = st.text_area("Buyer objective", snapshot.tender["buyer_objective"], height=90)
    eligibility_text = st.text_area(
        "Eligibility requirements · one per line",
        "\n".join(snapshot.tender["eligibility_requirements"]),
        height=100,
    )
    criteria_text = st.text_area(
        "Official evaluation score map · Criterion | weight",
        "\n".join(f'{item["name"]} | {item["weight"]}' for item in snapshot.tender["evaluation_criteria"]),
        height=130,
        help="The reviewed top-level weights must be unique, positive, and total 100.",
    )
    tags = tuple(tag.strip() for tag in st.text_input("Scope tags", "public-data, data-quality").split(",") if tag.strip())
    hours = st.number_input("Estimated delivery hours", min_value=1, value=720)
    outcome = st.text_input("Promised buyer outcome", "A measurable service handoff")
    if st.button("Open reviewed Bid Room", type="primary"):
        try:
            reviewed_criteria = []
            for line in criteria_text.splitlines():
                if not line.strip():
                    continue
                if "|" not in line:
                    raise TenderIntakeError("Write each score-map row as 'Criterion | weight'.")
                name, weight = line.rsplit("|", 1)
                reviewed_criteria.append({"name": name.strip(), "weight": weight.strip()})
            reviewed_snapshot = review_tender_snapshot(
                snapshot,
                scope=reviewed_scope,
                buyer_objective=reviewed_objective,
                eligibility_requirements=tuple(eligibility_text.splitlines()),
                evaluation_criteria=tuple(reviewed_criteria),
            )
            st.session_state["tender_snapshot"] = reviewed_snapshot
            st.session_state["intake_tender"] = build_pursuit_tender(
                reviewed_snapshot,
                tags=tags,
                delivery_hours=int(hours),
                promised_outcome=outcome,
            )
            st.success("Reviewed tender is now available in Bid Room replay.")
        except TenderIntakeError as error:
            st.error(str(error))


# ---------------------------------------------------------------------------
# Authenticated Bid Room helpers.
#
# Snowflake hands back VARIANT and ARRAY columns as JSON text and NUMBER as
# Decimal, so every value is normalised before it reaches the markup. Nothing
# here supplies a substitute value: an absent field is labelled as absent.
# ---------------------------------------------------------------------------

NOT_RECORDED = "Not recorded in this analysis"

TRACE_TITLE_KEYS = ("opportunity_title", "tender_title", "title")
TRACE_OBJECTIVE_KEYS = ("buyer_objective", "objective", "summary")
TRACE_SESSION_KEYS = ("session_id", "snowflake_session_id", "session")
TRACE_QUERY_KEYS = ("query_id", "query_ids", "last_query_id", "queries")
TRACE_STEP_KEYS = ("steps", "stages", "events", "trace")
STEP_NAME_KEYS = ("step", "name", "stage", "action", "operation")
STEP_DETAIL_KEYS = ("sql", "object", "output", "result", "input", "status", "error")
ASSET_NAME_KEYS = ("label", "title", "name", "asset", "project_title", "project_id")

STATUS_TONES = {
    "PURSUE": "positive",
    "REVIEW": "cautionary",
    "NO-GO": "negative",
    "NO_GO": "negative",
}


def esc(value: object) -> str:
    """HTML-escape any Snowflake scalar without turning None into the word None."""
    return html.escape("" if value is None else str(value))


def as_records(value: object) -> list:
    """Return a VARIANT/ARRAY column as a list, keeping unparseable text visible."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except ValueError:
            return [text]
        if isinstance(parsed, list):
            return parsed
        return [parsed] if parsed not in (None, "") else []
    return [value]


def record_label(item: object) -> str:
    """Name one asset or proof record without inventing a label for it."""
    if isinstance(item, dict):
        for key in ASSET_NAME_KEYS:
            if item.get(key):
                return str(item[key])
        return json.dumps(item, ensure_ascii=False, sort_keys=True)
    return str(item)


def record_detail(item: object) -> str:
    """Turn a structured proof card into judge-readable supporting detail."""
    if not isinstance(item, dict):
        return ""
    details = []
    outcome = item.get("detail") or item.get("recorded_outcome") or item.get("outcome")
    if outcome:
        details.append(str(outcome))
    overlap = item.get("tag_overlap")
    if overlap:
        details.append(f"Tender-tag overlap: {overlap}")
    return " · ".join(details)


def as_number(value: object) -> float | None:
    """Coerce NUMBER/Decimal to float so weights can be summed and compared."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def trim(value: float) -> str:
    return f"{value:g}"


def first_key(mapping: object, keys: tuple[str, ...]) -> object:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        candidate = mapping.get(key)
        if candidate not in (None, "", [], {}):
            return candidate
    return None


def flatten(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def trace_steps(trace: object) -> list[dict]:
    """Return the run's stage list if the trace recorded one."""
    if not isinstance(trace, dict):
        return []
    for key in TRACE_STEP_KEYS:
        value = trace.get(key)
        if isinstance(value, list) and value:
            return [item if isinstance(item, dict) else {"step": str(item)} for item in value]
    return []


def br_section(index: str, title: str, source: str = "") -> str:
    return (
        f'<div class="br-sec"><span class="br-sec__i" aria-hidden="true">{esc(index)}</span>'
        f'<h2 class="br-sec__t">{esc(title)}</h2>'
        + (f'<p class="br-sec__src">{esc(source)}</p>' if source else "")
        + "</div>"
    )


def br_fact(key: str, value: str | None, tone: str = "", extra: str = "") -> str:
    """One decision fact. An absent value is labelled, never replaced.

    `extra` carries an optional modifier class so a caller can mark which of
    its facts are secondary. It changes styling only; the fact is always in
    the DOM.
    """
    missing = "true" if not value else "false"
    shown = value or NOT_RECORDED
    return (
        f'<div class="br-fact{" " + extra if extra else ""}"><p class="br-fact__k">{esc(key)}</p>'
        f'<p class="br-fact__v" data-tone="{tone}" data-missing="{missing}">{esc(shown)}</p></div>'
    )


def br_facts(items: list[tuple], extra: str = "") -> str:
    return (
        f'<div class="br-facts{" " + extra if extra else ""}">'
        + "".join(br_fact(*item) for item in items)
        + "</div>"
    )


def display_date(value: object) -> str:
    """Render a stored timestamp as a readable date, in its own offset.

    Accepts a datetime-like object or an ISO-8601 string. The value is never
    converted to another timezone: `2026-08-01 17:09:33-07:00` is Aug 1 for
    the buyer who filed it, whatever the reader's clock says. Anything that
    does not parse is returned unchanged, so a stored value is never hidden.
    """
    if value in (None, ""):
        return ""
    if isinstance(value, (dt.datetime, dt.date)):
        moment = value
    else:
        text = str(value).strip()
        try:
            moment = dt.datetime.fromisoformat(text)
        except ValueError:
            return str(value)
    # %-d is glibc-only, so the day number is formatted by hand.
    return f"{moment:%b} {moment.day}, {moment.year}"


def br_badge(text: str, tone: str = "") -> str:
    return f'<span class="br-badge" data-tone="{esc(tone)}">{esc(text)}</span>'


def br_empty(text: str) -> str:
    return f'<div class="br-empty">{esc(text)}</div>'


def br_table(
    headers: list[str],
    rows: list[list[str]],
    caption: str = "",
    widths: tuple[str, ...] = (),
    row_attrs: list[str] | None = None,
) -> str:
    """A fixed-layout table whose cells carry their own label.

    Below 720px the stylesheet turns every row into a labelled card using those
    data-label values, so the same DOM and the same reading order survive at
    390px without horizontal scrolling.
    """
    cols = "".join(f'<col style="width:{width}">' for width in widths)
    head = "".join(f'<th scope="col">{esc(header)}</th>' for header in headers)
    body = ""
    for index, cells in enumerate(rows):
        attributes = (row_attrs[index] if row_attrs else "") or ""
        # A row with fewer cells than headers is a continuation row: it spans
        # the table and carries no column label of its own.
        labelled = len(cells) == len(headers)
        cell_html = "".join(
            f'<td data-label="{esc(headers[position])}">{cell}</td>'
            if labelled
            else f'<td colspan="{len(headers)}">{cell}</td>'
            for position, cell in enumerate(cells)
        )
        body += f"<tr {attributes}>{cell_html}</tr>"
    return (
        '<table class="br-table">'
        + (f"<caption>{esc(caption)}</caption>" if caption else "")
        + (f"<colgroup>{cols}</colgroup>" if cols else "")
        + f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def br_card(body: str, flush: bool = False) -> str:
    modifier = " br-card__body--flush" if flush else ""
    return f'<section class="br-card"><div class="br-card__body{modifier}">{body}</div></section>'


# ---------------------------------------------------------------------------
# Authenticated product surface.
#
# The persisted run is read as a four-stage product rather than one long
# report: Opportunities, Bid Decision, Win Plan, Proposal Room. Each stage is
# a small render helper over one presentation-only projection of the store
# result; the store, policy, proposal composition, red-team and persistence
# contracts are used exactly as they are.
# ---------------------------------------------------------------------------

STAGES = (
    ("01", "Opportunities"),
    ("02", "Bid Decision"),
    ("03", "Win Plan"),
    ("04", "Proposal Room"),
)

STAGE_KEY = "product_stage"
RUN_KEY = "product_run_id"

REVIEW_TASK_CRITERIA = {
    "tech": "Technical approach",
    "deliv": "Comparable delivery",
    "team": "Delivery team",
    "price": "Price",
}

# Fields that already have a dedicated place on the Bid Decision screen, or
# that identify the row rather than explain the verdict.
DECISION_FIELDS_PLACED = {
    "run_id",
    "tenant_id",
    "decision_id",
    "created_at",
    "updated_at",
    "status",
    "opportunity_id",
    "opportunity_version",
    "supplier_profile_id",
    "policy_version",
    "missing_eligibility",
    "capacity_gap_hours",
}


def current_stage() -> int:
    return int(st.session_state.get(STAGE_KEY, 0))


def go_to_stage(index: int) -> None:
    """Move to a stage and redraw, so no screen renders one click behind."""
    st.session_state[STAGE_KEY] = max(0, min(index, len(STAGES) - 1))
    st.rerun()


@st.cache_data(show_spinner=False)
def load_persisted_runs(connection_name: str) -> list[dict]:
    """List runs once per session instead of on every widget interaction."""
    return SnowflakeBidRoomStore(connection_name).list_runs()


@st.cache_data(show_spinner=False)
def load_persisted_run(connection_name: str, run_id: str) -> dict:
    return SnowflakeBidRoomStore(connection_name).load_run(run_id)


def build_run_view(result: dict, run_id: str, opportunity_id: str = "") -> dict:
    """Project one stored run for display. Nothing here supplies a value."""
    run = result.get("run") or {}
    trace = run.get("trace") if isinstance(run.get("trace"), dict) else {}
    opportunity = result.get("opportunity") or {}
    supplier = result.get("supplier") or {}
    decision = result.get("decision") or {}
    strategies = result.get("strategies") or []
    selected = next(
        (item for item in strategies if item.get("selected")),
        strategies[0] if strategies else {},
    )
    criteria: list[dict] = []
    total_weight = 0.0
    covered_weight = 0.0
    for item in result.get("blueprint") or []:
        weight = as_number(item.get("weight")) or 0.0
        assets = [record_label(asset) for asset in as_records(item.get("assets"))]
        total_weight += weight
        if assets:
            covered_weight += weight
        criteria.append(
            {
                "name": str(item.get("criterion_name") or "").strip(),
                "weight": weight,
                "assets": assets,
                "claim": item.get("claim"),
                "owner": item.get("owner"),
            }
        )
    status = str(decision.get("status") or first_key(trace, ("pursuit_status", "status")) or "RECORDED")
    return {
        "run_id": run_id,
        "run": run,
        "trace": trace,
        "opportunity": opportunity,
        "supplier": supplier,
        "decision": decision,
        "strategies": strategies,
        "selected": selected,
        "blueprint": result.get("blueprint") or [],
        "sections": result.get("sections") or [],
        "tasks": result.get("tasks") or [],
        "criteria": criteria,
        "total_weight": total_weight,
        "covered_weight": covered_weight,
        "open_weight": total_weight - covered_weight,
        "lead": max(criteria, key=lambda item: item["weight"], default=None),
        "status": status,
        "tone": STATUS_TONES.get(status.upper(), "neutral"),
        # The opportunity identifies itself. A run ID is provenance and never
        # stands in as the name of the thing the user is choosing.
        "headline": (
            opportunity.get("title")
            or first_key(trace, TRACE_TITLE_KEYS)
            or run.get("opportunity_id")
            or opportunity_id
            or NOT_RECORDED
        ),
        "opportunity_id": run.get("opportunity_id") or opportunity_id or "",
        "objective": opportunity.get("buyer_objective") or first_key(trace, TRACE_OBJECTIVE_KEYS),
        "supplier_name": supplier.get("supplier_name") or run.get("supplier_profile_id"),
        "missing_eligibility": [
            record_label(item) for item in as_records(decision.get("missing_eligibility"))
        ],
        "capacity_gap_hours": as_number(decision.get("capacity_gap_hours")),
    }


def decision_summary(view: dict) -> str:
    """State the verdict in one plain sentence over the two recorded facts."""
    missing = view["missing_eligibility"]
    gap = view["capacity_gap_hours"]
    if not view["decision"]:
        return "No pursuit decision is stored for this analysis."
    if missing:
        eligibility = f"{len(missing)} eligibility requirement{'s' if len(missing) > 1 else ''} unmet"
    else:
        eligibility = "No eligibility gaps"
    if gap is None:
        capacity = "delivery capacity was not assessed"
    elif gap > 0:
        capacity = f"delivery capacity is {trim(gap)} hours short"
    else:
        capacity = "no capacity shortfall"
    # "but" only when the two clauses pull in opposite directions.
    clear_eligibility = not missing
    clear_capacity = gap is not None and gap <= 0
    joiner = " and " if clear_eligibility == clear_capacity else ", but "
    return f"{eligibility}{joiner}{capacity}."


def recorded_decision_extras(decision: dict) -> list[tuple[str, str, str]]:
    """Other decision columns, shown only where the run recorded a value."""
    extras = []
    for key, value in decision.items():
        if key in DECISION_FIELDS_PLACED or value in (None, "", [], {}):
            continue
        extras.append((str(key).replace("_", " ").capitalize(), flatten(value), ""))
    return extras


def render_stage_navigation(live: bool, opportunity: str = "", supplier: str = "") -> None:
    """The branded shell: identity, connection status, four stages, context.

    Connection health lives here rather than on the working screens, as a
    status only; the connection name and the reader role are provenance and
    sit in Run proof. The context block names the opportunity and the
    supplier, not the run identifier or the execution state.
    """
    status_tone = "live" if live else "down"
    status_text = "Live · Snowflake" if live else "Not reachable"
    st.sidebar.markdown(
        '<div class="br-brand"><span class="br-mark" aria-hidden="true"></span>'
        '<span class="br-brand__name">BidPilot</span></div>'
        f'<p class="br-status" data-tone="{status_tone}"><span class="br-status__dot" aria-hidden="true"></span>'
        f'<span class="br-status__text">{esc(status_text)}</span></p>'
        '<span class="br-railkey">Workflow</span>',
        unsafe_allow_html=True,
    )
    stage = current_stage()
    for index, (number, label) in enumerate(STAGES):
        is_current = index == stage
        # The primary state is the current-stage signal. No arrow, no suffix.
        if st.sidebar.button(
            f"{number} · {label}",
            key=f"stage-nav-{index}",
            type="primary" if is_current else "secondary",
            width="stretch",
        ):
            go_to_stage(index)
    if opportunity or supplier:
        st.sidebar.markdown(
            '<span class="br-railkey">Current opportunity</span>'
            '<div class="br-context">'
            f'<div class="br-context__row"><span class="br-context__k">Opportunity</span>'
            f'<span class="br-context__v">{esc(opportunity or NOT_RECORDED)}</span></div>'
            f'<div class="br-context__row"><span class="br-context__k">Supplier</span>'
            f'<span class="br-context__v">{esc(supplier or NOT_RECORDED)}</span></div>'
            "</div>",
            unsafe_allow_html=True,
        )
    st.sidebar.markdown(
        '<p class="br-boundary">Synthetic supplier fixture · closed public tender. '
        "Not a currently biddable notice.</p>",
        unsafe_allow_html=True,
    )


def render_primary_action(label: str, target: int, help_text: str = "", key: str = "") -> None:
    """The screen's one dominant action, kept inside the first viewport.

    It sits directly under the page header rather than at the end of the page,
    so at 1440 the current job and its next step are visible without scrolling.
    """
    action, _ = st.columns([1.4, 2.6], gap="small")
    with action:
        if st.button(
            label,
            key=key or f"forward-to-{target}",
            type="primary",
            width="stretch",
            help=help_text or None,
        ):
            go_to_stage(target)


def render_stage_footer(
    back: tuple[str, int] | None,
    forward: tuple[str, int] | None,
    forward_key: str = "",
) -> None:
    """Back, and the same forward step repeated at the end of a long screen."""
    back_column, forward_column, _ = st.columns([1, 1.4, 1.6], gap="small")
    if back:
        with back_column:
            if st.button(back[0], key=f"back-to-{back[1]}", width="stretch"):
                go_to_stage(back[1])
    if forward:
        with forward_column:
            if st.button(
                forward[0],
                key=forward_key or f"forward-to-{forward[1]}-again",
                type="primary",
                width="stretch",
            ):
                go_to_stage(forward[1])


def group_by_opportunity(complete: list[dict]) -> list[tuple[str, list[dict]]]:
    """Group completed analyses by opportunity, newest analysis first.

    The store already orders runs by created_at descending, so the first run in
    each group is that opportunity's latest completed analysis.
    """
    groups: dict[str, list[dict]] = {}
    for run in complete:
        key = str(run.get("opportunity_id") or run.get("run_id") or "")
        groups.setdefault(key, []).append(run)
    return list(groups.items())


def render_opportunities_screen(
    groups: list[tuple[str, list[dict]]],
    all_runs: list[dict],
    selected_row: dict | None,
    view: dict | None,
) -> None:
    """Screen 1. Choose the tender to work, and open its bid decision."""
    st.markdown(
        '<header class="br-page"><p class="br-kicker"><b>BidPilot Bid Room</b></p>'
        '<h1 class="br-page__title">Choose an opportunity</h1>'
        '<p class="br-page__sub">Open a tender to read its bid decision, then its win plan, then write '
        "its proposal.</p></header>",
        unsafe_allow_html=True,
    )

    if not groups:
        st.markdown(
            br_section("01", "Nothing is ready to open", "no opportunity has a finished analysis"),
            unsafe_allow_html=True,
        )
        st.warning(
            "No opportunity currently carries a finished analysis: a decision, a chosen win position, "
            "a weighted plan, proposal sections and owned work together."
        )
        if all_runs:
            rows = [
                [
                    (
                        f'<span class="br-crit">{esc(run.get("opportunity_id") or NOT_RECORDED)}</span>'
                        f'<span class="br-sub">Started {esc(run.get("created_at") or NOT_RECORDED)}</span>'
                    ),
                    esc(run.get("state") or NOT_RECORDED),
                    f'{esc(run.get("decision_count"))} decision · {esc(run.get("selected_strategy_count"))} chosen position',
                    f'{esc(run.get("plan_count"))} plan · {esc(run.get("section_count"))} section · {esc(run.get("task_count"))} task',
                ]
                for run in all_runs
            ]
            st.markdown(
                br_card(
                    br_table(
                        ["Opportunity", "State", "Decision and position", "Plan, sections and work"],
                        rows,
                        caption=(
                            "What each unfinished analysis is still missing. An unfinished analysis is "
                            "not opened, and no fixture stands in for it."
                        ),
                        widths=("34%", "16%", "24%", "26%"),
                    ),
                    flush=True,
                ),
                unsafe_allow_html=True,
            )
        return

    # With one opportunity on record the card is the choice. A picker appears
    # only when there is genuinely something to pick between.
    if len(groups) > 1:
        opportunity_ids = [key for key, _ in groups]
        current_group = next(
            (
                key
                for key, runs in groups
                if selected_row and selected_row["run_id"] in {run["run_id"] for run in runs}
            ),
            opportunity_ids[0],
        )
        chosen = st.selectbox(
            "Opportunity",
            options=opportunity_ids,
            index=opportunity_ids.index(current_group),
            key="opportunity-picker",
        )
        if chosen != current_group:
            latest = dict(groups)[chosen][0]
            st.session_state[RUN_KEY] = latest["run_id"]
            st.rerun()

    if selected_row is None:
        return
    active_group = next(
        (runs for _, runs in groups if selected_row["run_id"] in {run["run_id"] for run in runs}),
        [selected_row],
    )
    render_opportunity_card(selected_row, active_group, view)


def render_opportunity_card(
    selected_row: dict,
    active_group: list[dict],
    view: dict | None,
) -> None:
    """One product card for the opportunity, and its one primary action.

    Every field is read from the selected analysis. A field the analysis did
    not record is omitted rather than filled in.
    """
    title = view["headline"] if view else (selected_row.get("opportunity_id") or NOT_RECORDED)
    objective = (view or {}).get("objective")
    supplier = (view or {}).get("supplier_name") or selected_row.get("supplier_profile_id")
    status = view["status"] if view and view.get("decision") else None
    tone = view["tone"] if view and view.get("decision") else ""

    if view and view["total_weight"]:
        mapped = f'{trim(view["covered_weight"])} of {trim(view["total_weight"])} points'
    elif selected_row.get("plan_count") is not None:
        mapped = f'{selected_row["plan_count"]} criteria planned'
    else:
        mapped = None

    # "Latest" is only true while the group's newest analysis is the active one.
    is_latest = bool(active_group) and active_group[0]["run_id"] == selected_row["run_id"]
    # Supplier and Mapped score answer "is this mine, and is it worth opening".
    # The rest is context the workflow shows again later, so it is marked
    # secondary and stands down below 640px rather than delaying the action.
    facts = [
        ("Supplier", str(supplier) if supplier else None, "", ""),
        (
            "Latest analysis" if is_latest else "Analysis recorded",
            display_date(selected_row.get("created_at")) or None,
            "",
            "br-fact--secondary",
        ),
        ("Mapped score", mapped, "", ""),
        (
            "Proposal sections",
            str(selected_row.get("section_count")) if selected_row.get("section_count") is not None else None,
            "",
            "br-fact--secondary",
        ),
        (
            "Owned work",
            str(selected_row.get("task_count")) if selected_row.get("task_count") is not None else None,
            "",
            "br-fact--secondary",
        ),
    ]
    st.markdown(
        '<section class="br-card"><div class="br-opp">'
        + (br_badge(str(status), tone) if status else "")
        + f'<h2 class="br-opp__t">{esc(title)}</h2>'
        + (f'<p class="br-opp__s">{esc(objective)}</p>' if objective else "")
        + '</div><div class="br-card__body">'
        + br_facts(facts, "br-facts--opp")
        + "</div></section>",
        unsafe_allow_html=True,
    )

    action, _ = st.columns([1.4, 2.6], gap="small")
    with action:
        if st.button("Open bid decision", type="primary", key="open-bid-decision", width="stretch"):
            go_to_stage(1)

    previous = [run for run in active_group if run["run_id"] != selected_row["run_id"]]
    if previous:
        with st.expander(f"Previous analyses ({len(previous)})"):
            st.markdown(
                '<p class="br-zonenote">Earlier finished analyses of this opportunity. Opening one '
                "makes it the active analysis on every screen.</p>",
                unsafe_allow_html=True,
            )
            for run in active_group:
                is_active = run["run_id"] == selected_row["run_id"]
                label, control = st.columns([2.4, 1], gap="small")
                with label:
                    st.markdown(
                        '<div class="br-prev"><span><span class="br-prev__t">'
                        f'{esc(run.get("created_at") or NOT_RECORDED)}</span>'
                        f'<span class="br-prev__s">Version {esc(run.get("opportunity_version") or NOT_RECORDED)}'
                        f' · {esc(run.get("section_count"))} section · {esc(run.get("task_count"))} task'
                        "</span></span></div>",
                        unsafe_allow_html=True,
                    )
                with control:
                    if is_active:
                        st.markdown(br_badge("Active", "accent"), unsafe_allow_html=True)
                    elif st.button(
                        "Open this analysis",
                        key=f"open-analysis-{run['run_id']}",
                        width="stretch",
                    ):
                        st.session_state[RUN_KEY] = run["run_id"]
                        st.rerun()


def render_decision_screen(view: dict) -> None:
    """Screen 2. The verdict and the facts the run recorded behind it."""
    pursue = view["status"].upper() == "PURSUE"
    st.markdown(
        '<header class="br-page"><p class="br-kicker"><b>Bid decision</b></p>'
        '<div class="br-page__grid"><div>'
        f'<h1 class="br-page__title">{esc(view["headline"])}</h1>'
        f'<p class="br-page__sub">{esc(view["objective"]) if view["objective"] else "No buyer objective is stored for this opportunity."}</p>'
        f'<p class="br-page__meta">Supplier <b>{esc(view["supplier_name"] or NOT_RECORDED)}</b> · '
        f'Tender version <b>{esc(view["run"].get("opportunity_version") or NOT_RECORDED)}</b></p>'
        f'</div><div class="br-verdict" data-tone="{esc(view["tone"])}">'
        '<p class="br-verdict__k">Pursuit decision</p>'
        f'<p class="br-verdict__v">{esc(view["status"])}</p></div></div>'
        f'<p class="br-page__sub" style="margin-top:16px">{esc(decision_summary(view))}</p></header>',
        unsafe_allow_html=True,
    )

    if not pursue:
        st.warning(
            f"The decision on this opportunity is {view['status']}. The win plan is the evidence behind "
            "that decision, not an approval to bid, and the proposal room stays blocked behind its own "
            "red-team result."
        )
    render_primary_action("Build the win plan" if pursue else "Review win plan", 2)

    missing = view["missing_eligibility"]
    gap = view["capacity_gap_hours"]
    facts = [
        ("Decision", view["status"], view["tone"]),
        (
            "Missing eligibility",
            ", ".join(missing) if missing else ("None recorded" if view["decision"] else None),
            "negative" if missing else "positive" if view["decision"] else "",
        ),
        (
            "Capacity gap",
            None if gap is None else (f"{trim(gap)} h short" if gap > 0 else "No shortfall recorded"),
            "negative" if gap else "positive" if gap == 0 else "",
        ),
    ]
    facts.extend(recorded_decision_extras(view["decision"]))
    st.markdown(
        br_section("02", "Why this is the decision", "eligibility and delivery capacity against the tender"),
        unsafe_allow_html=True,
    )
    st.markdown(br_card(br_facts(facts)), unsafe_allow_html=True)

    render_stage_footer(
        ("Back to opportunities", 0),
        ("Build the win plan" if pursue else "Review win plan", 2),
    )


def render_win_plan_screen(view: dict) -> None:
    """Screen 3. The official weighted score map is the centre of the screen."""
    lead = view["lead"]
    total = view["total_weight"]
    covered = view["covered_weight"]
    open_points = view["open_weight"]
    st.markdown(
        '<header class="br-page"><p class="br-kicker"><b>Win plan</b></p>'
        '<h1 class="br-page__title">Where this bid wins the official score</h1>'
        '<p class="br-page__sub">Each criterion connects its weight, the supplier evidence attached to '
        "it, the claim the proposal will make and the owner who carries it.</p>"
        '<div class="br-summary"><div class="br-summary__cell">'
        '<p class="br-summary__k">Lead score target</p>'
        f'<p class="br-summary__v">{esc(lead["name"] or NOT_RECORDED) if lead else NOT_RECORDED}</p>'
        f'<p class="br-summary__sub">{esc(trim(lead["weight"])) if lead else "0"} of {esc(trim(total))} weighted points</p>'
        "</div><div class=\"br-summary__cell\">"
        '<p class="br-summary__k">Covered points</p>'
        f'<p class="br-summary__v">{esc(trim(covered))} pts</p>'
        '<p class="br-summary__sub">Criteria with at least one recorded supplier asset</p>'
        "</div><div class=\"br-summary__cell\">"
        '<p class="br-summary__k">Open points</p>'
        f'<p class="br-summary__v">{esc(trim(open_points))} pts</p>'
        '<p class="br-summary__sub">Criteria with no recorded supplier asset</p>'
        "</div></div></header>",
        unsafe_allow_html=True,
    )
    render_primary_action("Draft proposal with this strategy", 3)

    st.markdown(
        br_section("02", "Official weighted evaluation score map", "one row per criterion the buyer scores"),
        unsafe_allow_html=True,
    )
    criteria = view["criteria"]
    if criteria:
        # The bar is the shape of the score, not a progress meter: one segment
        # per criterion, sized by its weight against the full weighted total.
        segments = "".join(
            f'<span class="br-cover__seg" data-tone="{"evidenced" if item["assets"] else "open"}"'
            f' style="flex:{item["weight"] or 0}"></span>'
            for item in criteria
        )
        ticks = "".join(
            f'<span class="br-tick" style="flex:{item["weight"] or 0}">{esc(trim(item["weight"]))} '
            f'{esc(item["name"] or NOT_RECORDED)}</span>'
            for item in criteria
        )
        coverage = (
            '<div class="br-cover" role="img" aria-label="'
            f'{esc(trim(covered))} of {esc(trim(total))} weighted points carry a recorded supplier asset, '
            f'{esc(trim(open_points))} points remain open">{segments}</div>'
            f'<div class="br-scale" aria-hidden="true">{ticks}</div>'
            '<div class="br-legend"><span><i data-tone="evidenced"></i>'
            f'Supplier asset recorded · {esc(trim(covered))} pts</span>'
            '<span><i data-tone="open"></i>'
            f'No asset recorded · {esc(trim(open_points))} pts</span></div>'
        )
        rows = []
        row_attrs = []
        for item in criteria:
            evidenced = bool(item["assets"])
            fill = (item["weight"] / total * 100) if total else 0
            assets_html = (
                '<span class="br-chips">'
                + "".join(f'<span class="br-chip">{esc(asset)}</span>' for asset in item["assets"])
                + "</span>"
                if evidenced
                else f'<span class="br-missing">{NOT_RECORDED}</span>'
            )
            rows.append(
                [
                    (
                        f'<span class="br-crit">{esc(item["name"] or NOT_RECORDED)}</span>'
                        f'<span class="br-sub">Owner · {esc(item["owner"] or NOT_RECORDED)}</span>'
                    ),
                    (
                        '<span class="br-weight"><span class="br-weight__track">'
                        f'<span class="br-weight__fill" style="width:{fill:.0f}%"></span></span>'
                        f'<span class="br-weight__n">{esc(trim(item["weight"]))}</span></span>'
                    ),
                    br_badge("Asset recorded" if evidenced else "No asset", "accent" if evidenced else ""),
                    assets_html,
                ]
            )
            row_attrs.append('class="is-lead"' if lead and item is lead else "")
            rows.append(
                [
                    f'<p class="br-claim"><b>Planned claim.</b> {esc(item["claim"] or NOT_RECORDED)}</p>'
                ]
            )
            row_attrs.append('class="row-claim"')
        table = br_table(
            ["Criterion", "Weight", "Evidence", "Supplier asset"],
            rows,
            caption=(
                "A criterion counts as evidenced when the analysis recorded at least one supplier asset "
                "against it. Bars are scaled against the full weighted total, so a 40-point criterion "
                "reads as 40 per cent of the score."
            ),
            widths=("28%", "22%", "18%", "32%"),
            row_attrs=row_attrs,
        )
        st.markdown(
            f'<section class="br-card"><div class="br-card__body">{coverage}</div>'
            f'<div class="br-card__body br-card__body--flush">{table}</div></section>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            br_card(br_empty("No weighted criterion is stored for this analysis.")),
            unsafe_allow_html=True,
        )

    selected = view["selected"]
    st.markdown(
        br_section("03", "Selected Win Position", "the position chosen, and the ones it was compared against"),
        unsafe_allow_html=True,
    )
    if selected:
        proofs = "".join(
            '<li class="br-proof">'
            f'<span class="br-proof__k">{esc(card.get("kind")) if isinstance(card, dict) and card.get("kind") else "Proof"}</span>'
            f'<span class="br-proof__l">{esc(record_label(card))}</span>'
            + (f'<span class="br-proof__d">{esc(record_detail(card))}</span>' if record_detail(card) else "")
            + "</li>"
            for card in as_records(selected.get("proof_cards"))
        )
        weakness = selected.get("weakness")
        mitigation = selected.get("mitigation")
        risk = (
            f'<p class="br-risk"><b>Recorded weakness.</b> {esc(weakness)}'
            + (f' <b>Mitigation.</b> {esc(mitigation)}' if mitigation else "")
            + "</p>"
            if weakness
            else f'<p class="br-risk"><b>Recorded weakness.</b> {NOT_RECORDED}</p>'
        )
        alternates = "".join(
            f'<li class="br-alt"><p class="br-alt__t">{esc(item.get("title") or NOT_RECORDED)}</p>'
            f'<p class="br-alt__s">{esc(item.get("statement") or NOT_RECORDED)}</p></li>'
            for item in view["strategies"]
            if item is not selected
        )
        st.markdown(
            '<section class="br-card"><div class="br-pos">'
            + br_badge("Selected", "accent")
            + f'<h3 class="br-pos__t">{esc(selected.get("title") or NOT_RECORDED)}</h3>'
            f'<p class="br-pos__s">{esc(selected.get("statement") or NOT_RECORDED)}</p>'
            + risk
            + "</div>"
            + (
                '<p class="br-proofhead br-summary__k">Proof carried into the proposal</p>'
                f'<ul class="br-proofs">{proofs}</ul>'
                if proofs
                else ""
            )
            + (
                '<div class="br-card__body"><p class="br-summary__k">Alternate positions compared</p>'
                f'<ul class="br-alts">{alternates}</ul></div>'
                if alternates
                else ""
            )
            + "</section>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            br_card(br_empty("No Win Position is stored for this analysis.")),
            unsafe_allow_html=True,
        )
    render_stage_footer(("Back to bid decision", 1), ("Draft proposal with this strategy", 3))


def finding_criterion(task: dict, criterion_names: list[str]) -> str:
    """Name the criterion a finding belongs to, using only recorded values.

    The `rt-<n>-<slug>` identifier is the authored signal and comes first. Only
    if it names nothing do we fall back to a criterion this bid actually
    scores appearing in the finding text. Nothing looser, because a short name
    like "Price" matches ordinary prose and would be a guess stated as a fact.
    """
    parts = str(task.get("task_id") or "").lower().split("-")
    if len(parts) > 2 and parts[2] in REVIEW_TASK_CRITERIA:
        return REVIEW_TASK_CRITERIA[parts[2]]
    lowered = str(task.get("task_name") or "").lower()
    for name in criterion_names:
        if name and name.lower() in lowered:
            return name
    return ""


CROSS_CUTTING = "Cross-cutting review"


def review_finding_card(task: dict, criterion_names: list[str]) -> str:
    """One finding as a compact card: criterion, action, owner, status.

    A finding that names no criterion is a control over the whole proposal —
    capacity, credentials, hallucination, scope — not a gap in the score map.
    It is labelled for what it is instead of reported as missing data.
    """
    criterion = finding_criterion(task, criterion_names)
    return (
        '<div class="br-find"><div class="br-find__top">'
        '<span class="br-find__crit" data-missing="false">'
        f'{esc(criterion) if criterion else CROSS_CUTTING}</span>'
        + br_badge(str(task.get("status") or NOT_RECORDED), "cautionary")
        + "</div>"
        f'<p class="br-find__t">{esc(task.get("task_name") or NOT_RECORDED)}</p>'
        f'<p class="br-find__m">Owner · {esc(task.get("owner") or NOT_RECORDED)}</p></div>'
    )


def render_proposal_screen(view: dict) -> None:
    """Screen 4. A proposal workspace: navigation, editor, review and closure."""
    run_id = view["run_id"]
    st.markdown(
        '<header class="br-page"><p class="br-kicker"><b>Proposal room</b></p>'
        '<h1 class="br-page__title">Turn the win plan into a proposal</h1>'
        '<p class="br-page__sub">Sections are composed from the stored plan and its written fragments. '
        "Edits stay in this session and are re-checked against the score map on every change.</p></header>",
        unsafe_allow_html=True,
    )

    if not view["sections"]:
        st.markdown(
            br_section("04", "Proposal workspace", "draft, review and owned work"),
            unsafe_allow_html=True,
        )
        st.warning(
            "This analysis has no written proposal section, so there is nothing to draft here. "
            "Choose another opportunity on the Opportunities screen."
        )
        render_stage_footer(("Back to win plan", 2), None)
        return

    st.markdown(
        br_section("04", "Proposal workspace", "draft, review findings and owned work"),
        unsafe_allow_html=True,
    )
    # Declaration order is the stacking order below 900px: sections, editor,
    # review. Widths favour the editor, then review, then the section list.
    navigation, workspace, closure = st.columns([1.0, 2.3, 1.7], gap="medium")

    with workspace:
        st.markdown("### Editable draft")
        draft = compose_persisted_proposal(view["blueprint"], view["sections"])
        edited = st.text_area(
            "Proposal draft",
            draft,
            height=520,
            key=f"authenticated-draft::{run_id}",
            help="Edits stay in this session and are not written back to Snowflake.",
        )
        findings = red_team_persisted_draft(view["blueprint"], edited)
        if findings:
            st.markdown(
                '<div class="br-review" data-tone="negative" role="status">'
                '<span class="br-review__spine" aria-hidden="true"></span>'
                '<div class="br-review__body"><p class="br-review__t">Review failed · '
                f'{len(findings)} open finding(s)</p>'
                '<p class="br-review__n">Resolve every finding listed beside the draft before the '
                "download opens.</p></div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="br-review" data-tone="positive" role="status">'
                '<span class="br-review__spine" aria-hidden="true"></span>'
                '<div class="br-review__body"><p class="br-review__t">Review passed · no open finding</p>'
                '<p class="br-review__n">Every score-bearing criterion carries its selected supplier asset, '
                "and the highest-weight response carries validation and outcome detail.</p></div></div>",
                unsafe_allow_html=True,
            )
        st.download_button(
            "Download proposal draft",
            edited,
            file_name=f"{run_id}.md",
            mime="text/markdown",
            type="primary",
            disabled=bool(findings),
            key=f"download-draft::{run_id}",
            help=(
                "Resolve the current red-team findings before downloading."
                if findings
                else "Downloads exactly the edited text above."
            ),
        )

    with navigation:
        st.markdown("### Score-bearing sections")
        failed = {item["criterion"]: item["finding"] for item in findings}
        items = ""
        for item in view["criteria"]:
            finding = failed.get(item["name"])
            tone = "negative" if finding else "positive"
            state = finding if finding else "Section present with its recorded asset."
            items += (
                f'<li><span class="br-check__t">{esc(item["name"] or NOT_RECORDED)}'
                f'<span class="br-check__w">{esc(trim(item["weight"]))} pts</span></span>'
                f'<span class="br-check__s" data-tone="{tone}">'
                f'{"Open · " if finding else "Ready · "}{esc(state)}</span></li>'
            )
        st.markdown(f'<ul class="br-check">{items}</ul>', unsafe_allow_html=True)

    with closure:
        st.markdown("### Review and closure")
        tasks = view["tasks"]
        # Findings and the rest of the owned work partition the same task list.
        # Every finding is still rendered in full, just once.
        review_tasks = [
            task for task in tasks if str(task.get("task_id") or "").lower().startswith("rt-")
        ]
        owned = [task for task in tasks if task not in review_tasks]
        criterion_names = [item["name"] for item in view["criteria"] if item["name"]]
        if review_tasks:
            st.markdown(
                f'<p class="br-zonenote">{len(review_tasks)} red-team finding'
                f'{"s" if len(review_tasks) != 1 else ""} recorded against this bid. '
                "Every finding stays listed, closed or not.</p>"
                '<div class="br-finds">'
                + "".join(
                    review_finding_card(task, criterion_names) for task in review_tasks
                )
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                br_card(br_empty("No red-team finding is recorded against this bid.")),
                unsafe_allow_html=True,
            )
        st.markdown("#### Owned work")
        if owned:
            st.markdown(
                '<div class="br-finds">'
                + "".join(
                    '<div class="br-find"><div class="br-find__top">'
                    f'<span class="br-find__crit">Owner · {esc(task.get("owner") or NOT_RECORDED)}</span>'
                    + br_badge(str(task.get("status") or NOT_RECORDED), "")
                    + "</div>"
                    f'<p class="br-find__t">{esc(task.get("task_name") or NOT_RECORDED)}</p></div>'
                    for task in owned
                )
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                br_card(br_empty("No pursuit work is recorded against this bid.")),
                unsafe_allow_html=True,
            )
        render_run_proof(view)

    render_stage_footer(("Back to win plan", 2), None)


def render_run_proof(view: dict) -> None:
    """Execution provenance, folded away: proof of the run, not a fifth screen."""
    run = view["run"]
    trace = view["trace"]
    provenance = (
        trace.get("execution_provenance") if isinstance(trace.get("execution_provenance"), dict) else {}
    )
    session_id = first_key(provenance, ("cortex_session_id", "session_id")) or first_key(trace, TRACE_SESSION_KEYS)
    query_ids = first_key(provenance, ("cortex_write_query_ids", "query_ids")) or first_key(trace, TRACE_QUERY_KEYS)
    with st.expander("Run proof · execution provenance"):
        st.markdown(
            '<div class="br-meta">'
            + "".join(
                f'<div><p class="br-meta__k">{esc(key)}</p>'
                f'<p class="br-meta__v">{esc(value) if value else NOT_RECORDED}</p></div>'
                for key, value in (
                    ("Run identifier", view["run_id"]),
                    ("Connection", configured_connection_name()),
                    ("Reader role", EXPECTED_READER_ROLE),
                    ("Provider", run.get("provider")),
                    ("Execution state", run.get("state")),
                    ("Policy version", run.get("policy_version")),
                    ("Cortex session", flatten(session_id) if session_id else ""),
                    ("Query provenance", flatten(query_ids) if query_ids else ""),
                    ("Run created", str(run.get("created_at")) if run.get("created_at") else ""),
                )
            )
            + "</div>",
            unsafe_allow_html=True,
        )
        steps = trace_steps(trace)
        if steps:
            step_html = ""
            for index, step in enumerate(steps, start=1):
                name = first_key(step, STEP_NAME_KEYS)
                detail = first_key(step, STEP_DETAIL_KEYS)
                step_html += (
                    f'<div class="br-step"><span class="br-step__n">{index:02d}</span>'
                    f'<span><span class="br-step__t">{esc(flatten(name)) if name else "Unnamed stage"}</span>'
                    + (f'<span class="br-step__d">{esc(flatten(detail))}</span>' if detail else "")
                    + "</span></div>"
                )
            st.markdown(f'<div class="br-steps">{step_html}</div>', unsafe_allow_html=True)
        st.json(run.get("trace") if run.get("trace") not in (None, "") else {})


def render_product() -> None:
    """The authenticated product: one branded shell over four numbered stages."""
    connection_name = configured_connection_name()
    if not connection_name:
        st.error(
            "Authenticated mode is not configured. Set BIDPILOT_SNOWFLAKE_CONNECTION to a named "
            "Snowflake CLI connection."
        )
        return

    st.session_state.setdefault(STAGE_KEY, 0)
    st.session_state.setdefault(RUN_KEY, None)

    runs: list[dict] = []
    listing_error = ""
    with st.spinner("Loading opportunities from Snowflake…"):
        try:
            runs = load_persisted_runs(connection_name)
        except (SnowflakeBidRoomError, KeyError) as error:
            listing_error = str(error)

    complete = [
        run for run in runs if str(run.get("state")) == "COMPLETED" and run.get("is_complete")
    ]
    # One opportunity can carry several finished analyses. The latest is its
    # active one; the earlier ones stay reachable but do not compete with it.
    groups = group_by_opportunity(complete)
    known = {run["run_id"] for run in complete}
    selected_id = st.session_state.get(RUN_KEY)
    if selected_id not in known:
        selected_id = complete[0]["run_id"] if complete else None
        st.session_state[RUN_KEY] = selected_id
    selected_row = next((run for run in complete if run["run_id"] == selected_id), None)

    # The detail is loaded before the shell, so the sidebar can name the
    # opportunity and the supplier rather than repeat their identifiers.
    detail_error = ""
    view: dict | None = None
    if selected_id:
        with st.spinner("Loading the opportunity from Snowflake…"):
            try:
                result = load_persisted_run(connection_name, selected_id)
            except (SnowflakeBidRoomError, KeyError) as error:
                detail_error = str(error)
            else:
                view = build_run_view(
                    result, selected_id, str((selected_row or {}).get("opportunity_id") or "")
                )

    render_stage_navigation(
        not listing_error,
        opportunity=(
            view["headline"] if view else str((selected_row or {}).get("opportunity_id") or "")
        ),
        supplier=(
            (view or {}).get("supplier_name") or str((selected_row or {}).get("supplier_profile_id") or "")
        ),
    )

    if listing_error:
        # An authenticated failure stays an authenticated failure. No fixture
        # is ever shown in its place.
        st.error(listing_error)
        st.info(
            "Authenticated mode does not fall back to fixtures. Check that the connection is reachable "
            f"and that it uses the {EXPECTED_READER_ROLE} role, then reload."
        )
        return

    stage = current_stage()
    if stage == 0:
        if detail_error:
            st.error(detail_error)
        render_opportunities_screen(groups, runs, selected_row, view)
        return
    if selected_id is None:
        st.warning("No opportunity is selected yet. Open the Opportunities stage to choose one.")
        render_stage_footer(("Back to opportunities", 0), None)
        return
    if detail_error or view is None:
        st.error(detail_error or "This opportunity could not be loaded.")
        render_stage_footer(("Back to opportunities", 0), None)
        return

    if stage == 1:
        render_decision_screen(view)
    elif stage == 2:
        render_win_plan_screen(view)
    else:
        render_proposal_screen(view)


# ---------------------------------------------------------------------------
# Surface selection.
#
# With a configured Snowflake connection this is the public product: the
# authenticated four-stage Bid Room, entered directly, with no development
# workflow selector. Without one, the existing local development surfaces stay
# exactly as they were so the local tests and demos keep working. Authenticated
# mode never falls back to those fixtures.
# ---------------------------------------------------------------------------

if configured_connection_name():
    st.markdown(PRODUCT_STYLE, unsafe_allow_html=True)
    render_product()
    st.stop()

workflow = st.sidebar.radio(
    "Workflow",
    options=["Bid Room replay", "Tender intake", "Synthetic decision simulation"],
    label_visibility="collapsed",
)
st.markdown(LOCAL_STYLE, unsafe_allow_html=True)
if workflow == "Bid Room replay":
    render_bid_room()
    st.stop()
if workflow == "Tender intake":
    render_tender_intake()
    st.stop()

st.sidebar.markdown('<div class="bp-kicker">Opportunity queue</div>', unsafe_allow_html=True)
labels = {rfp["id"]: f"{rfp['id']} · {rfp['title']}" for rfp in RFPS}
selected_id = st.sidebar.radio("Select an RFP", options=list(labels), format_func=labels.get)
selected = next(rfp for rfp in RFPS if rfp["id"] == selected_id)
decision = evaluate_bid(selected, COMPANY)
signals = derive_signals(selected, COMPANY)

st.sidebar.markdown("---")
queue_rows = "".join(
    f'<div class="bp-gate-row" style="grid-template-columns:1fr auto;">'
    f'<span class="bp-gate-name">{rfp["id"]}</span>'
    f'<span class="bp-gate-flag {"pass" if verdict.can_proceed else "fail"}">{verdict.recommendation}</span>'
    f"</div>"
    for rfp, verdict in ((rfp, evaluate_bid(rfp, COMPANY)) for rfp in RFPS)
)
st.sidebar.markdown(f'<div class="bp-gate">{queue_rows}</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    '<p class="bp-note" style="margin-top:1rem;">Local demo mode · synthetic contest fixture. '
    "No customer data, no live warehouse session, and no persistent task store is active in this view.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Status rail + masthead
# ---------------------------------------------------------------------------

rail_items = [
    ("Policy floor", f"{COMPANY['minimum_margin_rate']:.0%} margin"),
    ("Bench capacity", f"{COMPANY['available_hours']:,} h"),
    ("Loaded rate", f"${COMPANY['loaded_hourly_cost']}/h"),
    ("Lead time", f"≥ {COMPANY['minimum_lead_days']} days"),
    ("Queue", f"{len(RFPS)} open RFPs"),
]
st.markdown(
    '<div class="bp-rail">'
    + "".join(
        f'<span class="bp-rail-item"><span class="bp-rail-key">{key}</span>'
        f'<span class="bp-rail-val">{value}</span></span>'
        for key, value in rail_items
    )
    + '<span class="bp-rail-mode">Local demo · synthetic fixture · no warehouse session</span>'
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="bp-mast">
      <div class="bp-mast-left">
        <div class="bp-kicker">Snowflake CoCo CLI Hackathon · decision-to-action workbench</div>
        <div class="bp-title">BidPilot</div>
        <div class="bp-lede">A bid decision is only useful when it protects capacity. BidPilot tests every
        opportunity against three non-negotiable gates, declines work that cannot succeed, and turns the
        viable one into owned proposal work with named owners and dates.</div>
      </div>
      <div class="bp-mast-right">
        <b>Three hard gates</b><br>Qualification · Capacity · Margin<br><br>
        Delivery risks stay visible.<br>They never overturn a failed gate.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Decision narrative (left) · scorecard and gate evidence (right)
# ---------------------------------------------------------------------------

left, right = st.columns([1.05, 1], gap="large")

with left:
    state_class = "is-bid" if decision.can_proceed else "is-nobid"
    tally = "".join(f'<span>{gate["name"].lower()} · {gate["flag"]}</span>' for gate in signals["gates"])
    headline = (
        "Gates cleared. Commit proposal capacity."
        if decision.can_proceed
        else "Gate failure. Decline and hold capacity."
    )
    st.markdown(
        f"""
        <div class="bp-decision {state_class}">
          <div class="bp-dec-top"><span>Recommendation</span><span>{selected['id']}</span></div>
          <div class="bp-dec-word">{decision.recommendation}</div>
          <div class="bp-dec-line">{headline}
            <span class="bp-dec-tally">{tally}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(section("01", "Why this is the recommendation"), unsafe_allow_html=True)
    st.markdown(
        "".join(f'<div class="bp-reason">{reason}</div>' for reason in decision.rationale),
        unsafe_allow_html=True,
    )

    st.markdown(
        section("02", "Decision trace", f"{signals['gates_passed']}/{signals['gate_total']} gates passed"),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<pre class="bp-trace">{build_trace(selected, signals["gates"], decision.recommendation)}</pre>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="bp-note" style="margin-top:.6rem;">Every line is fixed arithmetic over the fixture record. '
        "No model output, no score, no inferred customer data.</p>",
        unsafe_allow_html=True,
    )

with right:
    st.markdown(section("03", "Opportunity scorecard", selected["id"]), unsafe_allow_html=True)
    score_cells = [
        (
            "Contract value",
            f"${selected['contract_value']:,.0f}",
            f"{selected['required_hours']:,} h of delivery",
            "",
        ),
        (
            "Expected margin",
            f"${signals['expected_margin']:,.0f}",
            f"{signals['margin_rate']:.1%} vs {signals['margin_floor']:.0%} floor",
            " is-neg" if signals["margin_rate"] < signals["margin_floor"] else "",
        ),
        (
            "Capacity coverage",
            f"{signals['coverage']:.0%}",
            f"{signals['capacity_gap']:,} h short" if signals["capacity_gap"] else "fully covered",
            " is-neg" if signals["capacity_gap"] else "",
        ),
        (
            "Gates passed",
            f"{signals['gates_passed']}/{signals['gate_total']}",
            "hard, non-negotiable",
            " is-neg" if signals["gates_passed"] < signals["gate_total"] else "",
        ),
        (
            "Proposal window",
            f"{selected['deadline_days']} d",
            f"policy needs {COMPANY['minimum_lead_days']} d",
            " is-neg" if selected["deadline_days"] < COMPANY["minimum_lead_days"] else "",
        ),
        ("Open risks", f"{len(decision.risks)}", "visible, not blocking", ""),
    ]
    st.markdown(
        '<div class="bp-score">'
        + "".join(
            f'<div class="bp-score-cell"><div class="bp-score-k">{key}</div>'
            f'<div class="bp-score-v{cls}">{value}</div><div class="bp-score-s">{sub}</div></div>'
            for key, value, sub, cls in score_cells
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="bp-note" style="margin-top:.55rem;">{selected["summary"]}</p>',
        unsafe_allow_html=True,
    )

    st.markdown(section("04", "Gate-by-gate evidence"), unsafe_allow_html=True)
    gate_rows = "".join(
        f'<div class="bp-gate-row"><span class="bp-gate-name">{gate["name"]}</span>'
        f'<span class="bp-gate-test">{gate["test"]}</span>'
        f'<span class="bp-gate-flag {"pass" if gate["ok"] else "fail"}">{gate["flag"]}</span></div>'
        for gate in signals["gates"]
    )
    if decision.risks:
        risk_rows = "".join(
            f'<div class="bp-gate-row"><span class="bp-gate-name">Risk</span>'
            f'<span class="bp-gate-test">{risk}</span>'
            f'<span class="bp-gate-flag info">Visible</span></div>'
            for risk in decision.risks
        )
    else:
        risk_rows = (
            '<div class="bp-gate-row"><span class="bp-gate-name">Risk</span>'
            '<span class="bp-gate-test">0 open risks · nothing flagged by policy</span>'
            '<span class="bp-gate-flag info">None</span></div>'
        )
    st.markdown(f'<div class="bp-gate">{gate_rows}{risk_rows}</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="bp-note" style="margin-top:.55rem;">Qualification, capacity, and margin are hard gates. '
        "Risks are reported beside the decision and never overturn a failed gate.</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Decision → work transition
# ---------------------------------------------------------------------------

if not isinstance(st.session_state.get("tasks"), dict):
    st.session_state["tasks"] = {}
tasks_by_rfp = st.session_state["tasks"]

if decision.can_proceed:
    st.markdown(
        section("05", "Decision becomes owned work", "BID → proposal work plan"),
        unsafe_allow_html=True,
    )
    act, plan = st.columns([1, 1.85], gap="large")
    with act:
        st.markdown(
            f"""
            <div class="bp-handoff">
              <div class="bp-handoff-k">Handoff</div>
              <div class="bp-handoff-v">{selected['id']} → bid team</div>
              <div class="bp-handoff-p">Committing {selected['required_hours']:,} h of the
              {COMPANY['available_hours']:,} h bench at a {signals['margin_rate']:.1%} expected margin,
              with {selected['deadline_days']} days to the proposal date.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Create internal proposal work plan", type="primary"):
            tasks_by_rfp[selected_id] = create_proposal_tasks(selected, decision)
    with plan:
        tasks = tasks_by_rfp.get(selected_id)
        if tasks:
            rows = "".join(
                work_row(
                    f"{index:02d}",
                    task["task"],
                    task.get("outcome", ""),
                    task["owner"]
                    + (f" · {task['workstream']}" if task.get("workstream") else ""),
                    f"D+{task['due_in_days']}",
                )
                for index, task in enumerate(tasks, start=1)
            )
            st.markdown(f'<div class="bp-work">{rows}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="bp-note" style="margin-top:.6rem;"><b>{len(tasks)} tasks</b> created for '
                f"{selected_id} and held in this browser session. Nothing is submitted externally, and "
                "Snowflake-backed task state is not connected in this local demo.</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="bp-work-empty">No work plan yet for this opportunity. Creating the plan '
                "assigns bounded tasks with named owners and due dates derived from the proposal window.</div>",
                unsafe_allow_html=True,
            )
else:
    st.markdown(
        section("05", "Capacity preserved", "NO-BID → next viable opportunity"),
        unsafe_allow_html=True,
    )
    held, nxt = st.columns([1, 1.85], gap="large")
    with held:
        st.markdown(
            f"""
            <div class="bp-handoff">
              <div class="bp-handoff-k">Protected this cycle</div>
              <div class="bp-handoff-v">{COMPANY['available_hours']:,} h held</div>
              <div class="bp-handoff-p">{selected['id']} would have consumed
              {selected['required_hours']:,} h at a {signals['margin_rate']:.1%} margin.
              No proposal tasks are created behind a failed gate.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nxt:
        next_viable = next(
            (
                rfp
                for rfp in RFPS
                if rfp["id"] != selected_id and evaluate_bid(rfp, COMPANY).can_proceed
            ),
            None,
        )
        if next_viable is None:
            st.markdown(
                '<div class="bp-work-empty">No other opportunity in the queue clears all three gates. '
                "The bench stays uncommitted until one does.</div>",
                unsafe_allow_html=True,
            )
        else:
            next_signals = derive_signals(next_viable, COMPANY)
            row = work_row(
                "→",
                f"{next_viable['id']} · {next_viable['title']}",
                "Select it in the queue to create its proposal work plan.",
                f"{next_signals['margin_rate']:.1%} margin · {next_viable['required_hours']:,} h",
                f"{next_signals['gates_passed']}/{next_signals['gate_total']} gates",
            )
            st.markdown(f'<div class="bp-work">{row}</div>', unsafe_allow_html=True)

st.markdown(
    '<p class="bp-foot"><b>Local simulation mode.</b> Every number on this screen is computed in-process from a '
    "synthetic contest fixture. No customer data, no live Snowflake session, and no persistent task store is "
    "connected in this view. With BIDPILOT_SNOWFLAKE_CONNECTION configured the app opens the authenticated "
    "Bid Room over the verified Snowpark and Cortex Code run instead. This simulation remains only as a "
    "transparent policy comparison surface.</p>",
    unsafe_allow_html=True,
)
