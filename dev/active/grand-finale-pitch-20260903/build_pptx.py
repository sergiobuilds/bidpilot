from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "deck.pptx"
RENDERED = ROOT / "rendered"

SLIDES = [
    (
        "BidPilot · AI Pursuit Decision Support for Public Tenders",
        "Public tender plus company evidence | PURSUE, REVIEW or NO-GO | "
        "KRW 250M | Technical 90 | Price 10 | Would you bid?",
    ),
    (
        "The Missing Answer · REVIEW",
        "Four unsupported supplier requirements | Real public tender | "
        "Synthetic demo supplier profile",
    ),
    (
        "Sergio Lee · CPA · Builder · CFO",
        "Washington State CPA | Government-support program specialist | "
        "Five-time hackathon winner including OpenAI Hackathon second prize | "
        "Maintainer of the 5.6K-star Ouroboros open-source Agent OS | "
        "CFO of Daedal Games, an AI game-harness technology company | BidPilot",
    ),
    (
        "Accounting-Firm + Enterprise Friction · 6 Breakpoints",
        "Opportunity | Eligibility | Evidence | Score | Strategy | Ownership | "
        "Fixed submission deadline",
    ),
    (
        "Global Public-Sector Pursuit · Shared Operating Pattern",
        "Korea G2B | US SAM.gov | EU TED | OECD public procurement | "
        "One shared operating pattern",
    ),
    (
        "Verification · Context · Strategy",
        "Source, eligibility and evidence | Credentials, people, availability and "
        "delivery history | Weights, position and owner | PURSUE, REVIEW or NO-GO",
    ),
    (
        "Fluency Is Not Evidence",
        "A proposal can sound excellent and still be indefensible",
    ),
    (
        "Should We Bid? · Who Owns What Next?",
        "Tender | Decision | Win Position | Proposal | Owner | "
        "Same run ID persisted and replayable in Snowflake",
    ),
    (
        "Public Tender + Supplier Evidence · Controlled Decision",
        "Real public tender | Synthetic demo supplier profile | Policy gate | "
        "Separate historical replay | No silent fixture fallback",
    ),
    (
        "Two Evidence Paths · REVIEW / PURSUE",
        "Real Suwon G2B source: REVIEW, four evidence gaps, no run | "
        "Separate synthetic replay: PURSUE, 40/30/20/10, three compared and one selected",
    ),
    (
        "40 Points · Changes the Plan",
        "Four weighted plans | Selected Win Position | Evidence | Eight proposal "
        "sections | Red-team | Twelve named tasks",
    ),
    (
        "Snowflake · Memory That Survives the Meeting",
        "Governed join | Least privilege | Durable state | Opportunity Graph | "
        "Snowpark policy | Streamlit reader | Same-run readback | Fail closed",
    ),
    (
        "CoCo CLI · Work That Survives the Prompt",
        "Query | Compare | Select | Write | Challenge | Persist | "
        "Cortex session and Snowflake query provenance",
    ),
    (
        "Verified Run · 1 → 3 → 4 → 8 → 12",
        "One decision | Three strategies | Four weighted plans | Eight sections | "
        "Twelve tasks | Internal work ready | Human approval | Legal submission",
    ),
    (
        "Win the score, not the prompt.",
        "Defensible decision | Weighted strategy | Owned execution | "
        "Persisted and replayable in Snowflake",
    ),
]


def add_hidden_editable_text(slide, title: str, body: str) -> None:
    """Keep the core wording editable behind the visual fidelity layer."""
    box = slide.shapes.add_textbox(Inches(0.4), Inches(0.4), Inches(12.5), Inches(6.7))
    box.name = f"Editable core text | {title}"
    frame = box.text_frame
    frame.clear()
    p = frame.paragraphs[0]
    run = p.add_run()
    run.text = title
    run.font.name = "Aptos Display"
    run.font.size = Pt(28)
    run.font.bold = True
    p = frame.add_paragraph()
    p.text = body
    p.font.name = "Aptos"
    p.font.size = Pt(18)


def build() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    prs.core_properties.title = "BidPilot · Snowflake CoCo CLI Hackathon 2026 Grand Finale"
    prs.core_properties.subject = "Fifteen-slide English finale deck"
    prs.core_properties.author = "Sergio Lee"

    for number, (title, body) in enumerate(SLIDES, start=1):
        image = RENDERED / f"slide-{number:02d}.png"
        if not image.exists():
            raise FileNotFoundError(image)
        slide = prs.slides.add_slide(blank)
        add_hidden_editable_text(slide, title, body)
        picture = slide.shapes.add_picture(
            str(image), 0, 0, width=prs.slide_width, height=prs.slide_height
        )
        picture.name = f"Rendered visual layer | slide {number:02d}"

    prs.save(OUT)
    print(f"wrote {OUT} with {len(prs.slides)} slides")


if __name__ == "__main__":
    build()
