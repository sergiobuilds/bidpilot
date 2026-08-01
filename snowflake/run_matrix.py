"""Execute the BidPilot 2x2 policy matrix through an authenticated Snowpark session."""

from __future__ import annotations

import argparse

import snowflake.connector
from snowflake.snowpark import Session

from snowpark_decision import evaluate_and_persist


MATRIX = (
    ("dq-northstar", "G2B-REPLAY-DATA-QUALITY", "supplier-northstar"),
    ("dq-atlas", "G2B-REPLAY-DATA-QUALITY", "supplier-atlas"),
    ("analytics-northstar", "G2B-REPLAY-ANALYTICS", "supplier-northstar"),
    ("analytics-atlas", "G2B-REPLAY-ANALYTICS", "supplier-atlas"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection", default="bidpilot-runner")
    parser.add_argument("--run-prefix", required=True, help="Unique append-safe prefix for the four run IDs")
    args = parser.parse_args()

    connector = snowflake.connector.connect(connection_name=args.connection)
    session = Session.builder.configs({"connection": connector}).create()
    try:
        for suffix, opportunity_id, supplier_profile_id in MATRIX:
            run_id = f"{args.run_prefix}-{suffix}"
            evaluate_and_persist(
                session,
                run_id=run_id,
                tenant_id="demo-tenant",
                opportunity_id=opportunity_id,
                opportunity_version="fixture-v1",
                supplier_profile_id=supplier_profile_id,
            )
            print(run_id)
    finally:
        session.close()


if __name__ == "__main__":
    main()
