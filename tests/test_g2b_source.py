from __future__ import annotations

import copy
import hashlib
import json
import socket

import pytest

from bidpilot.g2b_source import (
    DEFAULT_FIXTURE_PATH,
    DEFAULT_MANIFEST_PATH,
    G2BSourceError,
    SourceFetchResponse,
    create_operator_review,
    fetch_source,
    get_reviewed_facts,
    load_public_source,
    redact_public_text,
    validate_destination_addresses,
    validate_source_payload,
    validate_source_url,
)


NOTICE_NUMBER = "R26BK01680611-000"
NOTICE_URL = (
    "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
    "?bidPbancNo=R26BK01680611&bidPbancOrd=000&fileSeq=2&fileType=&prcmBsneSeCd=03"
)
RFP_URL = (
    "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
    "?bidPbancNo=R26BK01680611&bidPbancOrd=000&fileSeq=3&fileType=&prcmBsneSeCd=03"
)


def test_official_suwon_source_contract_has_verified_provenance() -> None:
    source = load_public_source()

    assert source["notice_number"] == NOTICE_NUMBER
    assert source["issuer"] == "Suwon City, Gyeonggi-do"
    assert source["operator_review"]["status"] == "required"
    assert len(source["source_contract_sha256"]) == 64

    artifacts = {artifact["artifact_id"]: artifact for artifact in source["artifacts"]}
    assert artifacts["notice-pdf"]["official_url"] == NOTICE_URL
    assert artifacts["notice-pdf"]["sha256"] == "d196bed74cc66e9ce95331bdf0aef825f87b39ec1a85738d425b2dc4d48b476c"
    assert artifacts["rfp-hwpx"]["official_url"] == RFP_URL
    assert artifacts["rfp-hwpx"]["sha256"] == "39315ec9c5ad2b4712fd1684171cd5ac5a5b49312e9a4c183732fa5f4672a1ce"
    assert artifacts["rfp-hwpx"]["observed_content_type"] == "application/octet-stream"
    assert "application/x-hwp+zip" in artifacts["rfp-hwpx"]["accepted_content_types"]
    assert artifacts["rfp-hwpx"]["extraction_status"] == "not_extracted"
    assert artifacts["rfp-hwpx"]["extraction_message"] == "Detailed RFP not extracted"


def test_public_projection_separates_source_facts_from_supplier_assumptions() -> None:
    projection = load_public_source()["public_projection"]

    facts = {fact["field"]: fact for fact in projection["source_facts"]}
    assert facts["title"]["value"] == "K패스 기반 수원시 사회초년생 청년 교통비 지원사업 서비스 개발 용역"
    assert facts["contract_value_krw"]["value"] == 250_000_000
    assert facts["proposal_deadline"]["value"] == "2026-09-03T16:00:00+09:00"
    assert facts["evaluation_weights"]["value"] == {"technical": 90, "price": 10}
    assert all(fact["provenance"]["artifact_id"] == "notice-pdf" for fact in facts.values())
    assert all(fact["review_required"] is True for fact in facts.values())

    assumptions = projection["supplier_assumptions"]
    assert assumptions
    assert all(item["classification"] == "synthetic-assumption" for item in assumptions)
    assert all(item["source_provenance"] is None for item in assumptions)
    labels = {item["field"]: item for item in projection["public_labels"]}
    assert labels["supplier_profile_boundary"]["value"] == "Synthetic demo supplier profile"
    conclusions = {item["field"]: item for item in projection["derived_claims"]}
    assert conclusions["eligibility_conclusion"]["value"] == "REVIEW — evidence required"
    assert "title" not in projection
    assert set(projection) == {"schema_version", "source_facts", "supplier_assumptions", "public_labels", "derived_claims"}


def test_public_projection_redacts_contact_details() -> None:
    redacted = redact_public_text(
        "담당자 홍길동 031-228-1234, 010.9876.5432, (031) 5191 2959, buyer@suwon.go.kr"
    )

    assert "031-228-1234" not in redacted
    assert "010.9876.5432" not in redacted
    assert "(031) 5191 2959" not in redacted
    assert "buyer@suwon.go.kr" not in redacted
    assert redacted.count("[REDACTED CONTACT]") == 4

    serialized_projection = str(load_public_source()["public_projection"])
    assert "@" not in serialized_projection
    assert "010-" not in serialized_projection


def test_fixture_rejects_unclassified_top_level_claims_and_named_contact_fields(tmp_path) -> None:
    fixture = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["public_projection"]["display_title"] = "Unclassified duplicate title"
    unclassified_path = tmp_path / "unclassified.json"
    unclassified_path.write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(G2BSourceError, match="unclassified top-level claims"):
        load_public_source(DEFAULT_MANIFEST_PATH, unclassified_path)

    fixture = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["public_projection"]["supplier_assumptions"][0]["contact_name"] = "홍길동"
    contact_path = tmp_path / "contact.json"
    contact_path.write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(G2BSourceError, match="named contact field"):
        load_public_source(DEFAULT_MANIFEST_PATH, contact_path)


def test_fixture_digest_rejects_empty_or_forged_fact_sets(tmp_path) -> None:
    fixture = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["public_projection"]["source_facts"] = []
    empty_path = tmp_path / "empty-facts.json"
    empty_path.write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(G2BSourceError, match="no reviewable facts"):
        load_public_source(DEFAULT_MANIFEST_PATH, empty_path)

    fixture = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["public_projection"]["source_facts"][0]["value"] = "Forged title"
    forged_path = tmp_path / "forged-facts.json"
    forged_path.write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(G2BSourceError, match="fixture digest"):
        load_public_source(DEFAULT_MANIFEST_PATH, forged_path)


def test_operator_review_requires_every_reviewable_fact() -> None:
    source = load_public_source()
    fact_ids = tuple(fact["fact_id"] for fact in source["public_projection"]["source_facts"])

    with pytest.raises(G2BSourceError, match="unconfirmed source facts"):
        create_operator_review(
            source,
            reviewer_id="operator-17",
            reviewed_at="2026-08-24T10:30:00+09:00",
            confirmed_fact_ids=fact_ids[:-1],
        )
    with pytest.raises(G2BSourceError, match="confirmations cannot be empty"):
        create_operator_review(
            source,
            reviewer_id="operator-17",
            reviewed_at="2026-08-24T10:30:00+09:00",
            confirmed_fact_ids=(),
        )
    with pytest.raises(G2BSourceError, match="validated source contract"):
        create_operator_review(
            {},
            reviewer_id="operator-17",
            reviewed_at="2026-08-24T10:30:00+09:00",
            confirmed_fact_ids=(),
        )

    mutated = copy.deepcopy(source)
    mutated["public_projection"]["source_facts"][0]["value"] = "Forged title"
    with pytest.raises(G2BSourceError, match="contract digest"):
        create_operator_review(
            mutated,
            reviewer_id="operator-17",
            reviewed_at="2026-08-24T10:30:00+09:00",
            confirmed_fact_ids=fact_ids,
        )

    review = create_operator_review(
        source,
        reviewer_id="operator-17",
        reviewed_at="2026-08-24T10:30:00+09:00",
        confirmed_fact_ids=fact_ids,
    )

    assert review["status"] == "reviewed"
    assert review["notice_number"] == NOTICE_NUMBER
    assert review["reviewer_id"] == "operator-17"
    assert review["confirmed_fact_ids"] == list(fact_ids)
    assert review["source_contract_sha256"] == source["source_contract_sha256"]
    assert get_reviewed_facts(source, review) == tuple(source["public_projection"]["source_facts"])

    forged_receipt = {**review, "source_contract_sha256": "0" * 64}
    with pytest.raises(G2BSourceError, match="review receipt"):
        get_reviewed_facts(source, forged_receipt)
    with pytest.raises(G2BSourceError, match="review receipt"):
        get_reviewed_facts(source, None)


def test_source_url_and_destination_validation_fail_closed() -> None:
    assert validate_source_url(NOTICE_URL, notice_number=NOTICE_NUMBER, file_sequence=2) == NOTICE_URL

    with pytest.raises(G2BSourceError, match="official G2B HTTPS host"):
        validate_source_url(
            NOTICE_URL.replace("www.g2b.go.kr", "g2b.example.com"),
            notice_number=NOTICE_NUMBER,
            file_sequence=2,
        )
    with pytest.raises(G2BSourceError, match="notice identity"):
        validate_source_url(NOTICE_URL, notice_number="R26BK09999999-000", file_sequence=2)
    with pytest.raises(G2BSourceError, match="public IP"):
        validate_destination_addresses(("127.0.0.1", "203.0.113.9"))


def test_source_payload_validation_checks_type_magic_size_and_digest() -> None:
    pdf = b"%PDF-1.7\nfixture"
    digest = hashlib.sha256(pdf).hexdigest()

    assert validate_source_payload(
        pdf,
        artifact_kind="pdf",
        content_type="application/pdf; charset=binary",
        expected_sha256=digest,
    ) == digest

    with pytest.raises(G2BSourceError, match="content type"):
        validate_source_payload(
            pdf,
            artifact_kind="pdf",
            content_type="text/html",
            expected_sha256=digest,
        )
    with pytest.raises(G2BSourceError, match="magic bytes"):
        validate_source_payload(
            b"not a PDF",
            artifact_kind="pdf",
            content_type="application/pdf",
            expected_sha256=hashlib.sha256(b"not a PDF").hexdigest(),
        )
    with pytest.raises(G2BSourceError, match="digest"):
        validate_source_payload(
            pdf,
            artifact_kind="pdf",
            content_type="application/pdf",
            expected_sha256="0" * 64,
        )


def test_safe_fetch_preflights_each_redirect_and_rejects_private_intermediate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = b"%PDF-1.7\nfixture"
    digest = hashlib.sha256(pdf).hexdigest()
    resolution_count = 0
    transport_calls: list[str] = []

    def resolve(_host, _port, *, type):
        nonlocal resolution_count
        assert type == socket.SOCK_STREAM
        resolution_count += 1
        address = "8.8.8.8" if resolution_count == 1 else "127.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]

    def redirect_once(plan):
        transport_calls.append(plan.url)
        return SourceFetchResponse(
            status_code=302,
            content_type="text/plain",
            data=b"",
            elapsed_seconds=0.1,
            redirect_url=f"{NOTICE_URL}&redirect_hop=1",
        )

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    with pytest.raises(G2BSourceError, match="public IP"):
        fetch_source(
            NOTICE_URL,
            notice_number=NOTICE_NUMBER,
            file_sequence=2,
            artifact_kind="pdf",
            expected_sha256=digest,
            transport=redirect_once,
        )

    assert resolution_count == 2
    assert transport_calls == [NOTICE_URL]


def test_safe_fetch_returns_validated_receipt_without_caller_asserted_destinations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = b"%PDF-1.7\nfixture"
    digest = hashlib.sha256(pdf).hexdigest()

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))],
    )

    def transport(plan):
        assert plan.resolved_addresses == ("8.8.8.8",)
        assert plan.timeout_seconds > 0
        return SourceFetchResponse(
            status_code=200,
            content_type="application/pdf",
            data=pdf,
            elapsed_seconds=0.4,
        )

    receipt = fetch_source(
        NOTICE_URL,
        notice_number=NOTICE_NUMBER,
        file_sequence=2,
        artifact_kind="pdf",
        expected_sha256=digest,
        transport=transport,
        timeout_seconds=20,
    )

    assert receipt["sha256"] == digest
    assert receipt["redirect_count"] == 0
    assert receipt["hops"][0]["resolved_addresses"] == ["8.8.8.8"]
