-- =============================================================================
-- 05_data_quality_queries.sql
-- Data-quality & integrity checks for the Legal Case Management platform.
-- These power the Data Quality dashboard and the analyst's pre-analysis audit.
-- Dialect: PostgreSQL.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- DQ 1 — DUPLICATE CLIENTS
-- Q: Which clients appear more than once (same first/last name + DOB)?
--    Fuzzy operational duplicates inflate intake counts and split case history.
-- -----------------------------------------------------------------------------
WITH keyed AS (
    SELECT client_id,
           LOWER(TRIM(first_name)) || '|' ||
           LOWER(TRIM(last_name))  || '|' ||
           date_of_birth::text                          AS identity_key,
           intake_date
    FROM clients
),
dups AS (
    SELECT identity_key,
           COUNT(*)                                     AS occurrences,
           MIN(client_id)                               AS keep_client_id,
           STRING_AGG(client_id, ', ' ORDER BY client_id) AS all_client_ids
    FROM keyed
    GROUP BY identity_key
    HAVING COUNT(*) > 1
)
SELECT identity_key, occurrences, keep_client_id, all_client_ids
FROM dups
ORDER BY occurrences DESC, identity_key;

-- 1b. Duplicate summary tile
WITH keyed AS (
    SELECT LOWER(TRIM(first_name))||'|'||LOWER(TRIM(last_name))||'|'||date_of_birth::text AS k
    FROM clients
)
SELECT COUNT(*)                                          AS total_client_rows,
       COUNT(DISTINCT k)                                 AS distinct_identities,
       COUNT(*) - COUNT(DISTINCT k)                      AS duplicate_rows
FROM keyed;


-- -----------------------------------------------------------------------------
-- DQ 2 — MISSING DOCUMENTS
-- Q: Which open matters have outstanding/missing documents, and how many?
--    Drives the workup blockers worklist.
-- -----------------------------------------------------------------------------
SELECT
    c.case_id,
    c.case_type,
    c.current_stage,
    COUNT(d.document_id) FILTER (WHERE d.status = 'Missing')  AS missing_docs,
    COUNT(d.document_id) FILTER (WHERE d.status = 'Pending')  AS pending_docs,
    COUNT(d.document_id)                                      AS total_docs,
    STRING_AGG(DISTINCT d.document_type, ', ')
        FILTER (WHERE d.status = 'Missing')                  AS missing_types
FROM cases c
JOIN documents d ON d.case_id = c.case_id
WHERE c.date_closed IS NULL
GROUP BY c.case_id, c.case_type, c.current_stage
HAVING COUNT(d.document_id) FILTER (WHERE d.status IN ('Missing','Pending')) > 0
ORDER BY missing_docs DESC;

-- 2b. Document completeness rate by type
SELECT document_type,
       COUNT(*)                                              AS total,
       SUM(CASE WHEN status = 'Received' THEN 1 ELSE 0 END)  AS received,
       ROUND(100.0 * SUM(CASE WHEN status='Received' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                  AS completeness_pct
FROM documents
GROUP BY document_type
ORDER BY completeness_pct ASC;


-- -----------------------------------------------------------------------------
-- DQ 3 — LOGICAL / RANGE VIOLATIONS
-- Q: Are there impossible values that would corrupt KPIs?
-- -----------------------------------------------------------------------------
-- 3a. Negative settlement amounts (data-entry errors)
SELECT case_id, case_type, settlement_amount
FROM cases
WHERE settlement_amount < 0
ORDER BY settlement_amount;

-- 3b. Negative days_in_stage
SELECT case_id, current_stage, days_in_stage
FROM cases
WHERE days_in_stage < 0
ORDER BY days_in_stage;

-- 3c. Settled cases with no settlement amount (and vice versa)
SELECT
    'settled_without_amount' AS issue, COUNT(*) AS rows
FROM cases WHERE case_status = 'Settled' AND settlement_amount IS NULL
UNION ALL
SELECT 'amount_without_settled', COUNT(*)
FROM cases WHERE case_status <> 'Settled' AND settlement_amount > 0;

-- 3d. close date earlier than open date (temporal integrity)
SELECT case_id, date_opened, date_closed
FROM cases
WHERE date_closed IS NOT NULL AND date_closed < date_opened;


-- -----------------------------------------------------------------------------
-- DQ 4 — COMPLETENESS (NULL audit on key client fields)
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                                                  AS total_clients,
    COUNT(*) FILTER (WHERE email IS NULL)                     AS missing_email,
    COUNT(*) FILTER (WHERE referral_source IS NULL)           AS missing_referral,
    COUNT(*) FILTER (WHERE state IS NULL)                     AS missing_state,
    ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NULL)
          / COUNT(*), 2)                                      AS pct_missing_email
FROM clients;


-- -----------------------------------------------------------------------------
-- DQ 5 — REFERENTIAL INTEGRITY (orphan check)
-- Q: Any child rows pointing to a non-existent parent? (Should be zero.)
-- -----------------------------------------------------------------------------
SELECT 'cases_orphan_client'   AS check_name,
       COUNT(*)                 AS violations
FROM cases c LEFT JOIN clients cl ON cl.client_id = c.client_id
WHERE cl.client_id IS NULL
UNION ALL
SELECT 'activities_orphan_case', COUNT(*)
FROM activities a LEFT JOIN cases c ON c.case_id = a.case_id
WHERE c.case_id IS NULL
UNION ALL
SELECT 'settlements_orphan_case', COUNT(*)
FROM settlements s LEFT JOIN cases c ON c.case_id = s.case_id
WHERE c.case_id IS NULL;


-- -----------------------------------------------------------------------------
-- DQ 6 — OVERALL DATA-QUALITY SCORECARD (single row for the DQ dashboard tile)
-- -----------------------------------------------------------------------------
SELECT
    (SELECT COUNT(*) - COUNT(DISTINCT
         LOWER(TRIM(first_name))||'|'||LOWER(TRIM(last_name))||'|'||date_of_birth::text)
       FROM clients)                                          AS duplicate_clients,
    (SELECT COUNT(*) FROM cases WHERE settlement_amount < 0)  AS negative_settlements,
    (SELECT COUNT(*) FROM cases WHERE days_in_stage < 0)      AS negative_days,
    (SELECT COUNT(*) FROM clients WHERE email IS NULL)        AS missing_emails,
    (SELECT COUNT(*) FROM cases c
       LEFT JOIN clients cl ON cl.client_id = c.client_id
      WHERE cl.client_id IS NULL)                             AS orphan_cases;

-- =============================================================================
-- End of data-quality queries
-- =============================================================================
