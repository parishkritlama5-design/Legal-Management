-- =============================================================================
-- 04_dashboard_queries.sql
-- Presentation-layer queries powering the BI dashboards (Power BI / Sigma).
-- Each block maps to a specific dashboard page & visual. Designed to be used as
-- views or import queries. Dialect: PostgreSQL.
-- =============================================================================


-- =============================================================================
-- PAGE 1 — EXECUTIVE OVERVIEW
-- =============================================================================

-- 1.1 Headline KPI tiles (single-row scorecard)
SELECT
    COUNT(*)                                                       AS total_cases,
    COUNT(*) FILTER (WHERE date_closed IS NULL)                    AS open_cases,
    ROUND(100.0 * SUM(workup_completed) / COUNT(*), 1)            AS workup_completion_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE case_status = 'Settled')
          / NULLIF(COUNT(*) FILTER (
              WHERE case_status IN ('Settled','Closed-Lost','Dropped')), 0), 1)
                                                                  AS settlement_rate_pct,
    ROUND(SUM(settlement_amount) FILTER (WHERE settlement_amount > 0), 0)
                                                                  AS total_settlement_value,
    COUNT(*) FILTER (WHERE date_closed IS NULL
                       AND CURRENT_DATE - last_activity_date > 30) AS stalled_cases
FROM cases;

-- 1.2 Case mix by type (donut / bar)
SELECT case_type,
       COUNT(*)                                                   AS cases,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)         AS pct_of_book
FROM cases
GROUP BY case_type
ORDER BY cases DESC;

-- 1.3 Open pipeline value estimate (expected value = open cases x type avg settle x settle rate)
WITH type_econ AS (
    SELECT case_type,
           AVG(settlement_amount) FILTER (WHERE settlement_amount > 0) AS avg_settle,
           AVG(CASE WHEN case_status = 'Settled' THEN 1.0
                    WHEN case_status IN ('Closed-Lost','Dropped') THEN 0.0 END)
                                                                       AS settle_rate
    FROM cases
    GROUP BY case_type
)
SELECT c.case_type,
       COUNT(*) FILTER (WHERE c.date_closed IS NULL)               AS open_cases,
       ROUND(te.avg_settle, 0)                                     AS avg_settlement,
       ROUND(COALESCE(te.settle_rate,0) * te.avg_settle
             * COUNT(*) FILTER (WHERE c.date_closed IS NULL), 0)   AS expected_pipeline_value
FROM cases c
JOIN type_econ te ON te.case_type = c.case_type
GROUP BY c.case_type, te.avg_settle, te.settle_rate
ORDER BY expected_pipeline_value DESC NULLS LAST;


-- =============================================================================
-- PAGE 2 — CLIENT WORKUP FUNNEL
-- =============================================================================

-- 2.1 Funnel counts (at-or-beyond each stage) — feeds funnel visual
WITH stage_order(stage, ord) AS (
    VALUES ('Intake',1),('Retainer Signed',2),('Records Requested',3),
           ('Records Received',4),('Workup Complete',5),('Demand Sent',6),
           ('Negotiation',7),('Resolved',8)
)
SELECT s.stage, s.ord,
       COUNT(c.case_id) AS cases_at_or_beyond
FROM stage_order s
JOIN cases c
  ON (SELECT ord FROM stage_order so WHERE so.stage = c.current_stage) >= s.ord
GROUP BY s.stage, s.ord
ORDER BY s.ord;

-- 2.2 Funnel by referral source (which channels convert to completed workup?)
SELECT COALESCE(cl.referral_source, 'Unknown')                   AS referral_source,
       COUNT(*)                                                  AS cases,
       SUM(c.workup_completed)                                   AS completed,
       ROUND(100.0 * SUM(c.workup_completed) / COUNT(*), 1)      AS completion_pct
FROM cases c
JOIN clients cl ON cl.client_id = c.client_id
GROUP BY COALESCE(cl.referral_source, 'Unknown')
ORDER BY completion_pct DESC;


-- =============================================================================
-- PAGE 3 — CASE MANAGER PRODUCTIVITY
-- =============================================================================

-- 3.1 Manager scorecard (table / heatmap)
SELECT m.manager_name, m.team, m.monthly_capacity,
       COUNT(c.case_id)                                          AS caseload,
       COUNT(c.case_id) FILTER (WHERE c.date_closed IS NULL)     AS open_cases,
       ROUND(100.0 * SUM(c.workup_completed) / NULLIF(COUNT(c.case_id),0), 1)
                                                                 AS completion_pct,
       ROUND(AVG(c.communication_count), 1)                      AS avg_touchpoints,
       ROUND(AVG(c.days_in_stage) FILTER (WHERE c.days_in_stage >= 0), 1)
                                                                 AS avg_days_in_stage
FROM case_managers m
LEFT JOIN cases c ON c.assigned_case_manager = m.case_manager_id
GROUP BY m.manager_name, m.team, m.monthly_capacity
ORDER BY completion_pct DESC NULLS LAST;

-- 3.2 Activity productivity trend by month (line, one series per team)
SELECT m.team,
       DATE_TRUNC('month', a.activity_date)::date                AS activity_month,
       COUNT(*)                                                  AS activities,
       ROUND(SUM(a.duration_minutes)/60.0, 1)                    AS logged_hours
FROM activities a
JOIN case_managers m ON m.case_manager_id = a.case_manager_id
GROUP BY m.team, DATE_TRUNC('month', a.activity_date)
ORDER BY activity_month, m.team;


-- =============================================================================
-- PAGE 4 — CASE QUALITY ANALYTICS
-- =============================================================================

-- 4.1 Case quality score components by type
-- Quality proxy: records received, low missing docs, adequate communication.
SELECT case_type,
       COUNT(*)                                                  AS cases,
       ROUND(100.0 * AVG(medical_records_received), 1)           AS pct_records_received,
       ROUND(AVG(missing_documents), 2)                          AS avg_missing_docs,
       ROUND(AVG(communication_count), 1)                        AS avg_communication,
       ROUND(100.0 * AVG(
           CASE WHEN medical_records_received = 1
                 AND missing_documents = 0
                 AND communication_count >= 5 THEN 1 ELSE 0 END), 1)
                                                                 AS pct_high_quality
FROM cases
GROUP BY case_type
ORDER BY pct_high_quality DESC;

-- 4.2 Settlement value vs. case quality (scatter source: one row per settled case)
SELECT c.case_id, c.case_type,
       c.communication_count, c.missing_documents,
       c.medical_records_received,
       s.settlement_amount
FROM cases c
JOIN settlements s ON s.case_id = c.case_id
WHERE s.settlement_amount > 0;


-- =============================================================================
-- PAGE 5 — FORECASTING DASHBOARD  (actuals; forecast overlay comes from Python)
-- =============================================================================

-- 5.1 Monthly completed-workup volume (the series the model forecasts)
SELECT DATE_TRUNC('month', date_opened)::date                    AS month,
       COUNT(*) FILTER (WHERE workup_completed = 1)              AS workups_completed,
       COUNT(*)                                                  AS cases_opened
FROM cases
GROUP BY DATE_TRUNC('month', date_opened)
ORDER BY month;

-- 5.2 Intake vs. completion (capacity gap) by month
WITH intake AS (
    SELECT DATE_TRUNC('month', intake_date)::date AS month, COUNT(*) AS new_clients
    FROM clients GROUP BY DATE_TRUNC('month', intake_date)
),
done AS (
    SELECT DATE_TRUNC('month', date_opened)::date AS month,
           COUNT(*) FILTER (WHERE workup_completed = 1) AS completed
    FROM cases GROUP BY DATE_TRUNC('month', date_opened)
)
SELECT i.month, i.new_clients, COALESCE(d.completed,0) AS workups_completed,
       i.new_clients - COALESCE(d.completed,0)         AS capacity_gap
FROM intake i
LEFT JOIN done d ON d.month = i.month
ORDER BY i.month;


-- =============================================================================
-- PAGE 6 — DATA QUALITY DASHBOARD  (summary tiles; detail in 05_*)
-- =============================================================================

-- 6.1 Completeness & integrity scorecard
SELECT
    (SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NULL) / COUNT(*),2)
       FROM clients)                                             AS pct_clients_missing_email,
    (SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE referral_source IS NULL)/COUNT(*),2)
       FROM clients)                                             AS pct_clients_missing_referral,
    (SELECT COUNT(*) FROM cases WHERE settlement_amount < 0)     AS negative_settlements,
    (SELECT COUNT(*) FROM cases WHERE days_in_stage < 0)         AS negative_days_in_stage,
    (SELECT COUNT(*) FROM cases WHERE case_status = 'Settled'
                                   AND settlement_amount IS NULL) AS settled_without_amount;


-- =============================================================================
-- PAGE 7 — OPERATIONAL BOTTLENECK DASHBOARD
-- =============================================================================

-- 7.1 Where cases pile up: open count & avg age by stage
SELECT current_stage,
       COUNT(*) FILTER (WHERE date_closed IS NULL)               AS open_cases,
       ROUND(AVG(days_in_stage) FILTER (
             WHERE date_closed IS NULL AND days_in_stage >= 0),1) AS avg_days_in_stage,
       COUNT(*) FILTER (WHERE date_closed IS NULL
                          AND CURRENT_DATE - last_activity_date > 30) AS stalled_30d
FROM cases
GROUP BY current_stage
ORDER BY open_cases DESC;

-- 7.2 Records bottleneck: outstanding medical records aging
SELECT mr.status,
       COUNT(*)                                                  AS records,
       ROUND(AVG(CURRENT_DATE - mr.requested_date), 0)           AS avg_days_outstanding
FROM medical_records mr
WHERE mr.received_date IS NULL
GROUP BY mr.status;

-- =============================================================================
-- End of dashboard queries
-- =============================================================================
