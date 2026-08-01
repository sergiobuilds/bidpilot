"""Snowpark execution path for the same fixed BidPilot policy.

Run this only from an authenticated Snowflake Python worksheet or a configured
Snowpark environment. It persists the result needed by the Streamlit surface.
"""

from snowflake.snowpark import Session
from snowflake.snowpark.functions import (
    array_agg,
    array_construct,
    array_size,
    coalesce,
    col,
    iff,
    lit,
)


def evaluate_and_persist(session: Session, rfp_id: str) -> None:
    rfp = session.table("BIDPILOT_DEMO.BIDPILOT.RFPS").filter(col("RFP_ID") == rfp_id)
    capacity = session.table("BIDPILOT_DEMO.BIDPILOT.COMPANY_CAPACITY")
    requirements = session.table("BIDPILOT_DEMO.BIDPILOT.RFP_REQUIREMENTS").filter(
        (col("RFP_ID") == rfp_id) & col("IS_MANDATORY")
    )
    capabilities = session.table("BIDPILOT_DEMO.BIDPILOT.COMPANY_CAPABILITIES")

    missing = requirements.join(
        capabilities,
        requirements["CAPABILITY"] == capabilities["CAPABILITY"],
        "leftanti",
    ).agg(array_agg(col("CAPABILITY")).alias("MISSING_CAPABILITIES"))

    decision = (
        rfp.cross_join(capacity)
        .cross_join(missing)
        .select(
            col("RFP_ID"),
            (col("CONTRACT_VALUE") - col("ESTIMATED_DELIVERY_COST")).alias("EXPECTED_MARGIN"),
            iff(col("REQUIRED_HOURS") > col("AVAILABLE_HOURS"), col("REQUIRED_HOURS") - col("AVAILABLE_HOURS"), lit(0)).alias("CAPACITY_GAP_HOURS"),
            col("MISSING_CAPABILITIES"),
            col("MINIMUM_MARGIN_RATE"),
            col("CONTRACT_VALUE"),
            col("DEADLINE_DAYS"),
            col("MINIMUM_LEAD_DAYS"),
        )
        .with_column(
            "RECOMMENDATION",
            iff(
                (coalesce(array_size(col("MISSING_CAPABILITIES")), lit(0)) > 0)
                | (col("CAPACITY_GAP_HOURS") > 0)
                | ((col("EXPECTED_MARGIN") / col("CONTRACT_VALUE")) < col("MINIMUM_MARGIN_RATE")),
                lit("NO-BID"),
                lit("BID"),
            ),
        )
        .select(
            "RFP_ID",
            "RECOMMENDATION",
            "EXPECTED_MARGIN",
            "CAPACITY_GAP_HOURS",
            col("MISSING_CAPABILITIES").alias("HARD_GATE_FAILURES"),
            array_construct().alias("RISKS"),
        )
    )

    decision.write.save_as_table(
        "BIDPILOT_DEMO.BIDPILOT.BID_DECISIONS",
        mode="append",
        column_order="name",
    )
