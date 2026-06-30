-- =============================================================================
-- 02_load_data.sql
-- Load the generated CSV extracts into the schema.
-- -----------------------------------------------------------------------------
-- Two options are provided:
--   A) Bulk load via \copy   (recommended - fast, loads all ~60k rows)
--   B) Representative INSERTs (for quick demo / engines without COPY access)
-- =============================================================================

-- =============================================================================
-- OPTION A — PostgreSQL bulk load
-- Run from psql with the working directory at the project root, e.g.:
--     psql -d legal_intel -f sql/01_create_tables.sql
--     psql -d legal_intel -f sql/02_load_data.sql
-- Adjust the path in each \copy if you run from elsewhere.
-- Load order respects foreign keys (parents first).
-- =============================================================================

\copy clients         FROM 'data/clients.csv'         WITH (FORMAT csv, HEADER true, NULL '');
\copy attorneys       FROM 'data/attorneys.csv'       WITH (FORMAT csv, HEADER true, NULL '');
\copy case_managers   FROM 'data/case_managers.csv'   WITH (FORMAT csv, HEADER true, NULL '');
\copy cases           FROM 'data/cases.csv'           WITH (FORMAT csv, HEADER true, NULL '');
\copy activities      FROM 'data/activities.csv'      WITH (FORMAT csv, HEADER true, NULL '');
\copy documents       FROM 'data/documents.csv'       WITH (FORMAT csv, HEADER true, NULL '');
\copy medical_records FROM 'data/medical_records.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy settlements     FROM 'data/settlements.csv'     WITH (FORMAT csv, HEADER true, NULL '');
\copy call_logs       FROM 'data/call_logs.csv'       WITH (FORMAT csv, HEADER true, NULL '');

-- Validate row counts after load:
--   SELECT 'cases' tbl, COUNT(*) FROM cases
--   UNION ALL SELECT 'clients', COUNT(*) FROM clients
--   UNION ALL SELECT 'settlements', COUNT(*) FROM settlements;


-- =============================================================================
-- OPTION B — Representative sample INSERTs
-- (Illustrative only; values mirror the generated schema. Use Option A for the
--  full dataset. Safe to run after 01_create_tables.sql on an empty database.)
-- =============================================================================

-- INSERT INTO clients
--   (client_id, first_name, last_name, date_of_birth, gender, state, phone,
--    email, intake_date, referral_source, marketing_channel)
-- VALUES
--   ('CL-00001','Maria','Garcia','1984-03-12','F','TX','(713) 555-0142',
--    'maria.garcia12@example.com','2024-02-08','TV Advertising','Broadcast'),
--   ('CL-00002','John','Smith','1971-11-02','M','CA','(213) 555-0199',
--    'john.smith88@example.com','2024-02-11','Google / SEO','Paid Search');

-- INSERT INTO attorneys
--   (attorney_id, attorney_name, bar_state, specialty, years_experience, hire_date)
-- VALUES
--   ('ATT-001','Susan Lee, Esq.','CA','Mass Tort',17,'2015-06-01'),
--   ('ATT-002','David Cohen, Esq.','TX','Personal Injury',11,'2018-09-15');

-- INSERT INTO case_managers
--   (case_manager_id, manager_name, team, hire_date, monthly_capacity)
-- VALUES
--   ('CM-001','Aisha Okafor','Workup Team A','2019-01-14',45),
--   ('CM-002','Brandon Walker','Intake','2021-05-03',40);

-- INSERT INTO cases
--   (case_id, client_id, case_type, state, intake_date, date_opened, date_closed,
--    case_status, current_stage, assigned_case_manager, attorney_id, days_in_stage,
--    medical_records_received, missing_documents, communication_count,
--    workup_completed, case_outcome, settlement_amount, last_activity_date)
-- VALUES
--   ('CASE-000001','CL-00001','Motor Vehicle Accident','TX','2024-02-08',
--    '2024-02-10',NULL,'In Workup','Workup Complete','CM-001','ATT-002',12,
--    1,0,14,1,'In Progress',NULL,'2025-06-20'),
--   ('CASE-000002','CL-00002','Mass Tort - Roundup','CA','2024-02-11',
--    '2024-02-13','2025-04-30','Settled','Resolved','CM-001','ATT-001',8,
--    1,0,21,1,'Settled',128500.00,'2025-04-30');

-- =============================================================================
-- End of load script
-- =============================================================================
