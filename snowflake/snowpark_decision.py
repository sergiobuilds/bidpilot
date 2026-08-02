"""Snowpark policy path for BidPilot Opportunity Graph runs.

This module is the policy path used for the authenticated 2x2 Snowpark matrix.
Execution provenance belongs to the persisted run and Snowflake query history,
not to import-time state in this module.
"""

from __future__ import annotations

from snowflake.snowpark import Session
from snowflake.snowpark.column import Column
from snowflake.snowpark.functions import (
    array_agg,
    array_construct,
    array_intersection,
    array_size,
    coalesce,
    col,
    count,
    current_date,
    iff,
    lit,
)

POLICY_VERSION = "2026-08-02.v1"
DECISIONS_TABLE = "BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS"


def pursue_status_expression(missing_eligibility_count: Column, capacity_gap_hours: Column, comparable_project_count: Column) -> Column:
    """Mirror ``bidpilot.policy.pursue_status`` in Snowpark expressions."""
    return iff(
        (missing_eligibility_count > lit(0)) | (capacity_gap_hours > lit(0)),
        lit("NO-GO"),
        iff(comparable_project_count < lit(2), lit("REVIEW"), lit("PURSUE")),
    )


def persisted_decision_count(session: Session, run_id: str) -> int:
    """Return the number of persisted decisions for a run without mutating state."""
    return session.table(DECISIONS_TABLE).filter(col("RUN_ID") == lit(run_id)).count()


def evaluate_and_persist(
    session: Session,
    run_id: str,
    tenant_id: str,
    opportunity_id: str,
    opportunity_version: str,
    supplier_profile_id: str,
) -> str:
    """Persist exactly one decision, or reuse the one already stored for this run."""
    existing_count = persisted_decision_count(session, run_id)
    if existing_count == 1:
        return "reused"
    if existing_count != 0:
        raise RuntimeError(f"Run {run_id!r} has {existing_count} persisted decisions; expected at most one.")

    opportunities = session.table("BIDPILOT_DEMO.BIDPILOT.OPPORTUNITIES").filter(
        (col("TENANT_ID") == tenant_id)
        & (col("OPPORTUNITY_ID") == opportunity_id)
        & (col("OPPORTUNITY_VERSION") == opportunity_version)
    )
    requirements = session.table("BIDPILOT_DEMO.BIDPILOT.REQUIREMENTS").filter(
        (col("TENANT_ID") == tenant_id)
        & (col("OPPORTUNITY_ID") == opportunity_id)
        & (col("OPPORTUNITY_VERSION") == opportunity_version)
        & (col("REQUIREMENT_KIND") == lit("eligibility"))
    )
    credentials = session.table("BIDPILOT_DEMO.BIDPILOT.CREDENTIALS").filter(
        (col("TENANT_ID") == tenant_id)
        & (col("SUPPLIER_PROFILE_ID") == supplier_profile_id)
        & (col("STATUS") == lit("active"))
    )
    missing = requirements.join(
        credentials,
        requirements["REQUIREMENT_TEXT"] == credentials["CREDENTIAL_NAME"],
        "leftanti",
    )
    missing_metrics = missing.agg(
        count(lit(1)).alias("MISSING_ELIGIBILITY_COUNT"),
        array_agg(col("REQUIREMENT_TEXT")).alias("MISSING_ELIGIBILITY"),
    )
    availability = session.table("BIDPILOT_DEMO.BIDPILOT.AVAILABILITY").filter(
        (col("TENANT_ID") == tenant_id)
        & (col("SUPPLIER_PROFILE_ID") == supplier_profile_id)
        & (col("EFFECTIVE_FROM") <= current_date())
        & (col("EFFECTIVE_TO") >= current_date())
    ).sort(col("EFFECTIVE_FROM").desc()).select(col("AVAILABLE_HOURS")).limit(1)
    projects = session.table("BIDPILOT_DEMO.BIDPILOT.PAST_PROJECTS").filter(
        (col("TENANT_ID") == tenant_id) & (col("SUPPLIER_PROFILE_ID") == supplier_profile_id)
    )
    comparable_count = projects.cross_join(opportunities).filter(
        array_size(array_intersection(projects["TAGS"], opportunities["TAGS"])) > lit(0)
    ).agg(count(lit(1)).alias("COMPARABLE_PROJECT_COUNT"))
    policy = (
        opportunities.cross_join(availability)
        .cross_join(missing_metrics)
        .cross_join(comparable_count)
        .with_column(
            "CAPACITY_GAP_HOURS",
            iff(col("DELIVERY_HOURS") > col("AVAILABLE_HOURS"), col("DELIVERY_HOURS") - col("AVAILABLE_HOURS"), lit(0)),
        )
        .with_column(
            "STATUS",
            pursue_status_expression(
                col("MISSING_ELIGIBILITY_COUNT"), col("CAPACITY_GAP_HOURS"), col("COMPARABLE_PROJECT_COUNT")
            ),
        )
        .select(
            lit(run_id).alias("RUN_ID"),
            col("STATUS"),
            coalesce(col("MISSING_ELIGIBILITY"), array_construct()).alias("MISSING_ELIGIBILITY"),
            col("CAPACITY_GAP_HOURS"),
        )
    )

    preview_count = policy.count()
    if preview_count != 1:
        raise RuntimeError(
            f"Snowpark policy for run {run_id!r} produced {preview_count} rows; expected exactly one."
        )
    policy.write.save_as_table(
        DECISIONS_TABLE,
        mode="append",
        column_order="name",
    )
    persisted_count = persisted_decision_count(session, run_id)
    if persisted_count != 1:
        raise RuntimeError(
            f"Run {run_id!r} has {persisted_count} decisions after persistence; expected exactly one."
        )
    return "inserted"
