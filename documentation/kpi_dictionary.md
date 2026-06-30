# KPI Dictionary
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Snapshot Date:** 2025-06-30  
**Prepared by:** Strategic Operations Business Analyst

---

## Usage Notes

- All KPIs are computed against the **2025-06-30 snapshot** of the PostgreSQL database unless otherwise noted.
- "Grain" indicates the atomic unit at which the KPI is computed before aggregation.
- Formulas reference exact field names from the schema defined in `documentation/data_dictionary.md`.
- Dashboard page references map to the 7-page Power BI / Sigma dashboard in `dashboards/`.
- Targets are operational benchmarks derived from legal-ops industry norms and firm-specific data distributions; they are **assumptions** until validated with firm leadership (see `documentation/assumptions.md`, A-08).

---

## KPI Index

| # | KPI Name | Dashboard Page |
|---|---|---|
| KPI-01 | Workup Completion Rate | Executive Overview, Workup Funnel |
| KPI-02 | Settlement Rate | Executive Overview, Case Quality |
| KPI-03 | Average Settlement Value | Executive Overview, Case Quality |
| KPI-04 | Average Workup Cycle Time | Workup Funnel, Operational Bottleneck |
| KPI-05 | Case Manager Productivity Index | Case Manager Productivity |
| KPI-06 | Backlog-to-Capacity Ratio | Case Manager Productivity, Operational Bottleneck |
| KPI-07 | SLA Compliance Rate | Operational Bottleneck |
| KPI-08 | Inactive Case Rate | Executive Overview, Operational Bottleneck |
| KPI-09 | Intake Volume & MoM Growth | Forecasting |
| KPI-10 | Missing Document Rate | Data Quality, Case Quality |
| KPI-11 | Duplicate Client Rate | Data Quality |
| KPI-12 | Expected Pipeline Value | Executive Overview |

---

## KPI Detail Tables

### KPI-01 — Workup Completion Rate

| Attribute | Definition |
|---|---|
| **Business Definition** | The percentage of matters (open or closed) that have reached the "Workup Complete" milestone or beyond in the workup funnel. Measures the firm's throughput efficiency in preparing cases for demand. |
| **Formula** | `SUM(cases.workup_completed) / COUNT(cases.case_id) * 100` |
| **Exact SQL** | `ROUND(100.0 * SUM(workup_completed) / COUNT(*), 1) AS completion_rate_pct` |
| **Numerator** | Count of rows in `cases` where `workup_completed = 1` |
| **Denominator** | Total rows in `cases` (all statuses, open and closed) |
| **Grain** | One row per matter (`cases.case_id`); aggregated firm-wide or by `cases.case_type` |
| **Source Table(s)** | `cases` |
| **Filters Applied** | None for firm-wide; filtered by `case_type` for drill-down |
| **Null Handling** | `workup_completed` is NOT NULL (0/1 flag); no null risk |
| **Snapshot Value** | **60.8%** firm-wide; by type: Dog Bite 75.2%, MVA 73.5%, Premises 64.6%, Workers Comp 62.8%, Slip & Fall 56.5%, Nursing Home 56.3%, Product Liability 54.9%, Med Mal 51.6%, Roundup 51.4%, Wrongful Death 50.0%, Camp Lejeune 43.9%, Talcum 41.3% |
| **Target / Benchmark** | 68% firm-wide within 12 months; ≥ 65% for each individual case type |
| **Owner** | Director of Operations |
| **Dashboard Page** | Executive Overview (KPI tile); Workup Funnel (by type bar chart) |
| **Known Limitation** | Includes closed-lost and dropped matters in the denominator; these have `workup_completed = 0` and lower the rate. A separate "completion rate among resolvable matters" metric may be warranted in a future iteration. |

---

### KPI-02 — Settlement Rate

| Attribute | Definition |
|---|---|
| **Business Definition** | The percentage of resolved (closed) matters that achieved a settlement outcome. Computed exclusively on resolved matters; open matters are excluded from both numerator and denominator. |
| **Formula** | `COUNT(CASE WHEN case_status = 'Settled' THEN 1 END) / COUNT(*) * 100` applied to resolved matters only |
| **Exact SQL** | `ROUND(100.0 * SUM(CASE WHEN case_status = 'Settled' THEN 1 ELSE 0 END) / COUNT(*), 1) AS settlement_rate_pct` WHERE `case_status IN ('Settled','Closed-Lost','Dropped')` |
| **Numerator** | Count of matters where `cases.case_status = 'Settled'` |
| **Denominator** | Count of matters where `cases.case_status IN ('Settled', 'Closed-Lost', 'Dropped')` |
| **Grain** | One row per resolved matter |
| **Source Table(s)** | `cases` |
| **Filters Applied** | `case_status IN ('Settled', 'Closed-Lost', 'Dropped')` — open pipeline excluded |
| **Snapshot Value** | **57.8%** of resolved matters settled |
| **Target / Benchmark** | ≥ 60% settlement rate among resolved matters |
| **Owner** | Managing Partner |
| **Dashboard Page** | Executive Overview (KPI tile); Case Quality Analytics (by type) |
| **Known Limitation** | Settlement rate is sensitive to the ratio of mass-tort vs. personal-injury cases in the resolved pool; mass-tort cases have longer cycle times and may resolve differently. Monitor by case type. |

---

### KPI-03 — Average Settlement Value

| Attribute | Definition |
|---|---|
| **Business Definition** | The mean gross settlement amount across all matters with a positive settlement recorded. Used for pipeline valuation and fee revenue forecasting. |
| **Formula** | `AVG(cases.settlement_amount) WHERE settlement_amount > 0` |
| **Exact SQL** | `ROUND(AVG(CASE WHEN settlement_amount > 0 THEN settlement_amount END), 0) AS avg_settlement` |
| **Grain** | One row per settled matter |
| **Source Table(s)** | `cases` (gross amount); `settlements` (full economic decomposition: `attorney_fee`, `lien_amount`, `case_costs`, `net_to_client`) |
| **Filters Applied** | `settlement_amount > 0` (excludes the 8 records corrected from negative values) |
| **Snapshot Value** | **$91,709** average; **$30.17M** total settlement value across 329 settlements |
| **Target / Benchmark** | Maintain ≥ $85,000 average; track trend quarterly |
| **Owner** | Managing Partner / Finance |
| **Dashboard Page** | Executive Overview (KPI tile); Case Quality Analytics (scatter: settlement value vs. quality score) |
| **Known Limitation** | 8 settlement records had negative amounts in the raw data, repaired to absolute value in the cleaning pipeline. Gross amount does not reflect net-to-client after fees and liens. Use `settlements.net_to_client` for client economics. |

---

### KPI-04 — Average Workup / Cycle Time

| Attribute | Definition |
|---|---|
| **Business Definition** | The average number of calendar days from matter opening (`cases.date_opened`) to closure (`cases.date_closed`) for closed matters. For open matters, reports the average age (days since `date_opened` as of snapshot date). Used to diagnose case velocity and stage-level bottlenecks. |
| **Formula (closed)** | `AVG(cases.date_closed - cases.date_opened) FILTER (WHERE date_closed IS NOT NULL)` |
| **Formula (open age)** | `AVG(CURRENT_DATE - cases.date_opened) FILTER (WHERE date_closed IS NULL)` |
| **Stage-Level Formula** | `AVG(cases.days_in_stage) WHERE date_closed IS NULL AND days_in_stage >= 0` by `current_stage` |
| **Grain** | One row per matter; aggregated by `case_type` |
| **Source Table(s)** | `cases` |
| **Filters Applied** | `days_in_stage >= 0` guard excludes the 10 records with negative values (data quality errors) |
| **Snapshot Value** | Varies by case type; mass-tort matters have substantially longer cycle times than personal-injury |
| **Target / Benchmark** | Stage-level SLA targets: Intake ≤ 3 days, Retainer Signed ≤ 5 days, Records Requested ≤ 30 days, Records Received ≤ 21 days, Workup Complete ≤ 14 days, Demand Sent ≤ 21 days, Negotiation ≤ 45 days |
| **Owner** | Director of Operations |
| **Dashboard Page** | Workup Funnel (stage funnel); Operational Bottleneck (avg days by stage, stalled count) |
| **Known Limitation** | `days_in_stage` reflects only time in the **current** stage, not cumulative time in each historical stage. A stage-history table would be required for full cycle-time decomposition (out of current scope). Note: `days_in_stage` is used for SLA and cycle-time KPIs but is **excluded from the predictive model's feature set** (derived from funnel stage index in the synthetic generator, making it a proxy for the target — review finding C1). Additionally, `cases.workup_completed_date` (nullable) enables point-in-time cycle-time measurement for completed matters; NULL values indicate either not-yet-completed or right-censored observations. |

---

### KPI-05 — Case Manager Productivity Index

| Attribute | Definition |
|---|---|
| **Business Definition** | A composite view of case manager throughput, measured by: (a) workup completion rate across their assigned caseload, (b) total activity count, (c) logged hours, and (d) firm-wide rank. Not a single scalar; presented as a scorecard per manager. |
| **Completion Rate Formula** | `SUM(cases.workup_completed) / COUNT(cases.case_id) * 100` grouped by `cases.assigned_case_manager` |
| **Activity Volume Formula** | `COUNT(activities.activity_id)` grouped by `activities.case_manager_id` |
| **Logged Hours Formula** | `SUM(activities.duration_minutes) / 60.0` grouped by `activities.case_manager_id` |
| **Rank Formula** | `RANK() OVER (ORDER BY 1.0 * completed / NULLIF(caseload,0) DESC)` |
| **Grain** | One row per case manager (`case_managers.case_manager_id`) |
| **Source Table(s)** | `case_managers`, `cases`, `activities` |
| **Filters Applied** | None; all assigned matters included. `NULLIF(caseload,0)` prevents division by zero for managers with no assigned cases. |
| **Snapshot Value** | 18 case managers; productivity scorecard available in dashboard; top quartile completion rates exceed 70% |
| **Target / Benchmark** | Completion rate ≥ firm average (60.8%); logged hours utilization ≥ 85% of monthly capacity |
| **Owner** | Director of Operations / Case Manager Supervisors |
| **Dashboard Page** | Case Manager Productivity (rank-ordered scorecard table, heatmap) |
| **Known Limitation** | Caseload mix varies by manager; a manager handling more mass-tort cases will show a structurally lower completion rate than one handling MVA cases due to case-type difficulty, not lower individual performance. Normalize by case type before performance evaluation. |

---

### KPI-06 — Backlog-to-Capacity Ratio

| Attribute | Definition |
|---|---|
| **Business Definition** | The ratio of a case manager's current open caseload to their stated monthly capacity. A ratio > 1.0 indicates the manager is carrying more open matters than they can process in a single month at stated capacity. |
| **Formula** | `COUNT(cases.case_id) FILTER (WHERE date_closed IS NULL) / case_managers.monthly_capacity` |
| **Exact SQL** | `ROUND(COUNT(c.case_id) FILTER (WHERE c.date_closed IS NULL) * 1.0 / NULLIF(m.monthly_capacity, 0), 2) AS backlog_to_capacity_ratio` |
| **Supplementary Metric** | `stuck_in_records`: open matters where `current_stage IN ('Records Requested', 'Records Received')` — the primary bottleneck stages |
| **Grain** | One row per case manager |
| **Source Table(s)** | `case_managers`, `cases` |
| **Filters Applied** | `cases.date_closed IS NULL` (open matters only) |
| **Target / Benchmark** | Ratio ≤ 1.0 per manager; escalate if > 1.5 |
| **Owner** | Case Manager Supervisors |
| **Dashboard Page** | Case Manager Productivity; Operational Bottleneck |
| **Known Limitation** | `monthly_capacity` is a stated target, not a verified throughput measurement. Actual throughput should be validated against activity logs quarterly. |

---

### KPI-07 — SLA Compliance Rate

| Attribute | Definition |
|---|---|
| **Business Definition** | The percentage of open matters in a given stage that are within the stage's defined SLA (maximum calendar days). Computed per stage; a matter is "within SLA" if `days_in_stage ≤ target_days` for its current stage. |
| **Formula** | `SUM(CASE WHEN days_in_stage <= target_days THEN 1 ELSE 0 END) / COUNT(*) * 100` per stage |
| **Exact SQL** | See `sql/03_kpi_queries.sql`, KPI-7 block; uses `sla` VALUES CTE joined to open cases |
| **Stage SLA Targets** | Intake: 3 days; Retainer Signed: 5 days; Records Requested: 30 days; Records Received: 21 days; Workup Complete: 14 days; Demand Sent: 21 days; Negotiation: 45 days |
| **Grain** | One row per open matter; aggregated by `current_stage` |
| **Source Table(s)** | `cases` |
| **Filters Applied** | `date_closed IS NULL` (open matters only); `days_in_stage >= 0` (excludes 10 data-quality errors) |
| **Target / Benchmark** | ≥ 80% SLA compliance in each stage |
| **Owner** | Director of Operations |
| **Dashboard Page** | Operational Bottleneck (compliance bar by stage) |
| **Known Limitation** | SLA targets are assumed operational benchmarks (see `documentation/assumptions.md`, A-08). SLA compliance can only be measured for the **current** stage; historical stage compliance is not computable without a stage-history audit table. |

---

### KPI-08 — Inactive Case Rate

| Attribute | Definition |
|---|---|
| **Business Definition** | The percentage of open matters with no activity recorded in the past 30 calendar days. Matters are bucketed by inactivity duration (31-60 days, 61-90 days, 90+ days) for triage prioritization. |
| **Formula (rate)** | `COUNT(*) FILTER (WHERE date_closed IS NULL AND CURRENT_DATE - last_activity_date > 30) / COUNT(*) FILTER (WHERE date_closed IS NULL) * 100` |
| **Bucket Logic** | 90+ days / 61-90 days / 31-60 days — see KPI-8 `CASE` block in `sql/03_kpi_queries.sql` |
| **Grain** | One row per open matter; `staleness_rank_in_cm` ranks oldest-stalled per case manager |
| **Source Table(s)** | `cases`, `case_managers` |
| **Filters Applied** | `date_closed IS NULL`; `CURRENT_DATE - last_activity_date > 30` |
| **Snapshot Value** | Stalled case count exposed in Executive Overview KPI tile (query 1.1 in `sql/04_dashboard_queries.sql`) |
| **Target / Benchmark** | < 10% of open caseload inactive > 30 days |
| **Owner** | Case Manager Supervisors |
| **Dashboard Page** | Executive Overview (stalled case count tile); Operational Bottleneck (stalled count by stage, query 7.1) |
| **Known Limitation** | `last_activity_date` reflects the most recent entry in `cases`, not a cross-check against `activities` or `call_logs`. A matter could have a recent `last_activity_date` via a brief call that does not reflect substantive case progress. |

---

### KPI-09 — Intake Volume & MoM Growth

| Attribute | Definition |
|---|---|
| **Business Definition** | Monthly count of new clients added to the firm, measured by `clients.intake_date`. Month-over-month (MoM) growth rate measures the trend in new business acquisition. A 3-month rolling average smooths seasonal volatility. |
| **Monthly Count Formula** | `COUNT(*) grouped by DATE_TRUNC('month', clients.intake_date)` |
| **MoM Growth Formula** | `(current_month - prior_month) / prior_month * 100` using `LAG()` window function |
| **Rolling Avg Formula** | `AVG(new_clients) OVER (ORDER BY intake_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` |
| **Grain** | One row per calendar month |
| **Source Table(s)** | `clients` (post-deduplication: 2,500 distinct clients) |
| **Filters Applied** | Uses `clients` after deduplication; 40 duplicate records excluded |
| **Snapshot Value** | 24 months of history (2023-07 to 2025-06); peak month July 2024 (118 new clients) |
| **Target / Benchmark** | Maintain positive MoM growth trend; 3-month rolling average ≥ 80 new clients/month |
| **Owner** | Intake Team Lead |
| **Dashboard Page** | Forecasting (intake vs. new-matter demand, query 5.2; 6-month demand forecast overlay) |
| **Known Limitation** | Intake date is from the `clients` table; some clients may have a case opened (`cases.date_opened`) on a different date. For capacity planning, `cases.date_opened` (new-matter demand) is the preferred series because it is uncensored and directly reflects workup pipeline entries. `clients.intake_date` MoM growth is a marketing-acquisition metric; `cases.date_opened` monthly volume is the capacity-planning metric. The 6-month forecast (Jul–Dec 2025: ~162, 157, 147, 154, 122, 127 new matters/month) targets `cases.date_opened`, not `clients.intake_date` counts. |

---

### KPI-10 — Missing Document Rate

| Attribute | Definition |
|---|---|
| **Business Definition** | The average number of outstanding (missing or pending) documents per open matter. Also expressed as the percentage of all document requests that remain unresolved. A high rate indicates intake or records-request process failures. |
| **Per-Matter Formula** | `AVG(cases.missing_documents) WHERE date_closed IS NULL` |
| **Document-Level Formula** | `COUNT(*) FILTER (WHERE status IN ('Missing','Pending')) / COUNT(*) * 100` on `documents` table |
| **Grain** | Matter-level: `cases.case_id`; Document-level: `documents.document_id` |
| **Source Table(s)** | `cases` (denormalized `missing_documents` count); `documents` (granular status) |
| **Filters Applied** | Open matters for per-matter metric; all documents for document-level metric |
| **Target / Benchmark** | Average missing documents per open matter < 1.0; document-level missing rate < 15% |
| **Owner** | Case Manager Supervisors |
| **Dashboard Page** | Data Quality (query 6.1 scorecard); Case Quality Analytics (avg missing docs by type, query 4.1) |
| **Known Limitation** | `cases.missing_documents` is a denormalized count that must be kept in sync with `documents.status`. If documents are added or updated without refreshing this field, the count will drift. |

---

### KPI-11 — Duplicate Client Rate

| Attribute | Definition |
|---|---|
| **Business Definition** | The percentage of raw client records identified as duplicates of an existing client based on identity key matching (name + date of birth + phone). Measures intake data hygiene. |
| **Formula** | `duplicate_count / total_raw_clients * 100` |
| **Snapshot Value** | **40 duplicates** detected in 2,540 raw records = **1.6% duplicate rate** (clients reduced to 2,500 post-deduplication) |
| **Cleaning Logic** | Duplicates merged into earliest `client_id` by identity key; see `python/01_data_cleaning.py` and cleaning report |
| **Grain** | One row per raw client record |
| **Source Table(s)** | `clients` (raw); `data/processed/clients_clean.csv` (cleaned) |
| **Target / Benchmark** | ≤ 0.5% duplicate rate on an ongoing basis (post-platform deduplication controls) |
| **Owner** | Intake Team Lead / IT-Data |
| **Dashboard Page** | Data Quality (duplicate count tile, query 6.1) |
| **Known Limitation** | Identity-key matching (name + DOB + phone) has false-negative risk for clients with name changes, transposed DOB, or different phone numbers across contacts. Probabilistic matching would reduce this risk. |

---

### KPI-12 — Expected Pipeline Value

| Attribute | Definition |
|---|---|
| **Business Definition** | The estimated gross revenue value of all open matters, calculated as the product of open case count, type-level historical average settlement amount, and type-level historical settlement rate. Represents a probabilistic expected value, not a committed revenue figure. |
| **Formula** | `SUM(open_cases_by_type × avg_settlement_by_type × settlement_rate_by_type)` |
| **Exact SQL** | See `sql/04_dashboard_queries.sql`, query 1.3 — uses `type_econ` CTE joined to open cases |
| **Grain** | Aggregated by `case_type`; summed to firm-wide total |
| **Source Table(s)** | `cases` (open cases count, settlement amounts, settlement status) |
| **Filters Applied** | `date_closed IS NULL` for open case count; `settlement_amount > 0` for average; `case_status IN ('Settled','Closed-Lost','Dropped')` for rate denominator |
| **Target / Benchmark** | Track as leading indicator of revenue health; no fixed benchmark (depends on mix and settlement rates) |
| **Owner** | Managing Partner / Finance |
| **Dashboard Page** | Executive Overview (pipeline value by case type, query 1.3) |
| **Known Limitation** | Expected value assumes future cases resolve at the same rate and value as historical cases of the same type. Mass-tort cases with low historical resolution rates (Camp Lejeune 43.9%, Talcum 41.3%) generate wide variance. This is a probabilistic estimate, not a revenue forecast. |

---

## SLA Reference Table

| Stage | SLA Target (Days) | Applied In |
|---|---|---|
| Intake | 3 | KPI-07, KPI-04 |
| Retainer Signed | 5 | KPI-07, KPI-04 |
| Records Requested | 30 | KPI-07, KPI-04 |
| Records Received | 21 | KPI-07, KPI-04 |
| Workup Complete | 14 | KPI-07, KPI-04 |
| Demand Sent | 21 | KPI-07, KPI-04 |
| Negotiation | 45 | KPI-07, KPI-04 |

*SLA targets are assumptions pending confirmation with firm leadership. See `documentation/assumptions.md`, A-08.*

---

*Cross-references: `sql/03_kpi_queries.sql` (KPI queries), `sql/04_dashboard_queries.sql` (dashboard queries), `documentation/data_dictionary.md` (field definitions), `documentation/assumptions.md` (all stated assumptions).*
