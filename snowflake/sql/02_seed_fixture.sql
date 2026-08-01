INSERT INTO BIDPILOT_DEMO.BIDPILOT.RFPS VALUES
  ('RFP-ORBIT', 'Public-sector data platform modernization', 210000, 1050, 248000, 6, 'high', TRUE),
  ('RFP-NORTHSTAR', 'Analytics migration and governance delivery', 182000, 840, 122000, 12, 'medium', FALSE);

INSERT INTO BIDPILOT_DEMO.BIDPILOT.RFP_REQUIREMENTS VALUES
  ('RFP-ORBIT', 'cloud_migration', TRUE),
  ('RFP-ORBIT', 'data_engineering', TRUE),
  ('RFP-ORBIT', 'public_sector_clearance', TRUE),
  ('RFP-NORTHSTAR', 'cloud_migration', TRUE),
  ('RFP-NORTHSTAR', 'data_engineering', TRUE),
  ('RFP-NORTHSTAR', 'security_review', TRUE);

INSERT INTO BIDPILOT_DEMO.BIDPILOT.COMPANY_CAPABILITIES VALUES
  ('cloud_migration'), ('data_engineering'), ('security_review');

INSERT INTO BIDPILOT_DEMO.BIDPILOT.COMPANY_CAPACITY VALUES (980, 82, 0.22, 8);
