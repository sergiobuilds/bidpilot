"""Safe tender URL and PDF intake for the BidPilot opportunity graph."""

from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from html import unescape
from io import BytesIO
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pypdf import PdfReader

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
_INSTRUCTION_PATTERNS = (
    r"ignore (all )?previous instructions",
    r"system message",
    r"you are chatgpt",
    r"disregard .* instructions",
)


class TenderIntakeError(ValueError):
    """Raised when an untrusted tender input cannot enter the product."""


class _PublicRedirectHandler(HTTPRedirectHandler):
    """Reject redirects before urllib connects to a non-public destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _is_public_url(newurl):
            raise TenderIntakeError("Tender URL redirected to a non-public host.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass(frozen=True)
class TenderSnapshot:
    source_url: str | None
    sha256: str
    retrieved_at: str
    content_type: str
    text: str
    has_instruction_like_content: bool
    tender: dict


def _is_public_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            return False
    return True


def _normalize_text(raw: str) -> str:
    text = unescape(re.sub(r"<[^>]+>", "\n", raw))
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines() if line.strip())


def _extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as error:  # pypdf uses several exception classes for malformed files.
        raise TenderIntakeError("The uploaded PDF could not be read as a tender document.") from error


def _parse_lines(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise TenderIntakeError("Tender content is empty.")
    criteria: list[dict] = []
    eligibility: list[str] = []
    submissions: list[str] = []
    scope = ""
    buyer_objective = ""
    for line in lines:
        lower = line.lower()
        match = re.search(r"(.+?)[\-:：]\s*(\d+)\s*(?:points?|점)", line, flags=re.IGNORECASE)
        if match and any(token in lower for token in ("technical", "delivery", "team", "price", "평가", "가격")):
            criteria.append({"name": match.group(1).strip(" -:："), "weight": int(match.group(2))})
        if any(token in lower for token in ("eligibility", "qualification", "자격", "등록", "certificate", "sme")):
            eligibility.append(re.sub(r"^(eligibility|qualification|자격)\s*[:：-]\s*", "", line, flags=re.IGNORECASE))
        if any(token in lower for token in ("submission", "submit", "제출", "proposal")):
            submissions.append(line)
        if not scope and any(token in lower for token in ("scope", "service", "과업", "용역")):
            scope = line
        if not buyer_objective and any(token in lower for token in ("objective", "purpose", "목적")):
            buyer_objective = line
    # Parenthetical percentages are normally subcriteria of the score that
    # precedes the parentheses.  The current score-map contract is flat, so
    # keep only the top-level weights instead of double-counting parent and
    # child values (for example 90 + 20 + 70 + 10).
    top_level_text = re.sub(r"\([^()]*\)", "", text)
    known_criteria = {item["name"].casefold() for item in criteria}
    for name, weight in re.findall(r"((?:기술능력|입찰가격|정량적|정성적)\s*평가)\s*(\d+(?:\.\d+)?)\s*%", top_level_text):
        normalized_name = re.sub(r"\s+", " ", name).strip()
        if normalized_name.casefold() not in known_criteria:
            criteria.append({"name": normalized_name, "weight": float(weight) if "." in weight else int(weight)})
            known_criteria.add(normalized_name.casefold())
    # English-language tenders often publish a comma-separated percentage
    # matrix instead of using "points".  Parse each clause independently so a
    # heading such as "Evaluation criteria" cannot become part of the name.
    for clause in re.split(r"[,;\n]", top_level_text):
        match = re.search(r"([A-Za-z][A-Za-z0-9 /&_-]{1,80}?)\s*(\d+(?:\.\d+)?)\s*%", clause)
        if not match:
            continue
        name = re.sub(r"^(?:evaluation|scoring)(?:\s+(?:criteria|weights?))?\s*[:\-]?\s*", "", match.group(1), flags=re.IGNORECASE).strip(" -:：")
        if not name or name.casefold() in known_criteria:
            continue
        criteria.append({"name": name, "weight": float(match.group(2)) if "." in match.group(2) else int(match.group(2))})
        known_criteria.add(name.casefold())
    return {
        "title": lines[0],
        "scope": scope or "Scope requires review from the source document.",
        "buyer_objective": buyer_objective or "Buyer objective requires review from the source document.",
        "eligibility_requirements": tuple(eligibility),
        "evaluation_criteria": tuple(criteria),
        "submission_items": tuple(submissions),
    }


def review_tender_snapshot(
    snapshot: TenderSnapshot,
    *,
    scope: str,
    buyer_objective: str,
    eligibility_requirements: tuple[str, ...],
    evaluation_criteria: tuple[dict, ...],
) -> TenderSnapshot:
    """Return an operator-reviewed snapshot after validating its score map."""
    cleaned_scope = scope.strip()
    cleaned_objective = buyer_objective.strip()
    if not cleaned_scope or not cleaned_objective:
        raise TenderIntakeError("Confirm the tender scope and buyer objective before opening a Bid Room.")
    cleaned_criteria: list[dict] = []
    seen: set[str] = set()
    for item in evaluation_criteria:
        name = str(item.get("name") or "").strip()
        try:
            weight = float(item.get("weight"))
        except (TypeError, ValueError) as error:
            raise TenderIntakeError(f"Evaluation weight for '{name or 'unnamed criterion'}' must be numeric.") from error
        if not name or weight <= 0:
            raise TenderIntakeError("Every evaluation criterion needs a name and a positive weight.")
        key = name.casefold()
        if key in seen:
            raise TenderIntakeError(f"Evaluation criterion '{name}' is duplicated.")
        seen.add(key)
        cleaned_criteria.append({"name": name, "weight": int(weight) if weight.is_integer() else weight})
    total = sum(float(item["weight"]) for item in cleaned_criteria)
    if not cleaned_criteria or abs(total - 100.0) > 0.01:
        raise TenderIntakeError(f"Evaluation weights must total 100; current total is {total:g}.")
    tender = {
        **snapshot.tender,
        "scope": cleaned_scope,
        "buyer_objective": cleaned_objective,
        "eligibility_requirements": tuple(item.strip() for item in eligibility_requirements if item.strip()),
        "evaluation_criteria": tuple(cleaned_criteria),
    }
    return replace(snapshot, tender=tender)


def build_pursuit_tender(
    snapshot: TenderSnapshot,
    *,
    tags: tuple[str, ...],
    delivery_hours: int,
    promised_outcome: str,
) -> dict:
    """Turn reviewed extraction into the explicit input contract for a Bid Room."""
    if not tags:
        raise TenderIntakeError("Confirm at least one scope tag before opening a Bid Room.")
    if delivery_hours <= 0:
        raise TenderIntakeError("Confirm a positive delivery-hours estimate before opening a Bid Room.")
    if not snapshot.tender["evaluation_criteria"]:
        raise TenderIntakeError("Tender evaluation criteria must be extracted or reviewed before opening a Bid Room.")
    total_weight = sum(float(item["weight"]) for item in snapshot.tender["evaluation_criteria"])
    if abs(total_weight - 100.0) > 0.01:
        raise TenderIntakeError(f"Evaluation weights must total 100; current total is {total_weight:g}.")
    outcome = promised_outcome.strip()
    if not outcome:
        raise TenderIntakeError("Confirm the promised buyer outcome before opening a Bid Room.")
    return {
        "id": snapshot.tender["id"],
        "title": snapshot.tender["title"],
        "buyer_objective": snapshot.tender["buyer_objective"],
        "promised_outcome": outcome,
        "tags": list(tags),
        "eligibility_requirements": list(snapshot.tender["eligibility_requirements"]),
        "delivery_hours": delivery_hours,
        "evaluation_criteria": list(snapshot.tender["evaluation_criteria"]),
        "source_snapshot": {
            "url": snapshot.source_url,
            "sha256": snapshot.sha256,
            "retrieved_at": snapshot.retrieved_at,
            "instruction_like_content": snapshot.has_instruction_like_content,
        },
    }


def intake_tender_bytes(data: bytes, *, source_url: str | None = None, content_type: str = "application/pdf") -> TenderSnapshot:
    """Create a versioned snapshot without treating document content as instructions."""
    if not data:
        raise TenderIntakeError("Tender input is empty.")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise TenderIntakeError(f"Tender input exceeds the {MAX_DOCUMENT_BYTES // 1024 // 1024} MB limit.")
    normalized_type = content_type.lower().split(";", 1)[0]
    if normalized_type == "application/pdf":
        text = _extract_pdf(data)
    elif normalized_type in {"text/plain", "text/html"}:
        text = _normalize_text(data.decode("utf-8", errors="replace"))
    else:
        raise TenderIntakeError("Tender input must be a PDF, plain text, or HTML document.")
    if not text:
        raise TenderIntakeError("Tender document contains no extractable text.")
    instruction_like = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in _INSTRUCTION_PATTERNS)
    tender = _parse_lines(text)
    tender["id"] = f"INTAKE-{hashlib.sha256(data).hexdigest()[:12]}"
    tender["source_url"] = source_url
    return TenderSnapshot(
        source_url=source_url,
        sha256=hashlib.sha256(data).hexdigest(),
        retrieved_at=datetime.now(UTC).isoformat(),
        content_type=normalized_type,
        text=text,
        has_instruction_like_content=instruction_like,
        tender=tender,
    )


def intake_tender_url(url: str) -> TenderSnapshot:
    """Download a bounded public tender document and snapshot it for review."""
    if not _is_public_url(url):
        raise TenderIntakeError("Tender URL must resolve to a public HTTP or HTTPS host.")
    request = Request(url, headers={"User-Agent": "BidPilot tender intake/0.1"})
    opener = build_opener(_PublicRedirectHandler())
    with opener.open(request, timeout=20) as response:
        final_url = response.geturl()
        if not _is_public_url(final_url):
            raise TenderIntakeError("Tender URL resolved to a non-public host.")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_DOCUMENT_BYTES:
            raise TenderIntakeError(f"Tender input exceeds the {MAX_DOCUMENT_BYTES // 1024 // 1024} MB limit.")
        data = response.read(MAX_DOCUMENT_BYTES + 1)
        content_type = response.headers.get_content_type()
    return intake_tender_bytes(data, source_url=final_url, content_type=content_type)
