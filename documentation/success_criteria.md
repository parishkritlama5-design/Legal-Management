# Success Criteria & Acceptance Criteria
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Snapshot Date:** 2025-06-30  
**Prepared by:** Strategic Operations Business Analyst

---

## 1. Purpose

This document defines the measurable conditions under which the Legal Case Management Intelligence Platform will be considered successful. It covers two levels of criteria:

1. **Acceptance Criteria** — the minimum conditions that must be met for the platform to be approved as delivered and fit for use (measured at launch)
2. **Success Metrics** — the longer-horizon business outcomes that demonstrate the platform is generating value (measured 3, 6, and 12 months post-launch)

All baselines are derived from the 2025-06-30 snapshot. Targets are operational goals that reflect both the analytic findings and industry benchmarks for plaintiff-side legal operations.

---

## 2. Acceptance Criteria (Launch Gate)

These criteria must all be satisfied before the platform is released for operational use. Each is verifiable at or immediately after delivery.

### AC-01 — Data Model Integrity

| Criterion | Test | Pass / Fail |
|---|---|---|
| All 9 tables exist in PostgreSQL with correct column names and types | `\dt` and `\d table_name` against `sql/01_create_tables.sql` | Pass if schema matches DDL exactly |
| All FK relationships enforce referential integrity | Attempt to insert orphan FK rows; expect rejection | Pass if all FK violations are rejected |
| All 5 indexes on `cases` exist (`cm`, `attorney`, `status`, `stage`, `intake`) | `\di cases*` | Pass if all 5 indexes present |
| Row counts match expected snapshot values within ±2% | `SELECT COUNT(*) FROM cases;` etc. | Cases: 2,743 ± 55; Clients: 2,500 ± 50; etc. |

### AC-02 — Data Cleaning Pipeline

| Criterion | Test | Pass / Fail |
|---|---|---|
| Duplicate clients reduced from 2,540 to 2,500 | `SELECT COUNT(*) FROM clients_clean.csv` | Pass if = 2,500 |
| 8 negative `settlement_amount` records corrected | `SELECT COUNT(*) FROM cases WHERE settlement_amount < 0` on cleaned data | Pass if = 0 |
| 10 negative `days_in_stage` records corrected | `SELECT COUNT(*) FROM cases WHERE days_in_stage < 0` on cleaned data | Pass if = 0 |
| 6 date-order violations (`date_closed < date_opened`) nulled | `SELECT COUNT(*) FROM cases WHERE date_closed < date_opened` on cleaned data | Pass if = 0 |
| Cleaning report generated with all repair counts | File exists: `python/outputs/cleaning_report.txt` with all sections | Pass if file exists and counts match |

### AC-03 — KPI Query Accuracy

| Criterion | Test | Pass / Fail |
|---|---|---|
| Firmwide workup completion rate = 60.8% ± 0.2% | Run KPI-02 query against loaded data | Pass if result in [60.6%, 61.0%] |
| Settlement rate (resolved matters) = 57.8% ± 0.5% | Run KPI-03 query | Pass if result in [57.3%, 58.3%] |
| Average settlement = $91,709 ± $500 | Run KPI-03 query | Pass if in [$91,209, $92,209] |
| Total settlement value = $30.17M ± $0.1M | Run KPI-03 query | Pass if in [$30.07M, $30.27M] |
| Open cases = 2,180 ± 5 | Run query 1.1 from `04_dashboard_queries.sql` | Pass if = 2,180 ± 5 |
| SLA query runs without error and returns 7 rows (one per stage) | Run KPI-07 query | Pass if 7 rows, no error |
| All 9 KPI queries run without SQL error | Execute all KPI queries in `03_kpi_queries.sql` | Pass if all 9 complete without error |

### AC-04 — Predictive Model

| Criterion | Test | Pass / Fail |
|---|---|---|
| Logistic Regression 5-fold CV ROC-AUC ≥ 0.68 | `python/outputs/model_metrics.txt`: CV AUC mean reported with ± std | Pass if CV mean ≥ 0.68 (actual: 0.700 ± 0.020) |
| Logistic Regression test-set ROC-AUC reported alongside CV result | `python/outputs/model_metrics.txt`: test AUC present | Pass if test AUC present (actual: 0.696) |
| Model output file exists with predictions for 686 test cases | `python/outputs/predictions.csv`: row count = 686 | Pass if = 686 |
| At-risk cases flagged = 184 ± 5 | Check `predictions.csv` for `at_risk = 1` count | Pass if in [179, 189] |
| No leakage columns present in feature set | Review `python/04_predictive_model.py` feature list | Pass if `current_stage`, `case_status`, `case_outcome`, `settlement_amount`, `date_closed`, and `days_in_stage` all absent from `X` features |
| All preprocessing (imputation, encoding) runs inside sklearn Pipeline fit on train folds only | Inspect Pipeline definition in `python/04_predictive_model.py` | Pass if no preprocessing step is fit on full dataset before split |

### AC-05 — Forecasting Model

| Criterion | Test | Pass / Fail |
|---|---|---|
| Forecast CSV exists with 6 forecast rows (Jul–Dec 2025) for new-matter demand | `python/outputs/forecast_workup_volume.csv`: 6 rows with `type = 'forecast'` | Pass if 6 rows present |
| Forecast values match updated demand series: ~162, 157, 147, 154, 122, 127 (within ±5) | Check `workups_completed` column for forecast rows | Pass if all 6 values within ±5 of targets |
| Prediction interval bounds are present and widen with horizon (not flat) | `lower_80` and `upper_80` non-null; verify interval width increases monotonically from Jul to Dec | Pass if bounds present and widening |
| Back-test MAPE ≤ 15% on last 4 held-out months | `python/outputs/model_metrics.txt` or console output | Pass if MAPE ≤ 15% (actual: 12.5%, MAE 15.8 matters/month) |
| Forecast target documented as new-matter demand, not completed-workup volume | Method note in output or script header explains right-censoring rationale (review finding H2) | Pass if rationale documented |

### AC-06 — Dashboard

| Criterion | Test | Pass / Fail |
|---|---|---|
| Dashboard contains all 7 pages | Visual inspection of dashboard file | Pass if 7 pages present |
| Executive Overview KPI tiles display: total cases, open cases, completion %, settlement rate %, total settlement value, stalled count | Visual inspection | Pass if all 6 tiles present and populated |
| Workup Funnel shows cumulative at-or-beyond counts (not distribution) | Verify funnel shape is monotone decreasing | Pass if Intake count > Retainer > … > Resolved |
| Case Manager Productivity page includes rank-ordered scorecard | Visual inspection | Pass |
| Forecasting page overlays actuals (24 months) with 6-month forecast and CI bands | Visual inspection | Pass |

### AC-07 — Documentation

| Criterion | Test | Pass / Fail |
|---|---|---|
| All 8 documentation files exist in `documentation/` | `ls documentation/` | Pass if all 8 `.md` files present |
| All KPIs have a complete entry in `kpi_dictionary.md` (12 KPIs) | Count KPI entries | Pass if 12 complete entries |
| All 9 tables have complete entries in `data_dictionary.md` | Count table sections | Pass if 9 complete sections |
| BRD contains RACI table and risk register | Visual inspection | Pass |
| Assumptions document lists ≥ 15 distinct assumptions | Count assumption entries | Pass if ≥ 15 (actual: 20) |

---

## 3. Success Metrics (Post-Launch Business Outcomes)

These metrics measure whether the platform is generating business value. They are evaluated at 3, 6, and 12 months post-launch.

### SM-01 — Workup Completion Rate

| | Baseline (Jun 2025) | 3-Month Target | 6-Month Target | 12-Month Target |
|---|---|---|---|---|
| **Firm-wide completion rate** | 60.8% | 62% | 65% | 68% |
| **Mass-tort completion rate (avg)** | ~42.6% (Camp Lejeune + Talcum avg) | 45% | 50% | 55% |
| **MVA completion rate** | 73.5% | 75% | 76% | 78% |

**How Measured:** KPI-01 query on `cases.workup_completed` grouped by `case_type`, run at each monthly refresh.

**Why This Matters:** Each 1-percentage-point increase in workup completion rate represents approximately 27 additional completed matters from the current 2,743-case book. At a 57.8% settlement rate and $91,709 average settlement, each percentage point increase represents approximately $1.43M in expected additional settled value.

---

### SM-02 — SLA Compliance Rate

| Stage | Baseline (Assumed) | 6-Month Target | 12-Month Target |
|---|---|---|---|
| Records Requested (30-day SLA) | Not measured | 65% | 75% |
| Records Received (21-day SLA) | Not measured | 65% | 75% |
| All stages (average) | Not measured | 70% | 80% |

**How Measured:** KPI-07 query on `cases.days_in_stage` vs. SLA targets, run monthly.

**Why This Matters:** Records Requested and Records Received stages represent the primary pipeline bottleneck. Improving SLA compliance in these stages is the single highest-leverage action available to the Director of Operations.

---

### SM-03 — Inactive Case Rate

| | Baseline (Jun 2025) | 3-Month Target | 6-Month Target | 12-Month Target |
|---|---|---|---|---|
| **% open caseload inactive > 30 days** | Not measured (stalled count visible; % not computed) | < 15% | < 12% | < 10% |
| **% open caseload inactive > 60 days** | Not measured | < 8% | < 6% | < 4% |

**How Measured:** KPI-08 query: `COUNT(*) FILTER (WHERE date_closed IS NULL AND CURRENT_DATE - last_activity_date > 30) / COUNT(*) FILTER (WHERE date_closed IS NULL)`.

**Why This Matters:** Inactive matters are at elevated risk of client attrition, dropped cases, and potential malpractice exposure. Each dropped case represents lost revenue; a 1% reduction in the inactive-case rate across 2,180 open matters = ~22 rescued matters.

---

### SM-04 — Duplicate Client Rate

| | Baseline (Jun 2025) | 6-Month Target | 12-Month Target |
|---|---|---|---|
| **Duplicate client rate (raw intake)** | 1.6% (40/2,540) | 0.8% | ≤ 0.5% |

**How Measured:** KPI-11: monthly deduplication scan comparing new intake records against existing `clients` on identity key.

**Why This Matters:** Duplicate records inflate intake counts, distort marketing attribution, and create compliance risk (clients may receive communications intended for their duplicate record). Reducing the rate to 0.5% requires an intake process change (dedup check at point of entry), not just a retroactive cleaning run.

---

### SM-05 — At-Risk Matter Recovery Rate

| | Baseline (Jun 2025) | 6-Month Target | 12-Month Target |
|---|---|---|---|
| **% of model-flagged at-risk matters that complete workup** | Unknown (model output new; baseline TBD) | 25% | 40% |
| **% of model-flagged at-risk matters that are dropped/lost** | Unknown | < 30% | < 20% |

**How Measured:** Compare the model's at-risk flag at each scoring date against the ultimate `workup_completed` and `case_status` outcome for those matters. Track the subset of flagged matters that received proactive intervention.

**Why This Matters:** The model flagged 184 matters as at-risk in the test set (out of 686). If even 25% of those at-risk matters are rescued through proactive intervention (closing document gaps, escalating records requests), that represents approximately 46 additional completed workups — with an estimated expected settlement value of ~$2.4M (46 × 57.8% × $91,709).

---

### SM-06 — Missing Document Rate

| | Baseline (Jun 2025) | 6-Month Target | 12-Month Target |
|---|---|---|---|
| **Avg missing documents per open matter** | Computed from `cases.missing_documents` (exact value from data) | < 1.5 | < 1.0 |
| **% of document requests unresolved at 30+ days** | Not separately tracked | < 25% | < 15% |

**How Measured:** KPI-10: `AVG(cases.missing_documents)` on open matters; `documents.status IN ('Missing','Pending')` aging query.

---

### SM-07 — Forecast Accuracy (Ongoing)

| | Baseline | 6-Month Target | 12-Month Target |
|---|---|---|---|
| **Rolling back-test MAPE (new-matter demand)** | 12.5% (last 4 months held out) | ≤ 15% | ≤ 12% |
| **MAE (new matters/month)** | 15.8 | ≤ 18 | ≤ 14 |

**How Measured:** Each month, compare the prior month's forecast demand value against the actual count of new matters opened. Update rolling MAPE calculation in `python/03_forecasting.py`. Note: the forecast targets new-matter demand, not completed-workup volume — compare against `cases.date_opened` monthly counts, not `workup_completed` counts (which are right-censored near the snapshot).

**Why This Matters:** If forecast MAPE deteriorates above 15%, the forecast is directionally unreliable and the Director of Operations should not use it for capacity planning without supplementary judgment.

---

### SM-08 — Platform Adoption

| | Baseline | 3-Month Target | 6-Month Target |
|---|---|---|---|
| **Dashboard active users (weekly)** | 0 (pre-launch) | ≥ 4 (Director of Ops + 3 CM Supervisors) | ≥ 8 |
| **KPI queries executed per month** | 0 | ≥ 9 (all KPIs run at monthly refresh) | ≥ 9 + ad hoc |
| **Stakeholders reporting decision influenced by dashboard** | 0 | ≥ 2 | ≥ 4 |

**How Measured:** Dashboard usage metrics (Power BI / Sigma usage logs); self-reported in monthly operational review.

**Why This Matters:** A platform not used is a platform with no value. Adoption by the Director of Operations and Case Manager Supervisors within 3 months is the leading indicator of long-term success.

---

## 4. Success Criteria Summary

| Criteria Set | # Criteria | Measurement Timing | Owner |
|---|---|---|---|
| AC-01: Data Model Integrity | 4 | At delivery | IT / Data |
| AC-02: Data Cleaning | 5 | At delivery | BA / Analyst |
| AC-03: KPI Query Accuracy | 7 | At delivery | BA / Director of Ops |
| AC-04: Predictive Model | 4 | At delivery | BA / Director of Ops |
| AC-05: Forecasting Model | 4 | At delivery | BA / Director of Ops |
| AC-06: Dashboard | 6 | At delivery | Director of Ops |
| AC-07: Documentation | 5 | At delivery | Managing Partner |
| SM-01: Workup Completion Rate | 3 metrics × 3 horizons | 3 / 6 / 12 months | Director of Ops |
| SM-02: SLA Compliance | 3 stages × 2 horizons | 6 / 12 months | Director of Ops |
| SM-03: Inactive Case Rate | 2 buckets × 3 horizons | 3 / 6 / 12 months | CM Supervisors |
| SM-04: Duplicate Client Rate | 1 metric × 2 horizons | 6 / 12 months | Intake Team Lead |
| SM-05: At-Risk Recovery Rate | 2 metrics × 2 horizons | 6 / 12 months | CM Supervisors |
| SM-06: Missing Document Rate | 2 metrics × 2 horizons | 6 / 12 months | CM Supervisors |
| SM-07: Forecast Accuracy | 2 metrics × 2 horizons | 6 / 12 months | BA / Analyst |
| SM-08: Platform Adoption | 3 metrics × 2 horizons | 3 / 6 months | Director of Ops |

---

*Cross-references: `documentation/business_requirements_document.md` (Objectives, Section 4), `documentation/kpi_dictionary.md` (KPI targets), `documentation/assumptions.md` (A-08: SLA targets are assumed; A-11: model requires re-validation on live data), `documentation/executive_recommendations.md` (expected business impact estimates).*
