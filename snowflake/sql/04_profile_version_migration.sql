-- Bind historical supplier evidence to the exact profile version used by each run.
-- Existing rows are backfilled only when the supplier has one unambiguous version.

ALTER TABLE BIDPILOT_DEMO.BIDPILOT.CREDENTIALS
    ADD COLUMN IF NOT EXISTS profile_version STRING;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.PEOPLE
    ADD COLUMN IF NOT EXISTS profile_version STRING;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.AVAILABILITY
    ADD COLUMN IF NOT EXISTS profile_version STRING;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.PAST_PROJECTS
    ADD COLUMN IF NOT EXISTS profile_version STRING;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.PAST_PROPOSALS
    ADD COLUMN IF NOT EXISTS profile_version STRING;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS
    ADD COLUMN IF NOT EXISTS supplier_profile_version STRING;

UPDATE BIDPILOT_DEMO.BIDPILOT.CREDENTIALS child
SET profile_version = profile.profile_version
FROM (
    SELECT tenant_id, supplier_profile_id, MIN(profile_version) AS profile_version
    FROM BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES
    GROUP BY tenant_id, supplier_profile_id
    HAVING COUNT(DISTINCT profile_version) = 1
) profile
WHERE child.tenant_id = profile.tenant_id
  AND child.supplier_profile_id = profile.supplier_profile_id
  AND child.profile_version IS NULL;

UPDATE BIDPILOT_DEMO.BIDPILOT.PEOPLE child
SET profile_version = profile.profile_version
FROM (
    SELECT tenant_id, supplier_profile_id, MIN(profile_version) AS profile_version
    FROM BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES
    GROUP BY tenant_id, supplier_profile_id
    HAVING COUNT(DISTINCT profile_version) = 1
) profile
WHERE child.tenant_id = profile.tenant_id
  AND child.supplier_profile_id = profile.supplier_profile_id
  AND child.profile_version IS NULL;

UPDATE BIDPILOT_DEMO.BIDPILOT.AVAILABILITY child
SET profile_version = profile.profile_version
FROM (
    SELECT tenant_id, supplier_profile_id, MIN(profile_version) AS profile_version
    FROM BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES
    GROUP BY tenant_id, supplier_profile_id
    HAVING COUNT(DISTINCT profile_version) = 1
) profile
WHERE child.tenant_id = profile.tenant_id
  AND child.supplier_profile_id = profile.supplier_profile_id
  AND child.profile_version IS NULL;

UPDATE BIDPILOT_DEMO.BIDPILOT.PAST_PROJECTS child
SET profile_version = profile.profile_version
FROM (
    SELECT tenant_id, supplier_profile_id, MIN(profile_version) AS profile_version
    FROM BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES
    GROUP BY tenant_id, supplier_profile_id
    HAVING COUNT(DISTINCT profile_version) = 1
) profile
WHERE child.tenant_id = profile.tenant_id
  AND child.supplier_profile_id = profile.supplier_profile_id
  AND child.profile_version IS NULL;

UPDATE BIDPILOT_DEMO.BIDPILOT.PAST_PROPOSALS child
SET profile_version = profile.profile_version
FROM (
    SELECT tenant_id, supplier_profile_id, MIN(profile_version) AS profile_version
    FROM BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES
    GROUP BY tenant_id, supplier_profile_id
    HAVING COUNT(DISTINCT profile_version) = 1
) profile
WHERE child.tenant_id = profile.tenant_id
  AND child.supplier_profile_id = profile.supplier_profile_id
  AND child.profile_version IS NULL;

UPDATE BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS run
SET supplier_profile_version = profile.profile_version
FROM (
    SELECT tenant_id, supplier_profile_id, MIN(profile_version) AS profile_version
    FROM BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES
    GROUP BY tenant_id, supplier_profile_id
    HAVING COUNT(DISTINCT profile_version) = 1
) profile
WHERE run.tenant_id = profile.tenant_id
  AND run.supplier_profile_id = profile.supplier_profile_id
  AND run.supplier_profile_version IS NULL;

ALTER TABLE BIDPILOT_DEMO.BIDPILOT.CREDENTIALS ALTER COLUMN profile_version SET NOT NULL;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.PEOPLE ALTER COLUMN profile_version SET NOT NULL;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.AVAILABILITY ALTER COLUMN profile_version SET NOT NULL;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.PAST_PROJECTS ALTER COLUMN profile_version SET NOT NULL;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.PAST_PROPOSALS ALTER COLUMN profile_version SET NOT NULL;
ALTER TABLE BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS ALTER COLUMN supplier_profile_version SET NOT NULL;
