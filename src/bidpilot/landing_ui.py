"""Public landing page in the SEAL landing grammar, filled with BidPilot's record.

Cinematic black hero with drifting glows, a live pipeline, then white story
bands, a dark proof band and a closing call to action. No script: the page is
rendered through Streamlit markdown, so every motion is CSS only and every
number comes from the recorded run or the reviewed public notice.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from bidpilot.ui_components import esc
from bidpilot.workspace_ui import catalog_date, deadline_state

API_URL = "https://bidpilot-api-164282963747.us-central1.run.app"
REPO_URL = "https://github.com/sergiobuilds/bidpilot"
RUN_ID = "cortex-final-20260802-a"

PIPELINE = (
    ("Tender", "public score sheet"),
    ("Evidence", "supplier record"),
    ("Decision", "evidence gate"),
    ("Win Position", "weighted"),
    ("Proposal", "red-teamed"),
    ("Snowflake", "one run id"),
)


def _reviewed(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    for row in rows:
        if row.get("evidence_level") == "source-reviewed":
            return row
    return None


def _pipeline() -> str:
    parts: list[str] = []
    for index, (label, sub) in enumerate(PIPELINE):
        if index:
            parts.append('<div class="plink"><i class="spark"></i></div>')
        parts.append(
            '<div class="pnode"><div class="ring"></div>'
            f'<div class="lab">{esc(label)}</div></div>'
        )
    return '<div class="pipe">' + "".join(parts) + "</div>"


def landing_page(rows: Sequence[Mapping[str, object]], *, now: datetime) -> str:
    """Return the whole landing page as trusted markup."""
    row = _reviewed(rows)
    notice = esc(row.get("notice_number")) if row else "R26BK01680611-000"
    title = esc(row.get("title")) if row else ""
    issuer = esc(row.get("issuer")) if row else ""
    due = catalog_date(row.get("deadline")) if row else ""
    state = deadline_state(row.get("deadline"), now) if row else None
    due_word = "closes" if state == "open" else "closed"
    open_count = sum(deadline_state(r.get("deadline"), now) == "open" for r in rows)

    return (
        '<div id="bp-land" class="bp-land">'
        # nav
        '<nav class="nav" aria-label="BidPilot">'
        '<a class="brand" href="?"><span class="mk">B</span><span class="wordmark">BidPilot</span></a>'
        '<div class="links"><a href="#problem">Problem</a><a href="#how">How it works</a>'
        '<a href="#proof">Proof</a><a href="#agents">Agents</a></div><div class="sp"></div>'
        '<div class="nav-cta"><a class="btn btn-md btn-ghost" href="?walkthrough=1">Completed run</a>'
        '<a class="btn btn-md btn-primary" href="?view=opportunities">Open the workspace</a></div></nav>'
        # hero
        '<header class="cine" id="top"><div class="glow g1"></div><div class="glow g2"></div>'
        '<div class="wrap cine-inner">'
        '<h1 class="reveal"><span class="ln">Decide the bid</span>'
        '<span class="ln">before anyone</span><span class="ln"><span class="shine">writes it.</span></span></h1>'
        '<p class="lead reveal">Evidence first. Then the bid.</p>'
        '<div class="cine-cta reveal"><a class="btn btn-lg btn-primary" href="?view=opportunities">Open the workspace</a>'
        f'<a class="btn btn-lg btn-outline" href="?tender={notice}">See the live decision</a></div>'
        + '</div><div class="scrollcue"><div class="mouse"></div>Scroll</div></header>'
        # story
        '<div class="sheet">'
        '<section class="band" id="problem"><div class="wrap">'
        '<h2 class="sec-h">Bids are lost before they are written.</h2>'
        "</div></section>"
        '<section class="band alt" id="how"><div class="wrap">'
        '<h2 class="sec-h">Read. Gate. Record.</h2>'
        '<div class="cards">'
        '<div class="card"><h3>Read</h3><p>The tender\'s own weights.</p></div>'
        '<div class="card"><h3>Gate</h3><p>No evidence, no proposal.</p></div>'
        '<div class="card"><h3>Record</h3><p>One Snowflake run id.</p></div>'
        "</div></div></section>"
        # proof (dark)
        '<section class="dark" id="proof"><div class="wrap"><div class="split">'
        '<div><p class="quote">One run id. <span class="accent">The whole chain.</span></p>'
        f'<p class="dsub"><code>{RUN_ID}</code></p>'
        '<div class="chips"><span class="chip on">1 decision</span><span class="chip on">3 strategies</span>'
        '<span class="chip on">4 weighted plans</span><span class="chip on">8 proposal sections</span>'
        '<span class="chip on">12 owned tasks</span></div>'
        '<div class="cine-cta"><a class="btn btn-lg btn-outline" href="?walkthrough=1">Open the completed run</a></div></div>'
        '<article class="sheetcard" aria-label="Live public notice">'
        f'<header><span>{notice}</span><span class="state">{esc(row.get("status")) if row else "REVIEW"}</span></header>'
        f'<h3>{title}</h3><p class="who">{issuer}</p>'
        '<div class="bar"><i style="flex:90"></i><i class="p" style="flex:10"></i></div>'
        '<div class="legend"><span>Technical <b>90</b></span><span>Price <b>10</b></span></div>'
        f"<dl><div><dt>Evidence gaps</dt><dd>4 of 4</dd></div><div><dt>Deadline</dt><dd>{esc(due_word)} {esc(due)}</dd></div>"
        "<div><dt>Proposal</dt><dd>Locked until evidenced</dd></div></dl>"
        f'<a class="btn btn-md btn-primary" href="?tender={notice}">Run the decision live</a></article>'
        "</div></div></section>"
        # agents
        '<section class="band alt" id="agents"><div class="wrap">'
        '<h2 class="sec-h">Not a dashboard.</h2>'
        '<div class="chips">'
        f'<a class="chip on" href="{REPO_URL}/tree/main/skills/bidpilot" target="_blank" rel="noreferrer">Cortex Code skill</a>'
        f'<a class="chip on" href="{API_URL}/mcp" target="_blank" rel="noreferrer">Remote MCP</a>'
        f'<a class="chip on" href="{API_URL}/openapi.json" target="_blank" rel="noreferrer">OpenAPI</a>'
        f'<a class="chip" href="{REPO_URL}/tree/main/integrations" target="_blank" rel="noreferrer">Claude Code · Cursor · Gemini</a>'
        "</div></div></section>"
        # foot cta
        '<section class="footcta band alt"><div class="wrap">'
        '<h2>Decide the bid <span class="accent">before anyone writes it.</span></h2>'
        '<div class="cine-cta"><a class="btn btn-lg btn-primary" href="?view=opportunities">Open the workspace</a>'
        '<a class="btn btn-lg btn-outline light" href="?walkthrough=1">Completed run</a></div>'
        "</div></section>"
        '<footer><div class="wrap frow"><a class="brand" href="?"><span class="mk">B</span><b>BidPilot</b></a>'
        f'<div class="sp"></div><span class="muted">Evidence-first B2G pursuit · <a href="{REPO_URL}">source</a></span></div></footer>'
        "</div></div>"
    )


def landing_css() -> str:
    """CSS for the landing, adapted from the SEAL landing with WDS tokens inlined."""
    return """<style>
@import url("https://static.wanted.co.kr/fonts/wantedsans/WantedSansVariable.min.css");
html,body,.stApp,[data-testid="stAppViewContainer"],section.stMain,[data-testid="stMain"]{height:auto!important;min-height:100vh!important;overflow:visible!important}body{overflow-x:hidden!important}[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stAppToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],[data-testid="stSkeleton"],.stSkeleton{display:none!important}.stMainBlockContainer,.block-container{max-width:none!important;padding:0!important}
.bp-land{--pri:#0066FF;--pri-strong:#005EEB;--b55:#1A75FF;--b60:#3385FF;--b65:#4F95FF;--b70:#69A5FF;--b95:#EAF2FE;--cn7:#141415;--cn10:#171719;--label:#171719;--label-strong:#000;--label-neutral:rgba(46,47,51,.88);--label-alt:rgba(55,56,60,.61);--line:rgba(112,115,124,.22);--line-neutral:rgba(112,115,124,.16);--line-alt:rgba(112,115,124,.08);--fill:rgba(112,115,124,.08);--fill-alt:rgba(112,115,124,.05);--bg-alt:#F7F7F8;font-family:"Wanted Sans Variable","Wanted Sans",-apple-system,BlinkMacSystemFont,system-ui,"Noto Sans KR",sans-serif;color:var(--label);background:#000;-webkit-font-smoothing:antialiased;line-height:1.5;letter-spacing:-.01em}
.bp-land,.bp-land *{box-sizing:border-box}.bp-land a{text-decoration:none;color:inherit}.bp-land h1,.bp-land h2,.bp-land h3,.bp-land p{margin:0;padding:0}.bp-land .accent{color:var(--pri)}.bp-land .wrap{max-width:1120px;margin:0 auto;padding:0 32px}
.bp-land .nav{position:sticky;top:0;z-index:60;height:68px;display:flex;align-items:center;gap:28px;padding:0 32px;background:rgba(5,7,13,.72);backdrop-filter:blur(18px);border-bottom:1px solid rgba(255,255,255,.08)}.bp-land .nav .brand{display:flex;align-items:center;gap:9px;font-weight:800;font-size:21px;letter-spacing:-.03em;color:#fff}.bp-land .mk{width:30px;height:30px;border-radius:9px;background:var(--pri);display:grid;place-items:center;color:#fff;font-weight:800;box-shadow:0 3px 14px -2px rgba(0,102,255,.8)}.bp-land .wordmark{font-weight:800;letter-spacing:-.04em;transform:skewX(-8deg);display:inline-block;padding-right:3px;line-height:1;background:linear-gradient(100deg,#0066FF 8%,#4F95FF 50%,#0066FF 92%);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;animation:bp-shine 5.5s linear infinite}.bp-land .nav .links{display:flex;gap:4px;margin-left:14px}.bp-land .nav .links a{font-size:14.5px;font-weight:600;color:rgba(255,255,255,.7);padding:8px 13px;border-radius:8px;white-space:nowrap}.bp-land .nav .links a:hover{background:rgba(255,255,255,.1);color:#fff}.bp-land .sp{flex:1}.bp-land .nav-cta{display:flex;align-items:center;gap:10px}
.bp-land .btn{display:inline-flex;align-items:center;gap:7px;font-weight:700;border:none;white-space:nowrap;border-radius:12px;transition:background .15s,color .2s}.bp-land .btn-primary{background:var(--pri);color:#fff}.bp-land .btn-primary:hover{background:var(--pri-strong)}.bp-land .btn-ghost{background:transparent;color:rgba(255,255,255,.85)}.bp-land .btn-ghost:hover{background:rgba(255,255,255,.1)}.bp-land .btn-lg{height:54px;padding:0 28px;font-size:17px;border-radius:14px}.bp-land .btn-md{height:42px;padding:0 18px;font-size:15px}.bp-land .btn-outline{background:rgba(255,255,255,.06);color:#fff;box-shadow:inset 0 0 0 1px rgba(255,255,255,.22)}.bp-land .btn-outline:hover{background:rgba(255,255,255,.12)}.bp-land .btn-outline.light{background:#fff;color:var(--label);box-shadow:inset 0 0 0 1px var(--line)}.bp-land .btn-outline.light:hover{background:var(--fill-alt)}
.bp-land .cine{position:relative;min-height:calc(100vh - 68px);overflow:hidden;background:#05070d;display:flex;flex-direction:column;justify-content:center;padding:96px 0 120px}.bp-land .glow{position:absolute;border-radius:50%;filter:blur(40px);pointer-events:none}.bp-land .g1{width:760px;height:760px;top:-260px;right:-160px;background:radial-gradient(circle,rgba(0,102,255,.42),rgba(0,102,255,0) 62%);animation:bp-drift1 22s ease-in-out infinite}.bp-land .g2{width:620px;height:620px;bottom:-240px;left:-180px;background:radial-gradient(circle,rgba(0,84,209,.34),rgba(0,84,209,0) 64%);animation:bp-drift2 26s ease-in-out infinite}@keyframes bp-drift1{0%,100%{transform:translate(0,0)}50%{transform:translate(-70px,60px)}}@keyframes bp-drift2{0%,100%{transform:translate(0,0)}50%{transform:translate(80px,-50px)}}
.bp-land .cine-inner{position:relative;z-index:2}.bp-land .kick{font-size:13.5px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--b65)}.bp-land .cine h1{font-size:clamp(40px,6.6vw,84px);font-weight:800;line-height:1.2;letter-spacing:-.04em;margin:26px 0 0;color:#fff}.bp-land .cine h1 .ln{display:block;white-space:nowrap;transform:skewX(-8deg);transform-origin:left center;padding-right:4px}.bp-land .shine{background:linear-gradient(100deg,#3385FF 10%,#9EC5FF 45%,#3385FF 80%);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;animation:bp-shine 5.5s linear infinite}@keyframes bp-shine{from{background-position:200% 0}to{background-position:-20% 0}}.bp-land .lead{font-size:clamp(18px,2.2vw,23px);color:rgba(255,255,255,.72);font-weight:500;margin:28px 0 0;max-width:34ch}.bp-land .cine-cta{display:flex;gap:12px;margin-top:38px;flex-wrap:wrap}.bp-land .cine .note,.bp-land .footcta .note{margin-top:16px;font-size:13.5px;color:rgba(255,255,255,.45);font-weight:500}.bp-land .footcta .note{color:var(--label-alt)}
.bp-land .pipe{position:relative;z-index:2;margin-top:64px;display:flex;align-items:center;gap:0}.bp-land .pnode{position:relative;flex-shrink:0;display:flex;flex-direction:column;align-items:center;gap:10px;width:116px;text-align:center}.bp-land .pnode .ring{width:60px;height:60px;border-radius:17px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.14);animation:bp-nodepulse 5.2s ease-in-out infinite}.bp-land .pnode .lab{font-size:14px;font-weight:700;color:rgba(255,255,255,.78)}.bp-land .pnode .sub{font-size:11.5px;font-weight:500;color:rgba(255,255,255,.4);margin-top:-4px}.bp-land .pnode:nth-child(1) .ring{animation-delay:0s}.bp-land .pnode:nth-child(3) .ring{animation-delay:.87s}.bp-land .pnode:nth-child(5) .ring{animation-delay:1.73s}.bp-land .pnode:nth-child(7) .ring{animation-delay:2.6s}.bp-land .pnode:nth-child(9) .ring{animation-delay:3.47s}.bp-land .pnode:nth-child(11) .ring{animation-delay:4.33s}@keyframes bp-nodepulse{0%,18%,100%{border-color:rgba(255,255,255,.14);box-shadow:none;background:rgba(255,255,255,.04)}7%{border-color:var(--b60);box-shadow:0 0 0 4px rgba(0,102,255,.22),0 0 26px rgba(0,102,255,.55);background:rgba(0,102,255,.18)}}.bp-land .plink{flex:1;height:2px;position:relative;background:rgba(255,255,255,.12);margin:0 -6px;overflow:hidden;min-width:28px}.bp-land .plink .spark{position:absolute;top:0;left:0;height:100%;width:38%;background:linear-gradient(90deg,transparent,var(--b55),transparent);animation:bp-travel 5.2s linear infinite}.bp-land .plink:nth-child(2) .spark{animation-delay:0s}.bp-land .plink:nth-child(4) .spark{animation-delay:.87s}.bp-land .plink:nth-child(6) .spark{animation-delay:1.73s}.bp-land .plink:nth-child(8) .spark{animation-delay:2.6s}.bp-land .plink:nth-child(10) .spark{animation-delay:3.47s}@keyframes bp-travel{0%{transform:translateX(-120%)}22%,100%{transform:translateX(360%)}}
.bp-land .scrollcue{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);z-index:2;color:rgba(255,255,255,.5);font-size:12px;font-weight:700;letter-spacing:.08em;text-align:center;display:flex;flex-direction:column;align-items:center;gap:8px}.bp-land .scrollcue .mouse{width:22px;height:34px;border:2px solid rgba(255,255,255,.35);border-radius:12px;position:relative}.bp-land .scrollcue .mouse::after{content:"";position:absolute;top:6px;left:50%;width:3px;height:6px;border-radius:2px;background:rgba(255,255,255,.6);transform:translateX(-50%);animation:bp-wheel 1.6s ease-in-out infinite}@keyframes bp-wheel{0%{opacity:0;transform:translate(-50%,0)}40%{opacity:1}100%{opacity:0;transform:translate(-50%,12px)}}
.bp-land .sheet{background:#fff;position:relative;z-index:3}.bp-land section.band{padding:104px 0}.bp-land .band.alt{background:var(--bg-alt);border-top:1px solid var(--line-alt);border-bottom:1px solid var(--line-alt)}.bp-land .sec-kick{font-size:13px;font-weight:800;color:var(--pri);letter-spacing:.04em;text-transform:uppercase}.bp-land .sec-h{font-size:clamp(28px,4.2vw,46px);font-weight:800;line-height:1.18;letter-spacing:-.035em;margin:16px 0 0;color:var(--label-strong);text-wrap:balance}.bp-land .sec-h b{color:var(--pri)}.bp-land .sec-sub{font-size:17px;color:var(--label-alt);font-weight:500;margin:18px 0 0;max-width:52ch;line-height:1.65}
.bp-land .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:48px}.bp-land .card{background:#fff;border:1px solid var(--line-neutral);border-radius:18px;padding:28px 26px}.bp-land .card .ic{width:48px;height:48px;border-radius:13px;background:var(--b95);color:var(--pri);display:grid;place-items:center;margin-bottom:18px;font-weight:800}.bp-land .card .step{font-size:12px;font-weight:800;color:var(--pri);letter-spacing:.05em}.bp-land .card h3{font-size:20px;font-weight:800;letter-spacing:-.02em;margin:7px 0 0;color:var(--label-strong)}.bp-land .card p{font-size:14.5px;color:var(--label-alt);font-weight:500;margin:10px 0 0;line-height:1.6}
.bp-land .chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:30px}.bp-land .chip{display:inline-flex;align-items:center;background:var(--fill);color:var(--label-neutral);font-weight:600;font-size:14.5px;padding:10px 16px;border-radius:999px;white-space:nowrap;min-height:44px}.bp-land .chip.on{background:var(--b95);color:var(--pri-strong)}
.bp-land .dark{background:var(--cn7);color:#fff;padding:110px 0}.bp-land .dark .sec-kick{color:var(--b60)}.bp-land .dark .quote{font-size:clamp(28px,4.4vw,50px);font-weight:800;line-height:1.28;letter-spacing:-.035em;margin:18px 0 0;max-width:18ch;text-wrap:balance}.bp-land .dark .quote .accent{color:var(--b60)}.bp-land .dark .dsub{font-size:17px;color:rgba(255,255,255,.66);font-weight:500;margin:26px 0 0;max-width:50ch;line-height:1.65}.bp-land .dark code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em;color:var(--b70)}.bp-land .dark .chip{background:rgba(255,255,255,.08);color:rgba(255,255,255,.92)}.bp-land .dark .chip.on{background:rgba(0,102,255,.22);color:var(--b70)}.bp-land .split{display:grid;grid-template-columns:1.1fr .9fr;gap:56px;align-items:center}
.bp-land .sheetcard{background:#fff;color:var(--label);border-radius:20px;padding:26px 28px 24px;box-shadow:0 30px 60px -30px rgba(0,0,0,.7)}.bp-land .sheetcard header{display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:13px;color:var(--label-alt)}.bp-land .sheetcard .state{display:inline-flex;align-items:center;height:26px;padding:0 10px;border-radius:999px;background:#FEF4E6;color:#D17600;font-weight:700;font-size:12px}.bp-land .sheetcard h3{margin-top:12px;font-size:19px;line-height:1.35;letter-spacing:-.01em;color:var(--label-strong)}.bp-land .sheetcard .who{margin-top:4px;font-size:14px;color:var(--label-alt)}.bp-land .sheetcard .bar{display:flex;height:32px;border-radius:8px;overflow:hidden;background:var(--fill-alt);margin-top:22px}.bp-land .sheetcard .bar i{display:block;height:100%;background:linear-gradient(90deg,#0054D1,#0066FF);transform-origin:left;animation:bp-fill .9s cubic-bezier(.4,0,.2,1) both}.bp-land .sheetcard .bar i.p{background:#9EC5FF}@keyframes bp-fill{from{transform:scaleX(0)}to{transform:scaleX(1)}}.bp-land .sheetcard .legend{display:flex;justify-content:space-between;margin-top:8px;font-size:13px;color:var(--label-alt)}.bp-land .sheetcard .legend b{color:var(--label);font-size:16px;margin-left:4px}.bp-land .sheetcard dl{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:22px 0 0;padding-top:18px;border-top:1px solid var(--line-alt)}.bp-land .sheetcard dt{font-size:12px;color:var(--label-alt)}.bp-land .sheetcard dd{margin:4px 0 0;font-size:15px;font-weight:600;line-height:1.3}.bp-land .sheetcard .btn{margin-top:22px}
.bp-land .footcta{text-align:center;padding:116px 0}.bp-land .footcta h2{font-size:clamp(30px,4.4vw,52px);font-weight:800;letter-spacing:-.035em;line-height:1.2;color:var(--label-strong);text-wrap:balance}.bp-land .footcta .cine-cta{justify-content:center}.bp-land footer{border-top:1px solid var(--line-alt);padding:40px 0;background:#fff}.bp-land footer .frow{display:flex;align-items:center;gap:16px;flex-wrap:wrap}.bp-land footer .muted{font-size:13.5px;color:var(--label-alt);font-weight:500}.bp-land footer .muted a{color:var(--pri);font-weight:600}.bp-land footer .brand{display:flex;align-items:center;gap:9px;font-weight:800;font-size:18px;letter-spacing:-.03em}.bp-land footer .brand .mk{width:26px;height:26px;border-radius:8px;box-shadow:none}.bp-land footer .brand b{color:var(--pri)}
.bp-land .reveal{animation:bp-rise .7s cubic-bezier(.2,.8,.2,1) both}.bp-land h1.reveal{animation-delay:.08s}.bp-land .lead.reveal{animation-delay:.16s}.bp-land .cine-cta.reveal{animation-delay:.24s}.bp-land .note.reveal{animation-delay:.3s}@keyframes bp-rise{from{transform:translateY(24px);opacity:0}to{transform:none;opacity:1}}
.bp-land a:focus-visible{outline:2px solid var(--b60);outline-offset:3px}
@media (max-width: 860px){.bp-land .nav{padding:0 18px;gap:14px}.bp-land .nav .links{display:none}.bp-land .nav .btn-ghost{display:none}.bp-land .wrap{padding:0 18px}.bp-land .cards{grid-template-columns:1fr}.bp-land .split{grid-template-columns:1fr;gap:28px}.bp-land .pipe{flex-wrap:wrap;justify-content:center;gap:10px}.bp-land .pipe .plink{display:none}.bp-land .pnode{width:96px}.bp-land .cine{padding:72px 0 80px}.bp-land section.band{padding:72px 0}.bp-land .dark{padding:80px 0}.bp-land .sheetcard{padding:20px 18px}.bp-land .sheetcard dl{grid-template-columns:1fr 1fr}.bp-land .cine h1 .ln{white-space:normal}}
@media (prefers-reduced-motion: reduce){.bp-land .g1,.bp-land .g2,.bp-land .shine,.bp-land .wordmark,.bp-land .ring,.bp-land .spark,.bp-land .scrollcue .mouse::after,.bp-land .reveal,.bp-land .sheetcard .bar i{animation:none!important}}
</style>"""
