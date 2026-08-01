-- Contest-safe fixture. MERGE keeps reruns idempotent without deleting runs.
MERGE INTO BIDPILOT_DEMO.BIDPILOT.OPPORTUNITIES target
USING (
    SELECT 'demo-tenant' tenant_id, 'G2B-REPLAY-DATA-QUALITY' opportunity_id, 'fixture-v1' opportunity_version,
           'Public data quality and API continuity service' title, NULL source_url, 'fixture-data-quality-v1' source_sha256,
           CURRENT_TIMESTAMP() retrieved_at, 'text/plain' content_type, 'historical-demo-replay' source_status,
           'Data quality remediation and API operations' scope,
           'Improve public-data reliability while keeping citizen-facing APIs stable.' buyer_objective,
           720 delivery_hours, ARRAY_CONSTRUCT('public-data', 'data-quality', 'api-operations') tags
    UNION ALL
    SELECT 'demo-tenant', 'G2B-REPLAY-ANALYTICS', 'fixture-v1',
           'Municipal analytics governance service', NULL, 'fixture-analytics-v1',
           CURRENT_TIMESTAMP(), 'text/plain', 'historical-demo-replay',
           'Analytics governance and operating handoff',
           'Give policy teams governed analytics they can operate after handoff.',
           520, ARRAY_CONSTRUCT('analytics', 'governance', 'public-sector')
) source
ON target.tenant_id = source.tenant_id AND target.opportunity_id = source.opportunity_id
   AND target.opportunity_version = source.opportunity_version
WHEN NOT MATCHED THEN INSERT (
    tenant_id, opportunity_id, opportunity_version, title, source_url, source_sha256, retrieved_at,
    content_type, source_status, scope, buyer_objective, delivery_hours, tags
) VALUES (
    source.tenant_id, source.opportunity_id, source.opportunity_version, source.title, source.source_url,
    source.source_sha256, source.retrieved_at, source.content_type, source.source_status, source.scope,
    source.buyer_objective, source.delivery_hours, source.tags
);

MERGE INTO BIDPILOT_DEMO.BIDPILOT.REQUIREMENTS target
USING (
    SELECT 'demo-tenant' tenant_id, 'G2B-REPLAY-DATA-QUALITY' opportunity_id, 'fixture-v1' opportunity_version,
           'eligibility-1' requirement_id, 'SME confirmation' requirement_text, 'eligibility' requirement_kind
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-DATA-QUALITY', 'fixture-v1', 'eligibility-2', 'Information-system maintenance certificate', 'eligibility'
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-ANALYTICS', 'fixture-v1', 'eligibility-1', 'SME confirmation', 'eligibility'
) source
ON target.tenant_id = source.tenant_id AND target.opportunity_id = source.opportunity_id
   AND target.opportunity_version = source.opportunity_version AND target.requirement_id = source.requirement_id
WHEN NOT MATCHED THEN INSERT (tenant_id, opportunity_id, opportunity_version, requirement_id, requirement_text, requirement_kind)
VALUES (source.tenant_id, source.opportunity_id, source.opportunity_version, source.requirement_id, source.requirement_text, source.requirement_kind);

MERGE INTO BIDPILOT_DEMO.BIDPILOT.EVALUATION_CRITERIA target
USING (
    SELECT 'demo-tenant' tenant_id, 'G2B-REPLAY-DATA-QUALITY' opportunity_id, 'fixture-v1' opportunity_version, 'technical' criterion_id, 'Technical approach' criterion_name, 40 weight
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-DATA-QUALITY', 'fixture-v1', 'delivery', 'Comparable delivery', 30
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-DATA-QUALITY', 'fixture-v1', 'team', 'Delivery team', 20
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-DATA-QUALITY', 'fixture-v1', 'price', 'Price', 10
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-ANALYTICS', 'fixture-v1', 'delivery', 'Comparable delivery', 45
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-ANALYTICS', 'fixture-v1', 'team', 'Team capability', 25
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-ANALYTICS', 'fixture-v1', 'handoff', 'Operating handoff', 20
    UNION ALL SELECT 'demo-tenant', 'G2B-REPLAY-ANALYTICS', 'fixture-v1', 'price', 'Price', 10
) source
ON target.tenant_id = source.tenant_id AND target.opportunity_id = source.opportunity_id
   AND target.opportunity_version = source.opportunity_version AND target.criterion_id = source.criterion_id
WHEN NOT MATCHED THEN INSERT (tenant_id, opportunity_id, opportunity_version, criterion_id, criterion_name, weight)
VALUES (source.tenant_id, source.opportunity_id, source.opportunity_version, source.criterion_id, source.criterion_name, source.weight);

MERGE INTO BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES target
USING (
    SELECT 'demo-tenant' tenant_id, 'supplier-northstar' supplier_profile_id, 'Northstar Systems' supplier_name, 'fixture-v1' profile_version
    UNION ALL SELECT 'demo-tenant', 'supplier-atlas', 'Atlas Advisory', 'fixture-v1'
) source
ON target.tenant_id = source.tenant_id AND target.supplier_profile_id = source.supplier_profile_id
WHEN NOT MATCHED THEN INSERT (tenant_id, supplier_profile_id, supplier_name, profile_version)
VALUES (source.tenant_id, source.supplier_profile_id, source.supplier_name, source.profile_version);

MERGE INTO BIDPILOT_DEMO.BIDPILOT.CREDENTIALS target
USING (
    SELECT 'demo-tenant' tenant_id, 'supplier-northstar' supplier_profile_id, 'SME confirmation' credential_name, 'active' status
    UNION ALL SELECT 'demo-tenant', 'supplier-northstar', 'Information-system maintenance certificate', 'active'
    UNION ALL SELECT 'demo-tenant', 'supplier-atlas', 'SME confirmation', 'active'
) source
ON target.tenant_id = source.tenant_id AND target.supplier_profile_id = source.supplier_profile_id AND target.credential_name = source.credential_name
WHEN NOT MATCHED THEN INSERT (tenant_id, supplier_profile_id, credential_name, status)
VALUES (source.tenant_id, source.supplier_profile_id, source.credential_name, source.status);

MERGE INTO BIDPILOT_DEMO.BIDPILOT.AVAILABILITY target
USING (
    SELECT 'demo-tenant' tenant_id, 'supplier-northstar' supplier_profile_id, 900 available_hours, CURRENT_DATE() effective_from, DATEADD('day', 365, CURRENT_DATE()) effective_to
    UNION ALL SELECT 'demo-tenant', 'supplier-atlas', 560, CURRENT_DATE(), DATEADD('day', 365, CURRENT_DATE())
) source
ON target.tenant_id = source.tenant_id AND target.supplier_profile_id = source.supplier_profile_id
   AND target.effective_from = source.effective_from
WHEN NOT MATCHED THEN INSERT (tenant_id, supplier_profile_id, available_hours, effective_from, effective_to)
VALUES (source.tenant_id, source.supplier_profile_id, source.available_hours, source.effective_from, source.effective_to);

MERGE INTO BIDPILOT_DEMO.BIDPILOT.PAST_PROJECTS target
USING (
    SELECT 'demo-tenant' tenant_id, 'supplier-northstar' supplier_profile_id, 'project-open-data' project_id,
           'City Open Data Reliability Program' project_title, ARRAY_CONSTRUCT('public-data', 'data-quality', 'api-operations') tags,
           'Reduced recurring data defects and introduced API change control.' outcome
    UNION ALL SELECT 'demo-tenant', 'supplier-northstar', 'project-analytics', 'Regional Analytics Governance Rollout',
           ARRAY_CONSTRUCT('analytics', 'governance', 'public-sector'), 'Handed governed dashboards to policy teams with an operating playbook.'
    UNION ALL SELECT 'demo-tenant', 'supplier-northstar', 'project-api', 'Citizen API Service Transition',
           ARRAY_CONSTRUCT('api-operations', 'public-sector'), 'Transferred API support without a public-service interruption.'
    UNION ALL SELECT 'demo-tenant', 'supplier-atlas', 'project-commercial', 'Commercial Analytics Modernization',
           ARRAY_CONSTRUCT('analytics', 'governance'), 'Established a commercial analytics governance model.'
) source
ON target.tenant_id = source.tenant_id AND target.supplier_profile_id = source.supplier_profile_id AND target.project_id = source.project_id
WHEN NOT MATCHED THEN INSERT (tenant_id, supplier_profile_id, project_id, project_title, tags, outcome)
VALUES (source.tenant_id, source.supplier_profile_id, source.project_id, source.project_title, source.tags, source.outcome);
