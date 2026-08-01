"""BidPilot's judge-facing decision-to-action workbench."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

import streamlit as st

from bidpilot.bid_room import BidRoomStore
from bidpilot.engine import create_proposal_tasks, evaluate_bid
from bidpilot.fixtures import COMPANY, RFPS, SUPPLIER_PROFILES, TENDERS
from bidpilot.intake import TenderIntakeError, build_pursuit_tender, intake_tender_bytes, intake_tender_url
from bidpilot.proposal_writer import red_team_proposal, red_team_tasks, write_strategy_proposal
from bidpilot.pursuit import build_pursuit_brief, select_win_position
from bidpilot.snowflake_store import SnowflakeBidRoomError, SnowflakeBidRoomStore, configured_connection_name

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
# Authenticated Bid Room stylesheet.
#
# Values are the resolved light-mode Seed tokens pinned by .design-system
# (carrot brand, gray neutrals, green/yellow/red status). Seed's own family is
# the platform stack, so this sheet loads no font, image or script from the
# network. Every table collapses into labelled cards below 720px, which is what
# keeps 390px free of horizontal overflow.
# ---------------------------------------------------------------------------

AUTHENTICATED_STYLE = """
    <style>
      :root {
        --sx-gray-00:#fff; --sx-gray-100:#f7f8f9; --sx-gray-200:#f3f4f5; --sx-gray-300:#eeeff1;
        --sx-gray-400:#dcdee3; --sx-gray-700:#868b94; --sx-gray-800:#555d6d; --sx-gray-900:#2a3038;
        --sx-gray-1000:#1a1c20;
        --sx-carrot-100:#fff2ec; --sx-carrot-300:#ffd5c0; --sx-carrot-400:#ffb999;
        --sx-carrot-600:#f60; --sx-carrot-700:#e14d00; --sx-carrot-800:#b93901;
        --sx-green-100:#edfaf6; --sx-green-400:#7ddcb3; --sx-green-700:#079171; --sx-green-900:#075445;
        --sx-yellow-100:#fff7de; --sx-yellow-300:#fbdc65; --sx-yellow-900:#4f3e1f;
        --sx-red-100:#fdf0f0; --sx-red-400:#feb7b3; --sx-red-700:#fa342c; --sx-red-900:#921708;
        --sx-focus:#5e98fe;
        --sx-line:#00000010; --sx-line-strong:#dcdee3;
        --sx-white-a300:#ffffff2e; --sx-white-a700:#ffffffb3;
        --sx-x1:4px; --sx-x2:8px; --sx-x3:12px; --sx-x4:16px; --sx-x5:20px; --sx-x6:24px; --sx-x8:32px;
        --sx-r2:8px; --sx-r3:12px; --sx-r4:16px; --sx-full:9999px;
        --sx-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
      }
      .stApp { background: var(--sx-gray-200); color: var(--sx-gray-1000); }
      .block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1320px; }
      .stApp, .stApp p, .stApp li, .stApp label, .stApp div {
        font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Segoe UI", Roboto,
          "Helvetica Neue", Arial, "Noto Sans", sans-serif; }
      .sx-num { font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
      .sx-mono { font-family: var(--sx-mono); overflow-wrap: anywhere; }

      /* run strip -------------------------------------------------------- */
      .sx-strip { display: flex; flex-wrap: wrap; gap: var(--sx-x3) var(--sx-x6);
        align-items: baseline; padding: var(--sx-x3) var(--sx-x4); margin-bottom: var(--sx-x4);
        background: var(--sx-gray-00); border-radius: var(--sx-r3);
        box-shadow: inset 0 0 0 1px var(--sx-line); }
      .sx-strip__i { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
      .sx-strip__k { font-size: 11px; line-height: 15px; letter-spacing: .1em; text-transform: uppercase;
        font-weight: 700; color: var(--sx-gray-800); }
      .sx-strip__v { font-size: 13px; line-height: 18px; color: var(--sx-gray-1000); overflow-wrap: anywhere; }
      .sx-strip__live { margin-left: auto; display: inline-flex; align-items: center; gap: var(--sx-x2);
        padding: 4px 10px; border-radius: var(--sx-full); background: var(--sx-green-100);
        color: var(--sx-green-900); font-size: 12px; line-height: 16px; font-weight: 700; white-space: nowrap; }
      .sx-strip__dot { width: 7px; height: 7px; border-radius: var(--sx-full); background: var(--sx-green-700); }

      /* masthead --------------------------------------------------------- */
      .sx-mast { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: var(--sx-x6);
        align-items: start; padding: var(--sx-x6); border-radius: var(--sx-r4);
        background: var(--sx-gray-900); color: #fff; border-bottom: 4px solid var(--sx-carrot-600); }
      .sx-kicker { display: flex; flex-wrap: wrap; gap: var(--sx-x2) var(--sx-x3); font-size: 11px;
        line-height: 15px; letter-spacing: .12em; text-transform: uppercase; font-weight: 700;
        color: var(--sx-carrot-400); }
      .sx-mast__title { font-size: 26px; line-height: 35px; font-weight: 700; letter-spacing: -.025em;
        margin: var(--sx-x3) 0 0; overflow-wrap: anywhere; }
      .sx-mast__sub { margin-top: var(--sx-x2); max-width: 62ch; font-size: 14px; line-height: 22px;
        color: var(--sx-white-a700); }
      .sx-magic { display: flex; flex-wrap: wrap; align-items: stretch; gap: var(--sx-x2);
        margin-top: var(--sx-x4); }
      .sx-magic__item { min-width: 150px; padding: var(--sx-x2) var(--sx-x3); border-radius: var(--sx-r2);
        background: var(--sx-white-a300); box-shadow: inset 0 0 0 1px #ffffff24; }
      .sx-magic__k { display: block; font-size: 10px; line-height: 14px; letter-spacing: .1em;
        text-transform: uppercase; font-weight: 700; color: var(--sx-carrot-400); }
      .sx-magic__v { display: block; margin-top: 2px; font-size: 13px; line-height: 18px;
        font-weight: 700; color: #fff; }
      .sx-magic__cta { display: inline-flex; align-items: center; justify-content: center; min-height: 42px;
        padding: 0 var(--sx-x4); border-radius: var(--sx-r2); background: var(--sx-carrot-600);
        color: #fff !important; text-decoration: none !important; font-size: 13px; font-weight: 700; }
      .sx-magic__cta:hover, .sx-magic__cta:focus { background: var(--sx-carrot-700); }
      .sx-magic__cta:focus-visible { outline: 3px solid var(--sx-focus); outline-offset: 2px; }
      .sx-verdict { display: grid; gap: 6px; justify-items: end; text-align: right; }
      .sx-verdict__k { font-size: 11px; line-height: 15px; letter-spacing: .12em; text-transform: uppercase;
        font-weight: 700; color: var(--sx-white-a700); }
      .sx-verdict__v { font-size: 24px; line-height: 32px; font-weight: 700; letter-spacing: -.02em; }
      .sx-verdict__v[data-tone="positive"] { color: var(--sx-green-400); }
      .sx-verdict__v[data-tone="warning"] { color: var(--sx-carrot-400); }
      .sx-verdict__v[data-tone="critical"] { color: var(--sx-red-400); }
      .sx-verdict__v[data-tone="neutral"] { color: #fff; }
      .sx-verdict__n { font-size: 12px; line-height: 16px; color: var(--sx-white-a700); overflow-wrap: anywhere; }
      @media (max-width: 860px) {
        .sx-mast { grid-template-columns: minmax(0,1fr); }
        .sx-verdict { justify-items: start; text-align: left; }
      }
      @media (max-width: 720px) {
        .sx-strip__i:nth-child(2), .sx-strip__i:nth-child(3), .sx-strip__i:nth-child(4) { display: none; }
        .sx-strip__live { margin-left: 0; }
        .sx-mast { padding: var(--sx-x5); gap: var(--sx-x4); }
        .sx-mast__title { font-size: 23px; line-height: 30px; }
        .sx-magic { display: grid; grid-template-columns: 1fr 1fr; }
        .sx-magic__item { min-width: 0; }
        .sx-magic__cta { grid-column: 1 / -1; }
      }

      /* cards ------------------------------------------------------------ */
      .sx-card { background: var(--sx-gray-00); border-radius: var(--sx-r4); margin-top: var(--sx-x6);
        box-shadow: inset 0 0 0 1px var(--sx-line); overflow: hidden; }
      .sx-card__head { display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--sx-x3);
        padding: var(--sx-x5) var(--sx-x5) var(--sx-x4); }
      .sx-step { font-size: 11px; line-height: 15px; font-weight: 700; letter-spacing: .14em;
        color: var(--sx-carrot-800); }
      .sx-card__title { font-size: 18px; line-height: 24px; font-weight: 700; letter-spacing: -.015em;
        margin: 0 auto 0 0; }
      .sx-card__note { font-size: 13px; line-height: 18px; color: var(--sx-gray-800); }
      .sx-card__body { padding: 0 var(--sx-x5) var(--sx-x5); }

      /* decision facts --------------------------------------------------- */
      .sx-facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--sx-x3); }
      .sx-fact { padding: var(--sx-x3) var(--sx-x4); border-radius: var(--sx-r2); background: var(--sx-gray-100); }
      .sx-fact__k { font-size: 11px; line-height: 15px; letter-spacing: .08em; text-transform: uppercase;
        font-weight: 700; color: var(--sx-gray-800); }
      .sx-fact__v { margin-top: 4px; font-size: 14px; line-height: 19px; color: var(--sx-gray-1000);
        overflow-wrap: anywhere; }
      .sx-fact__v[data-tone="critical"] { color: var(--sx-red-900); font-weight: 700; }
      .sx-fact__v[data-tone="positive"] { color: var(--sx-green-900); font-weight: 700; }
      /* Missing-evidence labels stay at gray-800 (6.62:1). gray-700 is 3.42:1
         on white and fails AA, so italics carry the distinction instead. */
      .sx-fact__v[data-missing="true"] { color: var(--sx-gray-800); font-style: italic; }

      /* coverage bar ----------------------------------------------------- */
      .sx-cover { display: flex; gap: 2px; height: var(--sx-x2); margin: 0 var(--sx-x5) var(--sx-x3);
        border-radius: var(--sx-full); overflow: hidden; background: var(--sx-gray-300); }
      .sx-cover__seg[data-tone="evidenced"] { background: var(--sx-green-700); }
      .sx-cover__seg[data-tone="open"] { background: var(--sx-gray-400); }
      .sx-legend { display: flex; flex-wrap: wrap; gap: var(--sx-x2) var(--sx-x5);
        margin: 0 var(--sx-x5) var(--sx-x4); font-size: 12px; line-height: 16px; color: var(--sx-gray-800); }
      .sx-legend span { display: inline-flex; align-items: center; gap: 6px; }
      .sx-legend i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
      .sx-legend i[data-tone="evidenced"] { background: var(--sx-green-700); }
      .sx-legend i[data-tone="open"] { background: var(--sx-gray-400); }

      /* tables ----------------------------------------------------------- */
      .sx-tablewrap { padding: 0 var(--sx-x3) var(--sx-x2); }
      table.sx-table { width: 100%; border-collapse: collapse; table-layout: fixed;
        font-size: 13px; line-height: 18px; }
      .sx-table th { text-align: left; padding: var(--sx-x2) var(--sx-x3); font-size: 11px; line-height: 15px;
        letter-spacing: .08em; text-transform: uppercase; font-weight: 700; color: var(--sx-gray-800);
        border-bottom: 1px solid var(--sx-line-strong); }
      .sx-table td { padding: var(--sx-x3); border-bottom: 1px solid var(--sx-line);
        color: var(--sx-gray-800); vertical-align: top; overflow-wrap: anywhere; }
      .sx-table tbody tr:last-child td { border-bottom: 0; }
      .sx-table tbody tr[data-tone="open"] { background: var(--sx-carrot-100); }
      .sx-crit { font-size: 14px; line-height: 19px; font-weight: 700; color: var(--sx-gray-1000); }
      .sx-owner { display: block; margin-top: 2px; font-size: 12px; line-height: 16px; color: var(--sx-gray-800); }
      .sx-weight { display: flex; align-items: center; gap: var(--sx-x2); }
      .sx-weight__track { flex: 1; min-width: 32px; height: 6px; border-radius: var(--sx-full);
        background: var(--sx-gray-300); overflow: hidden; }
      .sx-weight__fill { display: block; height: 100%; background: var(--sx-carrot-600); border-radius: var(--sx-full); }
      .sx-weight__n { font-size: 18px; line-height: 24px; font-weight: 700; letter-spacing: -.02em;
        color: var(--sx-gray-1000); }
      .sx-mark { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; line-height: 16px;
        font-weight: 700; padding: 3px 9px; border-radius: var(--sx-full); white-space: nowrap; }
      .sx-mark[data-tone="evidenced"] { background: var(--sx-green-100); color: var(--sx-green-900); }
      .sx-mark[data-tone="open"] { background: var(--sx-carrot-100); color: var(--sx-carrot-800); }
      .sx-mark[data-tone="neutral"] { background: var(--sx-gray-200); color: var(--sx-gray-800); }
      .sx-asset { display: block; }
      .sx-asset + .sx-asset { margin-top: 4px; }
      .sx-missing { color: var(--sx-gray-800); font-style: italic; }

      @media (max-width: 720px) {
        .sx-tablewrap { padding: 0 var(--sx-x4) var(--sx-x2); }
        .sx-table, .sx-table caption, .sx-table tbody, .sx-table tr, .sx-table td { display: block; width: 100%; }
        .sx-table colgroup, .sx-table col { display: none; }
        .sx-table thead { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
        .sx-table tbody tr { border: 1px solid var(--sx-line-strong); border-radius: var(--sx-r3);
          padding: var(--sx-x4); margin-bottom: var(--sx-x3); }
        .sx-table td { border-bottom: 0; padding: 0; }
        .sx-table td + td { margin-top: var(--sx-x3); }
        .sx-table td[data-label]::before { content: attr(data-label); display: block; margin-bottom: 4px;
          font-size: 11px; line-height: 15px; letter-spacing: .08em; text-transform: uppercase;
          font-weight: 700; color: var(--sx-gray-800); }
      }

      /* win position ----------------------------------------------------- */
      .sx-pos { padding: var(--sx-x5); border-radius: var(--sx-r3); background: var(--sx-carrot-100);
        box-shadow: inset 0 0 0 2px var(--sx-carrot-300); }
      .sx-pos__title { font-size: 16px; line-height: 22px; font-weight: 700; color: var(--sx-gray-1000); }
      .sx-pos__statement { margin-top: var(--sx-x2); font-size: 14px; line-height: 22px; color: var(--sx-gray-800); }
      .sx-proofs { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: var(--sx-x3); margin-top: var(--sx-x4); }
      .sx-proof { padding: var(--sx-x3); border-radius: var(--sx-r2); background: var(--sx-gray-00); }
      .sx-proof__kind { font-size: 11px; line-height: 15px; letter-spacing: .06em; text-transform: uppercase;
        font-weight: 700; color: var(--sx-carrot-800); }
      .sx-proof__label { margin-top: 2px; font-size: 13px; line-height: 18px; font-weight: 700; }
      .sx-proof__detail { margin-top: 2px; font-size: 12px; line-height: 18px; color: var(--sx-gray-800); }
      .sx-risk { margin-top: var(--sx-x4); padding-top: var(--sx-x3); border-top: 1px solid var(--sx-line);
        font-size: 13px; line-height: 19px; color: var(--sx-gray-800); }
      .sx-risk b { color: var(--sx-gray-1000); }
      .sx-alts { display: grid; gap: var(--sx-x2); margin-top: var(--sx-x4); }
      .sx-alt { padding: var(--sx-x3) var(--sx-x4); border-radius: var(--sx-r2); background: var(--sx-gray-100);
        font-size: 13px; line-height: 19px; color: var(--sx-gray-800); }
      .sx-alt b { color: var(--sx-gray-1000); }

      /* stage trace ------------------------------------------------------ */
      .sx-steps { display: grid; gap: var(--sx-x2); }
      .sx-stepline { display: grid; grid-template-columns: 26px minmax(0,1fr); gap: var(--sx-x3);
        align-items: start; padding: var(--sx-x3); border-radius: var(--sx-r2); background: var(--sx-gray-100); }
      .sx-stepline__n { font-size: 12px; line-height: 18px; font-weight: 700; color: var(--sx-carrot-800); }
      .sx-stepline__t { font-size: 13px; line-height: 18px; font-weight: 700; color: var(--sx-gray-1000); }
      .sx-stepline__d { margin-top: 2px; font-size: 12px; line-height: 18px; color: var(--sx-gray-800);
        font-family: var(--sx-mono); overflow-wrap: anywhere; }
      .sx-empty { padding: var(--sx-x4); border-radius: var(--sx-r2); background: var(--sx-gray-100);
        font-size: 13px; line-height: 19px; color: var(--sx-gray-800); }
      .sx-foot { margin-top: var(--sx-x6); font-size: 12px; line-height: 18px; color: var(--sx-gray-800); }

      /* streamlit chrome ------------------------------------------------- */
      .stApp h1, .stApp h2, .stApp h3 { letter-spacing: -.02em; }
      .stButton button, .stDownloadButton button { border-radius: var(--sx-r2); border: 0;
        background: var(--sx-carrot-600); color: #fff; font-weight: 700; font-size: 14px; min-height: 40px; }
      .stButton button:hover, .stDownloadButton button:hover { background: var(--sx-carrot-700); color: #fff; }
      .stButton button:focus-visible, .stDownloadButton button:focus-visible {
        outline: 3px solid var(--sx-focus); outline-offset: 2px; }
      .stTextArea textarea { font-family: var(--sx-mono); font-size: 13px; line-height: 20px;
        border-radius: var(--sx-r2); }
      section[data-testid="stSidebar"] { background: var(--sx-gray-00); border-right: 1px solid var(--sx-line-strong); }
      div[data-baseweb="select"] > div { border-radius: var(--sx-r2); }
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
        result = store.latest(tender["id"], supplier["id"], opportunity_version, position.statement)
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
    st.markdown('<p class="bp-foot"><b>Demo boundary.</b> This workflow intentionally uses synthetic replay fixtures and local SQLite. Choose Authenticated Snowflake Bid Room to inspect the verified complete run.</p>', unsafe_allow_html=True)


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
    tags = tuple(tag.strip() for tag in st.text_input("Scope tags", "public-data, data-quality").split(",") if tag.strip())
    hours = st.number_input("Estimated delivery hours", min_value=1, value=720)
    outcome = st.text_input("Promised buyer outcome", "A measurable service handoff")
    if st.button("Open reviewed Bid Room", type="primary"):
        try:
            st.session_state["intake_tender"] = build_pursuit_tender(
                snapshot,
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

NOT_RECORDED = "Not recorded in this run"

TRACE_TITLE_KEYS = ("opportunity_title", "tender_title", "title")
TRACE_OBJECTIVE_KEYS = ("buyer_objective", "objective", "summary")
TRACE_SESSION_KEYS = ("session_id", "snowflake_session_id", "session")
TRACE_QUERY_KEYS = ("query_id", "query_ids", "last_query_id", "queries")
TRACE_STEP_KEYS = ("steps", "stages", "events", "trace")
STEP_NAME_KEYS = ("step", "name", "stage", "action", "operation")
STEP_DETAIL_KEYS = ("sql", "object", "output", "result", "input", "status", "error")
ASSET_NAME_KEYS = ("label", "title", "name", "asset", "project_title")

STATUS_TONES = {"PURSUE": "positive", "REVIEW": "warning", "NO-GO": "critical", "NO_GO": "critical"}


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


def sx_card(step: str, title: str, note: str, body: str, bare: str = "") -> str:
    return (
        f'<section class="sx-card"><div class="sx-card__head"><span class="sx-step">{esc(step)}</span>'
        f'<h2 class="sx-card__title">{esc(title)}</h2>'
        f'<p class="sx-card__note">{esc(note)}</p></div>{bare}'
        f'<div class="sx-card__body">{body}</div></section>'
    )


def sx_fact(key: str, value: str | None, tone: str = "") -> str:
    missing = "true" if not value else "false"
    shown = value or NOT_RECORDED
    return (
        f'<div class="sx-fact"><p class="sx-fact__k">{esc(key)}</p>'
        f'<p class="sx-fact__v" data-tone="{tone}" data-missing="{missing}">{esc(shown)}</p></div>'
    )


def render_snowflake_bid_room() -> None:
    """Render one persisted Snowflake run: verdict, score map, sections, work, provenance."""
    connection_name = configured_connection_name()
    if not connection_name:
        st.error("Authenticated mode is not configured. Set BIDPILOT_SNOWFLAKE_CONNECTION to a named Snowflake CLI connection.")
        return

    try:
        store = SnowflakeBidRoomStore(connection_name)
        all_runs = store.list_runs()
        runs = [run for run in all_runs if run["state"] == "COMPLETED" and run["is_complete"]]
        if not runs:
            st.warning("No completed run currently contains a decision, strategy, proposal sections, and owned tasks under one run ID.")
            if all_runs:
                st.dataframe(all_runs, hide_index=True, width="stretch")
            return
        selected_id = st.sidebar.selectbox("Persisted run", [run["run_id"] for run in runs])
        result = store.load_run(selected_id)
    except (SnowflakeBidRoomError, KeyError) as error:
        st.error(str(error))
        return

    run = result["run"]
    opportunity = result.get("opportunity") or {}
    supplier = result.get("supplier") or {}
    trace = run.get("trace") if isinstance(run.get("trace"), dict) else {}
    decision = result["decision"] or {}
    strategies = result["strategies"] or []
    selected = next((item for item in strategies if item.get("selected")), strategies[0] if strategies else {})
    blueprint = result["blueprint"] or []
    lead_plan = max(blueprint, key=lambda item: as_number(item.get("weight")) or 0, default={})
    status = str(decision.get("status") or first_key(trace, ("pursuit_status", "status")) or "RECORDED")
    tone = STATUS_TONES.get(status.upper(), "neutral")

    # 00 · run strip. Provider, state and policy version come from AGENT_RUNS,
    # never from the locally imported policy constant.
    strip_items = [
        ("Run ID", selected_id),
        ("Provider", run.get("provider")),
        ("Execution state", run.get("state")),
        ("Policy version", run.get("policy_version")),
        ("Supplier", supplier.get("supplier_name") or run.get("supplier_profile_id")),
    ]
    st.markdown(
        '<div class="sx-strip">'
        + "".join(
            f'<span class="sx-strip__i"><span class="sx-strip__k">{esc(key)}</span>'
            f'<span class="sx-strip__v sx-mono">{esc(value) if value not in (None, "") else NOT_RECORDED}</span></span>'
            for key, value in strip_items
        )
        + f'<span class="sx-strip__live"><span class="sx-strip__dot"></span>'
        f"Snowflake connection {esc(connection_name)}</span></div>",
        unsafe_allow_html=True,
    )

    # 00 · masthead. The tender headline is only shown when the run itself
    # carries it; otherwise the opportunity identifier is the headline.
    headline = opportunity.get("title") or first_key(trace, TRACE_TITLE_KEYS) or run.get("opportunity_id") or selected_id
    objective = opportunity.get("buyer_objective") or first_key(trace, TRACE_OBJECTIVE_KEYS)
    lead_label = lead_plan.get("criterion_name") or NOT_RECORDED
    lead_weight = as_number(lead_plan.get("weight"))
    lead_value = f"{trim(lead_weight)} points · {lead_label}" if lead_weight is not None else lead_label
    position_value = selected.get("title") or NOT_RECORDED
    st.markdown(
        f'<section class="sx-mast"><div><p class="sx-kicker"><span>Authenticated Bid Room</span>'
        f'<span>Opportunity {esc(run.get("opportunity_id") or NOT_RECORDED)}</span></p>'
        f'<h1 class="sx-mast__title">{esc(headline)}</h1>'
        f'<p class="sx-mast__sub">{esc(objective) if objective else "Buyer objective is not carried in this run record."}</p>'
        f'<div class="sx-magic"><span class="sx-magic__item"><span class="sx-magic__k">Lead score target</span>'
        f'<span class="sx-magic__v">{esc(lead_value)}</span></span>'
        f'<span class="sx-magic__item"><span class="sx-magic__k">Selected Win Position</span>'
        f'<span class="sx-magic__v">{esc(position_value)}</span></span>'
        f'<a class="sx-magic__cta" href="#proposal-draft">Open proposal from selected strategy</a></div></div>'
        f'<div class="sx-verdict"><p class="sx-verdict__k">Pursuit decision</p>'
        f'<p class="sx-verdict__v" data-tone="{tone}">{esc(status)}</p>'
        f'<p class="sx-verdict__n sx-mono">Opportunity version {esc(run.get("opportunity_version") or NOT_RECORDED)}</p></div></section>',
        unsafe_allow_html=True,
    )

    # 01 · what the verdict rests on.
    missing = [record_label(item) for item in as_records(decision.get("missing_eligibility"))]
    gap_hours = as_number(decision.get("capacity_gap_hours"))
    st.markdown(
        sx_card(
            "01",
            "Why the run reached this decision",
            "PURSUIT_DECISIONS, one row per run",
            '<div class="sx-facts">'
            + sx_fact("Decision", status, tone)
            + sx_fact(
                "Missing eligibility",
                ", ".join(missing) if missing else ("None recorded" if decision else None),
                "critical" if missing else "positive" if decision else "",
            )
            + sx_fact(
                "Capacity gap",
                None if gap_hours is None else (f"{trim(gap_hours)} h short" if gap_hours > 0 else "No shortfall recorded"),
                "critical" if gap_hours else "positive" if gap_hours == 0 else "",
            )
            + "</div>",
        ),
        unsafe_allow_html=True,
    )

    # 02 · the score map. Criterion weight, the supplier asset the run attached
    # to it, and the claim the proposal will make for those points.
    rows: list[dict] = []
    total_weight = 0.0
    evidenced_weight = 0.0
    for item in blueprint:
        weight = as_number(item.get("weight")) or 0.0
        assets = [record_label(asset) for asset in as_records(item.get("assets"))]
        total_weight += weight
        if assets:
            evidenced_weight += weight
        rows.append({"item": item, "weight": weight, "assets": assets})
    # Bars are scaled against the full weighted total, so a 40-point criterion
    # reads as 40% of the score and not as a full bar.

    if rows:
        open_weight = total_weight - evidenced_weight
        cover_bar = (
            '<div class="sx-cover" role="img" aria-label="'
            f'{esc(trim(evidenced_weight))} of {esc(trim(total_weight))} weighted points have a supplier asset recorded">'
            f'<span class="sx-cover__seg" data-tone="evidenced" style="flex:{evidenced_weight or 0}"></span>'
            f'<span class="sx-cover__seg" data-tone="open" style="flex:{open_weight or 0}"></span></div>'
            '<div class="sx-legend"><span><i data-tone="evidenced"></i>'
            f"Evidence recorded · {esc(trim(evidenced_weight))} pts</span>"
            '<span><i data-tone="open"></i>'
            f"No asset recorded · {esc(trim(open_weight))} pts</span></div>"
        )
        body_rows = ""
        for row in rows:
            item, weight, assets = row["item"], row["weight"], row["assets"]
            evidenced = bool(assets)
            fill = (weight / total_weight * 100) if total_weight else 0
            asset_html = (
                "".join(f'<span class="sx-asset">{esc(asset)}</span>' for asset in assets)
                if evidenced
                else f'<span class="sx-missing">{NOT_RECORDED}</span>'
            )
            body_rows += (
                f'<tr data-tone="{"evidenced" if evidenced else "open"}">'
                f'<td data-label="Criterion"><span class="sx-crit">{esc(item.get("criterion_name") or NOT_RECORDED)}</span>'
                f'<span class="sx-owner">Owner · {esc(item.get("owner") or NOT_RECORDED)}</span></td>'
                f'<td data-label="Weight"><span class="sx-weight"><span class="sx-weight__track">'
                f'<span class="sx-weight__fill" style="width:{fill:.0f}%"></span></span>'
                f'<span class="sx-weight__n sx-num">{esc(trim(weight))}</span></span></td>'
                f'<td data-label="Evidence"><span class="sx-mark" data-tone="{"evidenced" if evidenced else "open"}">'
                f'{"Asset recorded" if evidenced else "No asset"}</span></td>'
                f'<td data-label="Supplier asset">{asset_html}</td>'
                f'<td data-label="Planned claim">{esc(item.get("claim") or NOT_RECORDED)}</td></tr>'
            )
        table = (
            '<div class="sx-tablewrap"><table class="sx-table">'
            "<caption class=\"sx-missing\" style=\"text-align:left;padding:0 12px 8px;font-style:normal\">"
            "Evidence is derived in this view from RUBRIC_RESPONSE_PLANS.assets: a criterion counts as "
            "evidenced when the run recorded at least one supplier asset against it.</caption>"
            '<colgroup><col style="width:24%"><col style="width:15%"><col style="width:13%">'
            '<col style="width:22%"><col style="width:26%"></colgroup>'
            "<thead><tr><th scope=\"col\">Criterion</th><th scope=\"col\">Weight</th>"
            "<th scope=\"col\">Evidence</th><th scope=\"col\">Supplier asset</th>"
            "<th scope=\"col\">Planned claim</th></tr></thead>"
            f"<tbody>{body_rows}</tbody></table></div>"
        )
        st.markdown(
            sx_card(
                "02",
                "Official weighted evaluation score map",
                f"{trim(evidenced_weight)} of {trim(total_weight)} weighted points carry a recorded supplier asset",
                "",
                cover_bar + table,
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            sx_card(
                "02",
                "Official weighted evaluation score map",
                "RUBRIC_RESPONSE_PLANS",
                '<div class="sx-empty">No weighted response plan rows are stored under this run ID.</div>',
            ),
            unsafe_allow_html=True,
        )

    # 03 · the strategy those claims are bound to.
    if selected:
        proofs = as_records(selected.get("proof_cards"))
        proof_html = "".join(
            '<div class="sx-proof">'
            f'<p class="sx-proof__kind">{esc(card.get("kind")) if isinstance(card, dict) and card.get("kind") else "Proof"}</p>'
            f'<p class="sx-proof__label">{esc(record_label(card))}</p>'
            + (
                f'<p class="sx-proof__detail">{esc(card["detail"])}</p>'
                if isinstance(card, dict) and card.get("detail")
                else ""
            )
            + "</div>"
            for card in proofs
        )
        weakness = selected.get("weakness")
        mitigation = selected.get("mitigation")
        risk = (
            f'<p class="sx-risk"><b>Recorded weakness.</b> {esc(weakness)}'
            + (f" <b>Mitigation.</b> {esc(mitigation)}" if mitigation else "")
            + "</p>"
            if weakness
            else ""
        )
        alternates = "".join(
            f'<div class="sx-alt"><b>{esc(item.get("title") or NOT_RECORDED)}</b> — '
            f'{esc(item.get("statement") or NOT_RECORDED)}</div>'
            for item in strategies
            if item is not selected
        )
        st.markdown(
            sx_card(
                "03",
                "Selected Win Position",
                "WIN_STRATEGIES, selected row of this run",
                '<div class="sx-pos">'
                f'<p class="sx-pos__title">{esc(selected.get("title") or NOT_RECORDED)}</p>'
                f'<p class="sx-pos__statement">{esc(selected.get("statement") or NOT_RECORDED)}</p>'
                + (f'<div class="sx-proofs">{proof_html}</div>' if proof_html else "")
                + risk
                + "</div>"
                + (
                    '<p class="sx-card__note" style="margin-top:16px">Positions the run considered and did not select</p>'
                    f'<div class="sx-alts">{alternates}</div>'
                    if alternates
                    else ""
                ),
            ),
            unsafe_allow_html=True,
        )

    # 04 · evidence-safe proposal sections, editable and downloadable.
    st.markdown(
        sx_card(
            "04",
            "Proposal sections",
            "PROPOSAL_SECTIONS, one section per score-bearing criterion",
            '<div class="sx-empty">Edit below. The download always reflects the edited text.</div>'
            if result["sections"]
            else '<div class="sx-empty">This run is incomplete: no proposal section is persisted under this run ID.</div>',
        ),
        unsafe_allow_html=True,
    )
    if result["sections"]:
        st.markdown('<span id="proposal-draft"></span>', unsafe_allow_html=True)
        draft = "\n\n".join(str(item.get("section_markdown") or "") for item in result["sections"])
        edited = st.text_area(
            "Proposal draft",
            draft,
            height=440,
            key=f"authenticated-draft::{selected_id}",
            help="Sections are loaded from this run. Edits stay in this session and are not written back to Snowflake.",
        )
        st.download_button(
            "Download proposal draft",
            edited,
            file_name=f"{selected_id}.md",
            mime="text/markdown",
        )

    # 05 · the owned work that closes the remaining gaps.
    tasks = result["tasks"] or []
    if tasks:
        task_rows = "".join(
            f'<tr><td data-label="Task"><span class="sx-crit">{esc(task.get("task_name") or NOT_RECORDED)}</span></td>'
            f'<td data-label="Owner">{esc(task.get("owner") or NOT_RECORDED)}</td>'
            f'<td data-label="Status"><span class="sx-mark" data-tone="neutral">'
            f'{esc(task.get("status") or NOT_RECORDED)}</span></td></tr>'
            for task in tasks
        )
        task_html = (
            '<div class="sx-tablewrap" style="padding-inline:0"><table class="sx-table">'
            '<caption class="sx-missing" style="text-align:left;padding:0 12px 8px;font-style:normal">'
            "Every task below is stored under the same run ID as the decision and the sections.</caption>"
            '<colgroup><col style="width:52%"><col style="width:28%"><col style="width:20%"></colgroup>'
            '<thead><tr><th scope="col">Task</th><th scope="col">Owner</th><th scope="col">Status</th></tr></thead>'
            f"<tbody>{task_rows}</tbody></table></div>"
        )
    else:
        task_html = '<div class="sx-empty">No pursuit task is persisted under this run ID.</div>'
    st.markdown(
        sx_card("05", "Owned pursuit work", f"PURSUIT_TASKS · {len(tasks)} rows", task_html),
        unsafe_allow_html=True,
    )

    # 06 · provenance. Compact by default, full trace behind the expander.
    provenance = trace.get("execution_provenance") if isinstance(trace.get("execution_provenance"), dict) else {}
    session_id = first_key(provenance, ("cortex_session_id", "session_id")) or first_key(trace, TRACE_SESSION_KEYS)
    query_ids = (
        first_key(provenance, ("cortex_write_query_ids", "query_ids"))
        or first_key(trace, TRACE_QUERY_KEYS)
    )
    st.markdown(
        sx_card(
            "06",
            "Execution provenance",
            "AGENT_RUNS.trace",
            '<div class="sx-facts">'
            + sx_fact("Provider", run.get("provider"))
            + sx_fact("Execution state", run.get("state"))
            + sx_fact("Cortex session", flatten(session_id) if session_id else None)
            + sx_fact("Query provenance", flatten(query_ids) if query_ids else None)
            + sx_fact("Run created", str(run.get("created_at")) if run.get("created_at") else None)
            + "</div>",
        ),
        unsafe_allow_html=True,
    )
    steps = trace_steps(trace)
    if steps:
        step_html = ""
        for index, step in enumerate(steps, start=1):
            name = first_key(step, STEP_NAME_KEYS)
            detail = first_key(step, STEP_DETAIL_KEYS)
            step_html += (
                f'<div class="sx-stepline"><span class="sx-stepline__n sx-num">{index:02d}</span>'
                f'<span><span class="sx-stepline__t">{esc(flatten(name)) if name else "Unnamed stage"}</span>'
                + (f'<span class="sx-stepline__d">{esc(flatten(detail))}</span>' if detail else "")
                + "</span></div>"
            )
        st.markdown(f'<div class="sx-steps" style="margin-top:16px">{step_html}</div>', unsafe_allow_html=True)
    with st.expander("Full run trace as stored in AGENT_RUNS"):
        st.json(run.get("trace") if run.get("trace") not in (None, "") else {})
    st.markdown(
        '<p class="sx-foot">Every value on this screen is a field of this run ID in Snowflake. '
        "Fields the run did not record are labelled rather than filled in.</p>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

workflow_options = ["Bid Room replay", "Tender intake", "Synthetic decision simulation"]
if configured_connection_name():
    workflow_options.insert(0, "Authenticated Snowflake Bid Room")
workflow = st.sidebar.radio(
    "Workflow",
    options=workflow_options,
    label_visibility="collapsed",
)
st.markdown(
    AUTHENTICATED_STYLE if workflow == "Authenticated Snowflake Bid Room" else LOCAL_STYLE,
    unsafe_allow_html=True,
)
if workflow == "Authenticated Snowflake Bid Room":
    render_snowflake_bid_room()
    st.stop()
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
    "connected in this view. The separate Authenticated Snowflake Bid Room reloads the verified Snowpark and "
    "Cortex Code run. This simulation remains only as a transparent policy comparison surface.</p>",
    unsafe_allow_html=True,
)
