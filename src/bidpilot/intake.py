"""Safe tender URL and PDF intake for the BidPilot opportunity graph."""

from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from io import BytesIO
from urllib.parse import urlparse
from urllib.request import Request, urlopen

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
        match = re.search(r"(.+?)[\-:：]\s*(\d+)\s*(?:points?|점)", line, flags=re.I)
        if match and any(token in lower for token in ("technical", "delivery", "team", "price", "평가", "가격")):
            criteria.append({"name": match.group(1).strip(" -:："), "weight": int(match.group(2))})
        if any(token in lower for token in ("eligibility", "qualification", "자격", "등록", "certificate", "sme")):
            eligibility.append(line)
        if any(token in lower for token in ("submission", "submit", "제출", "proposal")):
            submissions.append(line)
        if not scope and any(token in lower for token in ("scope", "service", "과업", "용역")):
            scope = line
        if not buyer_objective and any(token in lower for token in ("objective", "purpose", "목적")):
            buyer_objective = line
    return {
        "title": lines[0],
        "scope": scope or "Scope requires review from the source document.",
        "buyer_objective": buyer_objective or "Buyer objective requires review from the source document.",
        "eligibility_requirements": tuple(eligibility),
        "evaluation_criteria": tuple(criteria),
        "submission_items": tuple(submissions),
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
    instruction_like = any(re.search(pattern, text, flags=re.I) for pattern in _INSTRUCTION_PATTERNS)
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
    with urlopen(request, timeout=20) as response:  # noqa: S310 - _is_public_url validates destination.
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_DOCUMENT_BYTES:
            raise TenderIntakeError(f"Tender input exceeds the {MAX_DOCUMENT_BYTES // 1024 // 1024} MB limit.")
        data = response.read(MAX_DOCUMENT_BYTES + 1)
        content_type = response.headers.get_content_type()
    return intake_tender_bytes(data, source_url=url, content_type=content_type)
