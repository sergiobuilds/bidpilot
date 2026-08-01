CREATE DATABASE IF NOT EXISTS BIDPILOT_DEMO;
CREATE SCHEMA IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT;

CREATE OR REPLACE TABLE BIDPILOT_DEMO.BIDPILOT.RFPS (
    rfp_id STRING,
    title STRING,
    contract_value NUMBER(12, 2),
    required_hours NUMBER(10, 0),
    estimated_delivery_cost NUMBER(12, 2),
    deadline_days NUMBER(10, 0),
    delivery_risk STRING,
    incumbent_competitor BOOLEAN
);

CREATE OR REPLACE TABLE BIDPILOT_DEMO.BIDPILOT.RFP_REQUIREMENTS (
    rfp_id STRING,
    capability STRING,
    is_mandatory BOOLEAN
);

CREATE OR REPLACE TABLE BIDPILOT_DEMO.BIDPILOT.COMPANY_CAPABILITIES (
    capability STRING
);

CREATE OR REPLACE TABLE BIDPILOT_DEMO.BIDPILOT.COMPANY_CAPACITY (
    available_hours NUMBER(10, 0),
    loaded_hourly_cost NUMBER(12, 2),
    minimum_margin_rate NUMBER(5, 4),
    minimum_lead_days NUMBER(10, 0)
);

CREATE OR REPLACE TABLE BIDPILOT_DEMO.BIDPILOT.BID_DECISIONS (
    rfp_id STRING,
    recommendation STRING,
    expected_margin NUMBER(12, 2),
    capacity_gap_hours NUMBER(10, 0),
    hard_gate_failures VARIANT,
    risks VARIANT,
    evaluated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE BIDPILOT_DEMO.BIDPILOT.PROPOSAL_TASKS (
    rfp_id STRING,
    task_name STRING,
    owner STRING,
    due_in_days NUMBER(10, 0),
    status STRING DEFAULT 'OPEN',
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
