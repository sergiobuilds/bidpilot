"""Verified public-source contract for the curated Suwon G2B notice."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urljoin, urlparse

MAX_SOURCE_BYTES = 5 * 1024 * 1024
_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "public-tenders" / "R26BK01680611-000"
DEFAULT_MANIFEST_PATH = _DATA_DIR / "manifest.json"
DEFAULT_FIXTURE_PATH = _DATA_DIR / "public-fixture.json"
_OFFICIAL_HOST = "www.g2b.go.kr"
_DOWNLOAD_PATH = "/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
_NOTICE_PATTERN = re.compile(r"^R\d{2}BK\d{8}-\d{3}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?82[ .-]?)?\(?0\d{1,2}\)?[ .-]?\d{3,4}[ .-]?\d{4}(?!\d)"
)
_CONTACT_FIELD_MARKERS = ("contact", "phone", "telephone", "email", "담당자", "연락처")
_PUBLIC_PROJECTION_KEYS = {
    "schema_version",
    "source_facts",
    "supplier_assumptions",
    "public_labels",
    "derived_claims",
}
_REDIRECT_CODES = {301, 302, 303, 307, 308}


class G2BSourceError(ValueError):
    """Raised when source provenance or its public projection fails closed."""


@dataclass(frozen=True)
class SourceFetchPlan:
    """Preflighted network plan supplied to a transport callback."""

    url: str
    resolved_addresses: tuple[str, ...]
    timeout_seconds: float
    max_bytes: int


@dataclass(frozen=True)
class SourceFetchResponse:
    """Bounded transport result returned for one preflighted hop."""

    status_code: int
    content_type: str
    data: bytes
    elapsed_seconds: float
    redirect_url: str | None = None


def validate_source_url(url: str, *, notice_number: str, file_sequence: int) -> str:
    """Require the exact official G2B attachment route and notice identity."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != _OFFICIAL_HOST or parsed.port not in {None, 443}:
        raise G2BSourceError("Source URL must use the official G2B HTTPS host.")
    if parsed.username or parsed.password or parsed.path != _DOWNLOAD_PATH:
        raise G2BSourceError("Source URL must use the official G2B attachment route.")
    if not _NOTICE_PATTERN.fullmatch(notice_number):
        raise G2BSourceError("Source notice identity is malformed.")

    bid_number, bid_order = notice_number.rsplit("-", 1)
    query = parse_qs(parsed.query, keep_blank_values=True)
    expected = {
        "bidPbancNo": [bid_number],
        "bidPbancOrd": [bid_order],
        "fileSeq": [str(file_sequence)],
        "prcmBsneSeCd": ["03"],
    }
    if any(query.get(key) != value for key, value in expected.items()):
        raise G2BSourceError("Source URL does not match the declared notice identity and attachment.")
    return url


def validate_destination_addresses(addresses: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Reject a fetch when any resolved destination is not globally routable."""
    if not addresses:
        raise G2BSourceError("Source host did not resolve to a public IP address.")
    normalized: list[str] = []
    for value in addresses:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as error:
            raise G2BSourceError("Source host returned an invalid public IP address.") from error
        if not address.is_global:
            raise G2BSourceError("Every source destination must be a public IP address.")
        normalized.append(address.compressed)
    return tuple(normalized)


def validate_source_payload(
    data: bytes,
    *,
    artifact_kind: str,
    content_type: str,
    expected_sha256: str,
) -> str:
    """Validate bounded attachment bytes before extraction or projection."""
    if not data:
        raise G2BSourceError("Source payload is empty.")
    if len(data) > MAX_SOURCE_BYTES:
        raise G2BSourceError(f"Source payload exceeds the {MAX_SOURCE_BYTES // 1024 // 1024} MB limit.")
    if not _SHA256_PATTERN.fullmatch(expected_sha256):
        raise G2BSourceError("Expected source digest must be a lowercase SHA-256 value.")

    normalized_type = content_type.casefold().split(";", 1)[0].strip()
    contracts = {
        "pdf": ({"application/pdf"}, (b"%PDF-",)),
        "hwpx": (
            {"application/zip", "application/x-hwp+zip", "application/octet-stream"},
            (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
        ),
    }
    try:
        allowed_types, magic_values = contracts[artifact_kind]
    except KeyError as error:
        raise G2BSourceError(f"Unsupported source artifact kind: {artifact_kind}.") from error
    if normalized_type not in allowed_types:
        raise G2BSourceError(f"Unexpected {artifact_kind.upper()} content type: {normalized_type or 'missing'}.")
    if not data.startswith(magic_values):
        raise G2BSourceError(f"Source {artifact_kind.upper()} magic bytes are invalid.")

    actual_sha256 = hashlib.sha256(data).hexdigest()
    if actual_sha256 != expected_sha256:
        raise G2BSourceError("Source payload digest does not match its verified manifest.")
    return actual_sha256


def _preflight_fetch_plan(
    url: str,
    *,
    notice_number: str,
    file_sequence: int,
    timeout_seconds: float,
) -> SourceFetchPlan:
    validate_source_url(url, notice_number=notice_number, file_sequence=file_sequence)
    host = urlparse(url).hostname
    assert host is not None
    try:
        resolved = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise G2BSourceError("Source host did not resolve to a public IP address.") from error
    addresses = tuple(dict.fromkeys(item[4][0] for item in resolved))
    return SourceFetchPlan(
        url=url,
        resolved_addresses=validate_destination_addresses(addresses),
        timeout_seconds=timeout_seconds,
        max_bytes=MAX_SOURCE_BYTES,
    )


def fetch_source(
    url: str,
    *,
    notice_number: str,
    file_sequence: int,
    artifact_kind: str,
    expected_sha256: str,
    transport: Callable[[SourceFetchPlan], SourceFetchResponse],
    timeout_seconds: float = 20,
    max_redirects: int = 3,
) -> dict:
    """Fetch through a callback only after mandatory preflight of every hop."""
    if timeout_seconds <= 0:
        raise G2BSourceError("Source fetch timeout must be positive.")
    if max_redirects < 0:
        raise G2BSourceError("Source fetch redirect limit cannot be negative.")

    current_url = url
    elapsed_total = 0.0
    hops: list[dict] = []
    for redirect_count in range(max_redirects + 1):
        remaining = timeout_seconds - elapsed_total
        if remaining <= 0:
            raise G2BSourceError("Source fetch exceeded its configured timeout.")
        plan = _preflight_fetch_plan(
            current_url,
            notice_number=notice_number,
            file_sequence=file_sequence,
            timeout_seconds=remaining,
        )
        response = transport(plan)
        if not isinstance(response, SourceFetchResponse):
            raise G2BSourceError("Source transport returned an invalid fetch response.")
        if response.elapsed_seconds < 0:
            raise G2BSourceError("Source transport returned an invalid elapsed time.")
        elapsed_total += response.elapsed_seconds
        if elapsed_total > timeout_seconds:
            raise G2BSourceError("Source fetch exceeded its configured timeout.")
        hops.append(
            {
                "url": current_url,
                "resolved_addresses": list(plan.resolved_addresses),
                "status_code": response.status_code,
            }
        )

        if response.status_code in _REDIRECT_CODES:
            if redirect_count == max_redirects:
                raise G2BSourceError("Source fetch exceeded its redirect limit.")
            if not response.redirect_url:
                raise G2BSourceError("Source redirect did not include a destination.")
            current_url = urljoin(current_url, response.redirect_url)
            continue
        if response.status_code != 200:
            raise G2BSourceError(f"Source fetch returned HTTP {response.status_code}.")

        digest = validate_source_payload(
            response.data,
            artifact_kind=artifact_kind,
            content_type=response.content_type,
            expected_sha256=expected_sha256,
        )
        return {
            "requested_url": url,
            "final_url": current_url,
            "sha256": digest,
            "elapsed_seconds": elapsed_total,
            "redirect_count": redirect_count,
            "hops": hops,
        }
    raise G2BSourceError("Source fetch ended without a validated payload.")


def redact_public_text(text: str) -> str:
    """Remove personal contact channels from public tender text."""
    return _PHONE_PATTERN.sub("[REDACTED CONTACT]", _EMAIL_PATTERN.sub("[REDACTED CONTACT]", text))


def _find_named_contact_field(value: object) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = re.sub(r"[^a-z0-9가-힣]", "", str(key).casefold())
            if any(marker in normalized for marker in _CONTACT_FIELD_MARKERS):
                return str(key)
            found = _find_named_contact_field(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_named_contact_field(nested)
            if found:
                return found
    return None


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise G2BSourceError(f"Public source data could not be read: {path.name}.") from error
    if not isinstance(value, dict):
        raise G2BSourceError(f"Public source data must be a JSON object: {path.name}.")
    return value


def _validate_manifest(manifest: dict) -> None:
    if manifest.get("schema_version") != "bidpilot.g2b-source-manifest.v1":
        raise G2BSourceError("Unsupported G2B source manifest schema.")
    notice_number = manifest.get("notice_number")
    if not isinstance(notice_number, str) or not _NOTICE_PATTERN.fullmatch(notice_number):
        raise G2BSourceError("G2B source manifest has an invalid notice identity.")
    if not _SHA256_PATTERN.fullmatch(str(manifest.get("public_fixture_sha256") or "")):
        raise G2BSourceError("G2B source manifest has an invalid public fixture digest.")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise G2BSourceError("G2B source manifest has no artifacts.")
    seen_ids: set[str] = set()
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        kind = artifact.get("kind")
        if not isinstance(artifact_id, str) or artifact_id in seen_ids:
            raise G2BSourceError("G2B source artifact identifiers must be unique.")
        seen_ids.add(artifact_id)
        if kind not in {"pdf", "hwpx"}:
            raise G2BSourceError("G2B source artifact kind is unsupported.")
        file_sequence = 2 if artifact_id == "notice-pdf" else 3 if artifact_id == "rfp-hwpx" else None
        if file_sequence is None:
            raise G2BSourceError("G2B source manifest contains an unknown artifact.")
        validate_source_url(
            str(artifact.get("official_url") or ""),
            notice_number=notice_number,
            file_sequence=file_sequence,
        )
        if not _SHA256_PATTERN.fullmatch(str(artifact.get("sha256") or "")):
            raise G2BSourceError("G2B source artifact has an invalid SHA-256 digest.")
        observed_type = artifact.get("observed_content_type")
        accepted_types = artifact.get("accepted_content_types")
        if not isinstance(observed_type, str) or not isinstance(accepted_types, list):
            raise G2BSourceError("G2B source artifact must separate observed and accepted content types.")
        if observed_type not in accepted_types or not all(isinstance(item, str) for item in accepted_types):
            raise G2BSourceError("Observed source content type must be included in accepted content types.")
        retrieved_at = artifact.get("retrieved_at")
        try:
            parsed_at = datetime.fromisoformat(retrieved_at)
        except (TypeError, ValueError) as error:
            raise G2BSourceError("G2B source artifact lacks a valid retrieval timestamp.") from error
        if parsed_at.tzinfo is None:
            raise G2BSourceError("G2B source retrieval timestamp must include a timezone.")
    if seen_ids != {"notice-pdf", "rfp-hwpx"}:
        raise G2BSourceError("G2B source manifest must contain the notice PDF and RFP HWPX.")


def _validate_public_projection(projection: dict, *, artifact_ids: set[str]) -> None:
    unexpected_keys = set(projection) - _PUBLIC_PROJECTION_KEYS
    if unexpected_keys:
        raise G2BSourceError(
            f"Public source projection contains unclassified top-level claims: {', '.join(sorted(unexpected_keys))}."
        )
    if set(projection) != _PUBLIC_PROJECTION_KEYS:
        raise G2BSourceError("Public source projection is missing a classified claim collection.")
    if projection.get("schema_version") != "bidpilot.g2b-public-projection.v1":
        raise G2BSourceError("Unsupported public source projection schema.")
    contact_field = _find_named_contact_field(projection)
    if contact_field:
        raise G2BSourceError(f"Public source projection contains named contact field '{contact_field}'.")

    facts = projection.get("source_facts")
    assumptions = projection.get("supplier_assumptions")
    if not isinstance(facts, list) or not facts:
        raise G2BSourceError("Public source projection has no reviewable facts.")
    if not isinstance(assumptions, list) or not assumptions:
        raise G2BSourceError("Public source projection must declare supplier assumptions.")

    fact_ids: set[str] = set()
    fact_fields: set[str] = set()
    for fact in facts:
        fact_id = fact.get("fact_id")
        field = fact.get("field")
        provenance = fact.get("provenance")
        if not isinstance(fact_id, str) or not isinstance(field, str) or fact_id in fact_ids or field in fact_fields:
            raise G2BSourceError("Public source fact identifiers must be unique.")
        fact_ids.add(fact_id)
        fact_fields.add(field)
        if fact.get("classification") != "source-fact" or fact.get("review_required") is not True:
            raise G2BSourceError("Every public source fact must be classified and require review.")
        if not isinstance(provenance, dict) or provenance.get("artifact_id") not in artifact_ids:
            raise G2BSourceError("Every public source fact must cite a manifest artifact.")
        if not provenance.get("locator"):
            raise G2BSourceError("Every public source fact must include a source locator.")

    for assumption in assumptions:
        if assumption.get("classification") != "synthetic-assumption":
            raise G2BSourceError("Supplier assumptions must be explicitly synthetic.")
        if assumption.get("source_provenance") is not None:
            raise G2BSourceError("Supplier assumptions cannot claim source provenance.")

    labels = projection.get("public_labels")
    claims = projection.get("derived_claims")
    if not isinstance(labels, list) or not labels:
        raise G2BSourceError("Public source projection must classify its public labels.")
    if not isinstance(claims, list) or not claims:
        raise G2BSourceError("Public source projection must classify its derived claims.")
    if any(item.get("classification") != "public-label" for item in labels):
        raise G2BSourceError("Every public label must be explicitly classified.")
    if any(item.get("classification") != "policy-conclusion" for item in claims):
        raise G2BSourceError("Every derived claim must be explicitly classified.")
    if any(not item.get("basis") for item in claims):
        raise G2BSourceError("Every derived claim must declare its evidence basis.")

    title_fact = next((item for item in facts if item.get("field") == "title"), None)
    if not title_fact or not str(title_fact.get("value") or "").strip():
        raise G2BSourceError("Public source projection must provide one source-bound title.")

    weight_fact = next((item for item in facts if item.get("field") == "evaluation_weights"), None)
    weights = weight_fact.get("value") if weight_fact else None
    if not isinstance(weights, dict) or sum(weights.values()) != 100:
        raise G2BSourceError("Reviewed evaluation weights must total 100.")

    serialized = json.dumps(projection, ensure_ascii=False, sort_keys=True)
    if redact_public_text(serialized) != serialized:
        raise G2BSourceError("Public source projection contains personal contact details.")


def _source_contract_payload(source: dict) -> dict:
    return {
        "schema_version": source.get("schema_version"),
        "notice_number": source.get("notice_number"),
        "issuer": source.get("issuer"),
        "public_fixture_sha256": source.get("public_fixture_sha256"),
        "artifacts": source.get("artifacts"),
        "operator_review": source.get("operator_review"),
        "public_projection": source.get("public_projection"),
    }


def _contract_digest(source: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            _source_contract_payload(source),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validate_loaded_source(source: object) -> dict:
    if not isinstance(source, dict):
        raise G2BSourceError("Operator review requires a validated source contract.")
    digest = source.get("source_contract_sha256")
    if not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest):
        raise G2BSourceError("Operator review requires a validated source contract.")
    try:
        manifest = {
            "schema_version": source["schema_version"],
            "notice_number": source["notice_number"],
            "issuer": source["issuer"],
            "public_fixture_sha256": source["public_fixture_sha256"],
            "artifacts": source["artifacts"],
        }
        _validate_manifest(manifest)
        projection = source["public_projection"]
        artifact_ids = {artifact["artifact_id"] for artifact in source["artifacts"]}
        _validate_public_projection(projection, artifact_ids=artifact_ids)
        if source["operator_review"].get("status") != "required":
            raise G2BSourceError("Operator review requires a validated source contract.")
    except (KeyError, TypeError, AttributeError) as error:
        raise G2BSourceError("Operator review requires a validated source contract.") from error
    if not hmac.compare_digest(digest, _contract_digest(source)):
        raise G2BSourceError("Validated source contract digest does not match its content.")
    return source


def load_public_source(
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    fixture_path: str | Path = DEFAULT_FIXTURE_PATH,
) -> dict:
    """Load and validate the curated public contract without raw source objects."""
    manifest = _read_json(Path(manifest_path))
    fixture_path = Path(fixture_path)
    fixture = _read_json(fixture_path)
    _validate_manifest(manifest)
    if fixture.get("schema_version") != "bidpilot.g2b-public-fixture.v1":
        raise G2BSourceError("Unsupported G2B public fixture schema.")
    if fixture.get("notice_number") != manifest.get("notice_number"):
        raise G2BSourceError("Manifest and public fixture notice identities do not match.")
    projection = fixture.get("public_projection")
    if not isinstance(projection, dict):
        raise G2BSourceError("G2B public fixture has no public projection.")
    artifact_ids = {artifact["artifact_id"] for artifact in manifest["artifacts"]}
    _validate_public_projection(projection, artifact_ids=artifact_ids)
    try:
        fixture_sha256 = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    except OSError as error:
        raise G2BSourceError(f"Public source data could not be read: {fixture_path.name}.") from error
    if not hmac.compare_digest(fixture_sha256, manifest["public_fixture_sha256"]):
        raise G2BSourceError("Public fixture digest does not match the verified source manifest.")
    source = {
        "schema_version": manifest["schema_version"],
        "notice_number": manifest["notice_number"],
        "issuer": manifest["issuer"],
        "public_fixture_sha256": manifest["public_fixture_sha256"],
        "artifacts": manifest["artifacts"],
        "operator_review": fixture["operator_review"],
        "public_projection": projection,
    }
    source["source_contract_sha256"] = _contract_digest(source)
    return source


def create_operator_review(
    source: dict,
    *,
    reviewer_id: str,
    reviewed_at: str,
    confirmed_fact_ids: tuple[str, ...] | list[str],
) -> dict:
    """Create a review receipt only after every source fact is confirmed."""
    source = _validate_loaded_source(source)
    reviewer = reviewer_id.strip()
    if not reviewer:
        raise G2BSourceError("Operator review requires a reviewer identity.")
    try:
        timestamp = datetime.fromisoformat(reviewed_at)
    except ValueError as error:
        raise G2BSourceError("Operator review requires an ISO-8601 timestamp.") from error
    if timestamp.tzinfo is None:
        raise G2BSourceError("Operator review timestamp must include a timezone.")

    facts = source["public_projection"]["source_facts"]
    required = [fact["fact_id"] for fact in facts if fact.get("review_required") is True]
    if not confirmed_fact_ids:
        raise G2BSourceError("Operator review confirmations cannot be empty.")
    confirmed = list(dict.fromkeys(confirmed_fact_ids))
    missing = [fact_id for fact_id in required if fact_id not in confirmed]
    unknown = [fact_id for fact_id in confirmed if fact_id not in required]
    if missing:
        raise G2BSourceError(f"Operator review has unconfirmed source facts: {', '.join(missing)}.")
    if unknown:
        raise G2BSourceError(f"Operator review contains unknown source facts: {', '.join(unknown)}.")

    reviewed_facts_sha256 = hashlib.sha256(
        json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "status": "reviewed",
        "notice_number": source["notice_number"],
        "reviewer_id": reviewer,
        "reviewed_at": timestamp.isoformat(),
        "confirmed_fact_ids": required,
        "source_contract_sha256": source["source_contract_sha256"],
        "reviewed_facts_sha256": reviewed_facts_sha256,
        "analysis_gate": "open",
    }


def get_reviewed_facts(source: dict, receipt: object) -> tuple[dict, ...]:
    """Expose reviewed facts only when a complete receipt matches the source."""
    source = _validate_loaded_source(source)
    if not isinstance(receipt, dict) or receipt.get("status") != "reviewed":
        raise G2BSourceError("A valid operator review receipt is required to expose reviewed facts.")
    facts = source["public_projection"]["source_facts"]
    required = [fact["fact_id"] for fact in facts if fact.get("review_required") is True]
    facts_sha256 = hashlib.sha256(
        json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    valid = (
        receipt.get("notice_number") == source["notice_number"]
        and receipt.get("source_contract_sha256") == source["source_contract_sha256"]
        and receipt.get("confirmed_fact_ids") == required
        and receipt.get("reviewed_facts_sha256") == facts_sha256
        and receipt.get("analysis_gate") == "open"
        and bool(receipt.get("reviewer_id"))
        and bool(receipt.get("reviewed_at"))
    )
    if not valid:
        raise G2BSourceError("Operator review receipt does not match the validated source contract.")
    return tuple(json.loads(json.dumps(fact, ensure_ascii=False)) for fact in facts)
