from __future__ import annotations

from bidpilot.tender_catalog import load_public_tender_catalog


def test_catalog_combines_one_deep_reviewed_notice_with_five_source_found_rows() -> (
    None
):
    rows = load_public_tender_catalog()

    assert len(rows) == 6
    assert len({row["notice_number"] for row in rows}) == 6
    reviewed = [row for row in rows if row["evidence_level"] == "source-reviewed"]
    discovered = [row for row in rows if row["evidence_level"] == "source-found"]
    assert [row["notice_number"] for row in reviewed] == ["R26BK01680611-000"]
    assert len(discovered) == 5
    assert all(row["contract_value_krw"] is None for row in discovered)
    assert all(row["technical_weight"] is None for row in discovered)
    assert all(row["price_weight"] is None for row in discovered)
    assert all(row["official_url"].startswith("https://www.g2b.go.kr/") for row in rows)


def test_source_found_rows_keep_retrieval_and_future_deadline_evidence() -> None:
    rows = load_public_tender_catalog()
    discovered = [row for row in rows if row["evidence_level"] == "source-found"]

    assert {row["retrieved_at"] for row in discovered} == {"2026-08-24T02:25:13+09:00"}
    assert all(row["deadline"] > "2026-08-24T02:25:13+09:00" for row in discovered)
    assert {row["status"] for row in discovered} == {"SOURCE FOUND"}
    assert {row["verification_method"] for row in discovered} == {
        "official_g2b_detail_rendered"
    }
    assert all(
        row["verified_fields"]
        == ("notice_number", "title", "issuer", "proposal_deadline", "official_url")
        for row in discovered
    )
    assert all(
        row["unverified_fields"]
        == ("contract_value_krw", "technical_weight", "price_weight")
        for row in discovered
    )
