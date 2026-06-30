-- =============================================================================
-- 03_kpi_queries.sql
-- Core operational KPIs for the Legal Case Management Intelligence Platform.
-- Dialect: PostgreSQL.  Techniques: CTEs, window functions, CASE, aggregations.
-- Each query is self-contained and headed by the business question it answers.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- KPI 1 — CLIENT WORKUP FUNNEL
-- Q: How many matters reach each stage of the workup pipeline, and what is the
--    stage-over-stage conversion and overall drop-off?
-- -----------------------------------------------------------------------------
WITH stage_order(stage, ord) AS (
    VALUES
        ('Intake', 1), ('Retainer Signed', 2), ('Records Requested', 3),
        ('Records Received', 4), ('Workup Complete', 5), ('Demand Sent', 6),
        ('Negotiation', 7), ('Resolved', 8)
),
-- A case that has reached stage N has, by definition, passed through every
-- earlier stage. Count cases at-or-beyond each stage to build a true funnel.
reached AS (
    SELECT s.stage, s.ord,
           COUNT(c.case_id) AS cases_reached
    FROM stage_order s
    JOIN cases c
      ON  (SELECT ord FROM stage_order so WHERE so.stage = c.current_stage) >= s.ord
    GROUP BY s.stage, s.ord
)
SELECT
    stage,
    cases_reached,
    ROUND(100.0 * cases_reached
          / FIRST_VALUE(cases_reached) OVER (ORDER BY ord), 1)        AS pct_of_intake,
    LAG(cases_reached) OVER (ORDER BY ord)                            AS prev_stage_count,
    ROUND(100.0 * cases_reached
          / NULLIF(LAG(cases_reached) OVER (ORDER BY ord), 0), 1)     AS stage_conversion_pct
FROM reached
ORDER BY ord;


-- -----------------------------------------------------------------------------
-- KPI 2 — CASE COMPLETION RATE  (workup completion)
-- Q: What share of matters have completed workup, overall and by case type?
-- -----------------------------------------------------------------------------
SELECT
    case_type,
    COUNT(*)                                                    AS total_cases,
    SUM(workup_completed)                                       AS completed_cases,
    ROUND(100.0 * SUM(workup_completed) / COUNT(*), 1)          AS completion_rate_pct,
    ROUND(100.0 * AVG(SUM(workup_completed) * 1.0 / COUNT(*))
          OVER (), 1)                                           AS firmwide_avg_pct
FROM cases
GROUP BY case_type
ORDER BY completion_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- KPI 3 — SETTLEMENT RATE & ECONOMICS
-- Q: Of resolved matters, what share settle, and what do they yield?
--    (Settlement rate is computed on RESOLVED cases, not the open pipeline.)
-- -----------------------------------------------------------------------------
WITH resolved AS (
    SELECT *
    FROM cases
    WHERE case_status IN ('Settled', 'Closed-Lost', 'Dropped')
)
SELECT
    COUNT(*)                                                    AS resolved_cases,
    SUM(CASE WHEN case_status = 'Settled' THEN 1 ELSE 0 END)    AS settled_cases,
    ROUND(100.0 * SUM(CASE WHEN case_status = 'Settled' THEN 1 ELSE 0 END)
          / COUNT(*), 1)                                        AS settlement_rate_pct,
    ROUND(AVG(CASE WHEN settlement_amount > 0
                   THEN settlement_amount END), 0)              AS avg_settlement,
    ROUND(SUM(CASE WHEN settlement_amount > 0
                   THEN settlement_amount ELSE 0 END), 0)       AS total_settlement_value
FROM resolved;


-- -----------------------------------------------------------------------------
-- KPI 4 — AVERAGE WORKUP TIME (cycle time)
-- Q: How long does it take a matter to reach workup completion / resolution?
--    Uses date_opened -> date_closed for resolved matters; otherwise age to now.
-- -----------------------------------------------------------------------------
SELECT
    case_type,
    COUNT(*) FILTER (WHERE date_closed IS NOT NULL)            AS closed_cases,
    ROUND(AVG( (date_closed - date_opened) )
          FILTER (WHERE date_closed IS NOT NULL), 1)           AS avg_days_to_close,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
              ORDER BY (date_closed - date_opened) )
          FILTER (WHERE date_closed IS NOT NULL), 1)           AS median_days_to_close,
    ROUND(AVG( (CURRENT_DATE - date_opened) )
          FILTER (WHERE date_closed IS NULL), 1)               AS avg_age_open_cases
FROM cases
GROUP BY case_type
ORDER BY avg_days_to_close DESC NULLS LAST;


-- -----------------------------------------------------------------------------
-- KPI 5 — CASE MANAGER PRODUCTIVITY
-- Q: Per case manager, how many matters, what completion rate, what activity
--    volume, and how do they rank firm-wide?
-- -----------------------------------------------------------------------------
WITH cm_cases AS (
    SELECT assigned_case_manager AS cm_id,
           COUNT(*)                         AS caseload,
           SUM(workup_completed)            AS completed,
           SUM(missing_documents)           AS open_missing_docs
    FROM cases
    GROUP BY assigned_case_manager
),
cm_activity AS (
    SELECT case_manager_id AS cm_id,
           COUNT(*)                         AS activities,
           ROUND(SUM(duration_minutes)/60.0, 1) AS logged_hours
    FROM activities
    GROUP BY case_manager_id
)
SELECT
    m.case_manager_id,
    m.manager_name,
    m.team,
    cc.caseload,
    cc.completed,
    ROUND(100.0 * cc.completed / NULLIF(cc.caseload, 0), 1)     AS completion_rate_pct,
    COALESCE(ca.activities, 0)                                  AS activities,
    COALESCE(ca.logged_hours, 0)                               AS logged_hours,
    RANK() OVER (ORDER BY 1.0 * cc.completed / NULLIF(cc.caseload,0) DESC)
                                                               AS completion_rank
FROM case_managers m
LEFT JOIN cm_cases    cc ON cc.cm_id = m.case_manager_id
LEFT JOIN cm_activity ca ON ca.cm_id = m.case_manager_id
ORDER BY completion_rate_pct DESC NULLS LAST;


-- -----------------------------------------------------------------------------
-- KPI 6 — BACKLOG BY CASE MANAGER
-- Q: Who is carrying the heaviest backlog of open, in-flight matters, and how
--    does open caseload compare to their stated monthly capacity?
-- -----------------------------------------------------------------------------
SELECT
    m.case_manager_id,
    m.manager_name,
    m.monthly_capacity,
    COUNT(c.case_id) FILTER (WHERE c.date_closed IS NULL)       AS open_backlog,
    COUNT(c.case_id) FILTER (
        WHERE c.date_closed IS NULL
          AND c.current_stage IN ('Records Requested','Records Received')
    )                                                          AS stuck_in_records,
    ROUND(
        COUNT(c.case_id) FILTER (WHERE c.date_closed IS NULL)
        * 1.0 / NULLIF(m.monthly_capacity, 0), 2)              AS backlog_to_capacity_ratio
FROM case_managers m
LEFT JOIN cases c ON c.assigned_case_manager = m.case_manager_id
GROUP BY m.case_manager_id, m.manager_name, m.monthly_capacity
ORDER BY open_backlog DESC;


-- -----------------------------------------------------------------------------
-- KPI 7 — SLA COMPLIANCE (time in current stage vs. target)
-- Q: What share of open matters are within their stage SLA, by stage?
--    Stage SLA targets (days): Intake 3, Retainer 5, Records Requested 30,
--    Records Received 21, Workup Complete 14, Demand Sent 21, Negotiation 45.
-- -----------------------------------------------------------------------------
WITH sla(stage, target_days) AS (
    VALUES
        ('Intake', 3), ('Retainer Signed', 5), ('Records Requested', 30),
        ('Records Received', 21), ('Workup Complete', 14),
        ('Demand Sent', 21), ('Negotiation', 45)
),
open_cases AS (
    SELECT current_stage, days_in_stage
    FROM cases
    WHERE date_closed IS NULL
      AND days_in_stage >= 0          -- guard against dirty negatives
)
SELECT
    s.stage,
    s.target_days,
    COUNT(o.current_stage)                                      AS open_in_stage,
    SUM(CASE WHEN o.days_in_stage <= s.target_days
             THEN 1 ELSE 0 END)                                 AS within_sla,
    ROUND(100.0 * SUM(CASE WHEN o.days_in_stage <= s.target_days
                           THEN 1 ELSE 0 END)
          / NULLIF(COUNT(o.current_stage), 0), 1)              AS sla_compliance_pct
FROM sla s
LEFT JOIN open_cases o ON o.current_stage = s.stage
GROUP BY s.stage, s.target_days
ORDER BY sla_compliance_pct ASC NULLS LAST;


-- -----------------------------------------------------------------------------
-- KPI 8 — INACTIVE CASES OVER 30 DAYS
-- Q: Which open matters have had no activity in 30+ days (stall risk)?
--    Bucketed for triage; ranked oldest-first within manager.
-- -----------------------------------------------------------------------------
SELECT
    c.case_id,
    c.case_type,
    c.current_stage,
    m.manager_name,
    c.last_activity_date,
    (CURRENT_DATE - c.last_activity_date)                       AS days_inactive,
    CASE
        WHEN CURRENT_DATE - c.last_activity_date >  90 THEN '90+ days'
        WHEN CURRENT_DATE - c.last_activity_date >  60 THEN '61-90 days'
        WHEN CURRENT_DATE - c.last_activity_date >  30 THEN '31-60 days'
        ELSE 'Active (<=30 days)'
    END                                                        AS inactivity_bucket,
    ROW_NUMBER() OVER (PARTITION BY c.assigned_case_manager
                       ORDER BY c.last_activity_date)           AS staleness_rank_in_cm
FROM cases c
JOIN case_managers m ON m.case_manager_id = c.assigned_case_manager
WHERE c.date_closed IS NULL
  AND (CURRENT_DATE - c.last_activity_date) > 30
ORDER BY days_inactive DESC;


-- -----------------------------------------------------------------------------
-- KPI 9 — MONTHLY INTAKE TRENDS  (with MoM growth & rolling average)
-- Q: How is new-client intake trending month over month?
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT DATE_TRUNC('month', intake_date)::date AS intake_month,
           COUNT(*)                               AS new_clients
    FROM clients
    GROUP BY DATE_TRUNC('month', intake_date)
)
SELECT
    intake_month,
    new_clients,
    LAG(new_clients) OVER (ORDER BY intake_month)              AS prev_month,
    ROUND(100.0 * (new_clients - LAG(new_clients) OVER (ORDER BY intake_month))
          / NULLIF(LAG(new_clients) OVER (ORDER BY intake_month), 0), 1)
                                                               AS mom_growth_pct,
    ROUND(AVG(new_clients) OVER (ORDER BY intake_month
              ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1)    AS rolling_3mo_avg
FROM monthly
ORDER BY intake_month;

-- =============================================================================
-- End of KPI queries
-- =============================================================================
