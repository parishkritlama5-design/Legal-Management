# Assumptions & Constraints
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Snapshot Date:** 2025-06-30  
**Prepared by:** Strategic Operations Business Analyst

---

## Purpose

Explicitly stated assumptions are a professional standard in analytics and business analysis. This document catalogs every assumption made in the design, data model, KPI definitions, predictive models, and documentation of the Legal Case Management Intelligence Platform.

Each assumption carries a **risk level** (Low / Medium / High) indicating the potential impact if the assumption is wrong, and a **validation path** for how it would be confirmed or corrected when the platform is deployed against live firm data.

Assumptions are grouped into six categories: Data, Metric Definitions, Modeling, Forecasting, Operational, and Stakeholder.

---

## Category 1: Data Assumptions

### A-01 — Synthetic Data

**Statement:** All data in this platform (2,743 cases, 2,500 clients, 12 attorneys, 18 case managers, ~17.4k activities, ~15k documents, ~5.9k medical records, 329 settlements, ~15k call logs) is **synthetically generated** by `python/generate_data.py` to reflect realistic operational distributions for a plaintiff-side personal-injury and mass-tort law firm. No real client, attorney, or case data was used.

**Implications:** All KPI values, model metrics, forecast outputs, and dashboard figures reflect synthetic data patterns, not actual firm performance. The platform architecture, query logic, KPI framework, and model design are production-ready; the specific numeric findings are illustrative.

**Risk Level:** Low (for design purposes) / High (if platform numbers are used as actual firm metrics without re-running against real data)

**Validation Path:** Replace synthetic CSVs with extracts from the live case management system. Re-run all Python scripts and refresh dashboards. Re-validate model metrics on live data before production deployment.

---

### A-02 — Snapshot Date

**Statement:** All analysis uses a **single snapshot date of 2025-06-30** as the reference for "current" state. Fields like `days_in_stage` (calculated as `CURRENT_DATE - stage_entry_date`) and inactive-case detection (`CURRENT_DATE - last_activity_date`) are evaluated as of this date.

**Implications:** KPI values will change with each data refresh. The platform is not a real-time system; it is a snapshot-based analytical layer. `CURRENT_DATE` in SQL queries will evaluate to the actual query execution date in a live system, not the snapshot date. For reproducibility of the snapshot figures, the queries should be parameterized with a `@snapshot_date` parameter.

**Risk Level:** Medium

**Validation Path:** In production deployment, parameterize all `CURRENT_DATE` references to `@snapshot_date` in the ETL layer or dashboard variables, allowing point-in-time reproducibility.

---

### A-03 — Duplicate Client Detection Method

**Statement:** Duplicate client records are identified using an identity key of `last_name + first_name + date_of_birth + phone`. Matches on all four fields constitute a duplicate; the earlier `client_id` (by creation order) is retained, and the later record is merged into it.

**Implications:** This method has false-negative risk for clients with:
- Name changes (e.g., post-marriage last name change)
- Different phone numbers across contacts
- Typographical errors in DOB

It also has false-positive risk if two legitimate clients share the same name, DOB, and phone number (extremely rare but theoretically possible).

**Risk Level:** Medium

**Validation Path:** In production, implement probabilistic matching (e.g., Jaro-Winkler similarity on name, fuzzy DOB matching) with a human-review queue for borderline matches. The current exact-match method is appropriate for the synthetic dataset.

---

### A-04 — Data Quality Repairs

**Statement:** The following data quality repairs were applied in the cleaning pipeline (`python/01_data_cleaning.py`) without case-by-case manual review:

| Repair | Method | Count |
|---|---|---|
| Negative `settlement_amount` | Corrected to absolute value (`ABS()`) | 8 records |
| Negative `days_in_stage` | Corrected to absolute value | 10 records |
| `date_closed < date_opened` | `date_closed` nulled; flagged for review | 6 records |
| Null `referral_source` | Imputed to `'Unknown'` | 50 records |
| Null `email` | Left null; counted in data quality KPI | 76 records |

**Implications:** The absolute-value repair for negative settlements assumes the negative sign was a data entry error (e.g., entered as a debit rather than a credit). In a real system, negative settlement amounts should be reviewed individually to confirm they are not write-backs or adjustments.

**Risk Level:** Low (for synthetic data) / Medium (for production data — each case should be manually reviewed)

**Validation Path:** In production, route all anomalous records to a data quality exception queue for manual review rather than applying automatic repairs.

---

### A-05 — One Case Per Client Is Not Assumed

**Statement:** The data model allows a single client to have multiple cases (a client may have multiple separate matters). The deduplication process deduplicates `clients`, not `cases`. After deduplication, 2,500 unique clients have 2,743 total cases — an average of ~1.1 cases per client.

**Risk Level:** Low

**Validation Path:** Confirm with firm intake policy whether a client can legitimately have concurrent cases in the same case management system. If not, flag multi-case clients for review.

---

## Category 2: Metric Definition Assumptions

### A-06 — Workup Completion Rate Denominator

**Statement:** The denominator for KPI-01 (Workup Completion Rate) is **all cases** (open + closed), not just open cases or just closeable cases. Cases that are `Closed-Lost` or `Dropped` with `workup_completed = 0` are included and depress the rate.

**Implications:** This is a conservative metric. A "completion rate among resolvable matters" (excluding dropped cases where completion was never achievable) would produce a higher rate. The current method was chosen to reflect total firm throughput efficiency, including case attrition.

**Risk Level:** Low

**Validation Path:** Consult with Director of Operations on whether the preferred metric excludes dropped/dismissed cases. If so, add a filtered variant as KPI-01b.

---

### A-07 — Settlement Rate Denominator

**Statement:** KPI-02 (Settlement Rate) is computed on **resolved matters only** — those where `case_status IN ('Settled', 'Closed-Lost', 'Dropped')`. Open cases (2,180 matters, 79.5% of the book) are excluded from both numerator and denominator.

**Implications:** The 57.8% settlement rate reflects the outcome distribution of the 563 resolved matters only. Including open cases in the denominator would produce a firm-wide settlement rate of approximately 12% (329 / 2,743), which is misleading because the open pipeline has not yet resolved.

**Risk Level:** Low

**Validation Path:** This definition follows standard legal-operations convention. Confirm with Managing Partner that this matches their mental model of "settlement rate."

---

### A-08 — SLA Targets Are Assumed

**Statement:** The stage-level SLA targets used in KPI-07 are **assumed operational benchmarks**, not confirmed firm policy:

| Stage | Assumed Target (Days) |
|---|---|
| Intake | 3 |
| Retainer Signed | 5 |
| Records Requested | 30 |
| Records Received | 21 |
| Workup Complete | 14 |
| Demand Sent | 21 |
| Negotiation | 45 |

These targets are consistent with industry norms for plaintiff-side personal-injury practices but have not been validated against the firm's actual operations or client service agreements.

**Risk Level:** High

**Validation Path:** Present the SLA target table to the Director of Operations and Managing Partner for confirmation or revision before the platform is used for performance reporting. Targets are stored in a `VALUES` CTE in `sql/03_kpi_queries.sql` and can be updated with a single edit.

---

### A-09 — Expected Pipeline Value Methodology

**Statement:** KPI-12 (Expected Pipeline Value) is calculated as `open_cases_count × type_avg_settlement × type_settlement_rate`. This assumes:
- Future matters will resolve at the same rate as historically observed matters of the same type
- Future settlements will average the same as historical settlements of the same type
- No case-specific factors (liability strength, injury severity) are modeled

**Implications:** This is a portfolio-level probabilistic estimate, not a case-by-case valuation. It is appropriate as a leading indicator of pipeline health but should not be used as a revenue forecast for financial statement purposes.

**Risk Level:** Medium

**Validation Path:** Finance team should confirm this methodology is acceptable for operational planning. For financial reporting, case-by-case attorney valuation estimates would be more appropriate.

---

## Category 3: Modeling Assumptions

### A-10 — Leakage Avoidance (Critical)

**Statement:** The following fields were **deliberately excluded** from the predictive model's feature set to prevent data leakage — the use of information that would not be available at the time of prediction in a real operational context:

| Excluded Field | Reason |
|---|---|
| `days_in_stage` | In the synthetic data generator this field is derived from the funnel stage index, which is conditionally dependent on the target (`workup_completed`). Using it as a feature would constitute indirect target leakage. Excluded per methodology review finding C1. Field retained for SLA and operational KPIs; excluded from all model features. |
| `current_stage` | Encodes current workup position; a matter already at "Workup Complete" would trivially predict itself |
| `case_status` | Directly encodes the outcome (Settled, Closed-Lost, etc.) |
| `case_outcome` | Directly encodes the disposition after closure |
| `settlement_amount` | Only populated after settlement; unavailable for open matters |
| `date_closed` | Only populated after closure; available only for resolved matters |
| `workup_completed_date` | Only populated post-completion and right-censored for recent matters |

**Additional Methodology Fix (M1):** Imputation of missing values (median/mode) now runs inside the sklearn `Pipeline` object, fit only on training folds during cross-validation. The prior approach fit imputers on the full dataset before splitting, which introduced a minor train/test contamination through imputed values. This is corrected in the final model.

**Implications:** Excluding these fields makes the model harder (lower accuracy) but valid for real-world use on open matters where the outcome is genuinely unknown. A model trained *with* these fields would show artificially inflated accuracy but would be operationally useless (it cannot predict what is already known).

**Risk Level:** Critical if violated — would produce a model that appears accurate in testing but fails in production

**Validation Path:** Confirm feature list in `python/04_predictive_model.py` before any re-training on live data. Add automated leakage-check assertions to the training pipeline. Confirm that all preprocessing steps (imputation, encoding) are encapsulated within the cross-validation Pipeline.

---

### A-11 — Model Generalizability

**Statement:** The predictive model was trained and validated on synthetic data. Final model performance (post methodology-review fixes):

| Model | Validation Method | ROC-AUC | Notes |
|---|---|---|---|
| Logistic Regression | 5-fold stratified CV (train set) | 0.700 ± 0.020 | Headline metric; CV mean ± std |
| Logistic Regression | Single held-out test set (25%) | 0.696 | Test-set: Accuracy 0.687, Precision 0.701, Recall 0.844 |
| Random Forest | 5-fold stratified CV (train set) | 0.696 ± 0.014 | Comparable; LR selected for interpretability |

**At-risk matters flagged:** 184 of 686 test cases (26.8%). **Top predictive features (post-leakage-fix):** `missing_documents`, `medical_records_received`, `communication_count`, `attorney_years_experience`, `case_type`.

**Implications:** The CV mean (0.700) is the more robust estimate of expected performance; the single test-set AUC (0.696) provides an additional independent check. The model should be treated as a proof of concept and methodology demonstration. Before production deployment, it must be:
1. Re-trained on real historical data (minimum 18 months recommended)
2. Re-validated on a held-out test set from real data
3. Monitored for performance drift over time

**Risk Level:** High

**Validation Path:** Schedule model re-training and validation sprint after live data integration. Set a minimum acceptable 5-fold CV ROC-AUC of 0.68 on live data before enabling the at-risk queue for operational use.

---

### A-12 — Model Grain Is the Matter

**Statement:** The predictive model produces one prediction per matter (`case_id`), not one per stage transition or time period. A matter receives a single score (probability of completing workup) based on its attributes at the time the model is run.

**Implications:** The model does not produce time-varying risk scores. In production, the model should be re-scored monthly (or at each data refresh) so that scores reflect the current state of each matter.

**Risk Level:** Low

**Validation Path:** Operationalize as a monthly scoring batch job in the ETL pipeline.

---

### A-13 — Case Manager Performance Is Not Normalized by Case-Type Mix

**Statement:** The Case Manager Productivity scorecard (KPI-05) ranks CMs by completion rate without normalizing for case-type mix. A case manager assigned predominantly mass-tort cases (Camp Lejeune: 43.9% completion, Talcum: 41.3%) will show a structurally lower completion rate than a CM handling primarily MVA cases (73.5% completion) even if they are equally productive.

**Implications:** Raw completion rate rankings should not be used for formal performance evaluations without case-type normalization.

**Risk Level:** High (if used for HR decisions without normalization)

**Validation Path:** Add a "type-adjusted completion rate" metric (actual completion rate vs. expected rate given case-type mix) as a Phase 2 KPI enhancement. Communicate this limitation to Case Manager Supervisors before surfacing the rank.

---

## Category 4: Forecasting Assumptions

### A-14 — Forecast Target, Horizon, and Methodology

**Statement:** The forecast targets **monthly new-matter demand — the number of cases opened per month** — not monthly completed-workup volume. This reframing was driven by methodology review finding H2: completed-workup volume is right-censored near the snapshot date because recently opened matters have not yet had sufficient time to complete workup. Using that series in a back-test artificially depresses recent months and corrupts the error estimate. The `cases.workup_completed_date` field is the direct evidence of this censoring. New-matter demand (cases opened per month) is the uncensored leading indicator the workup team uses for capacity planning.

The model is fit on 24 months of monthly new-matter counts (July 2023 – June 2025) using a trend + seasonal decomposition. Prediction intervals are anchored on back-test residual error and **widen with horizon** (not derived from flat in-sample residuals — review fix M3).

**6-Month Forecast (Jul–Dec 2025), new matters/month:** 162, 157, 147, 154, 122, 127.

**Back-Test Performance (last 4 months held out):** MAPE = 12.5%, MAE = 15.8 matters/month.

**Disclosure:** A one-time marketing-driven intake surge is present in the 24-month history. A pure trend+seasonal model cannot fully capture a one-off spike; the surge may modestly inflate trend estimates. Monitor actuals against forecast each month and re-fit if the surge distorts the baseline.

**Key Assumptions:**
- Past monthly demand patterns are predictive of near-future patterns, absent structural breaks (mass layoff, major new mass-tort campaign launch, etc.)
- The November 2025 trough (~122 new matters) reflects seasonal demand softness, consistent with prior Q4 patterns
- Forecast intervals represent uncertainty about future demand, not uncertainty about workup throughput

**Risk Level:** Low-Medium

**Validation Path:** Re-evaluate and update the rolling forecast each month as actuals arrive. Flag the November 2025 projected demand trough (~122 matters) to the Director of Operations for capacity planning. If actual intake in July or August diverges from the 162/157 projections by > 20%, re-fit the model before publishing the November outlook.

---

### A-15 — Forecast Does Not Model Case Type Mix Shifts

**Statement:** The demand forecast models total firm-wide monthly new-matter volume as a single time series. It does not disaggregate by case type. If intake mix shifts toward mass-tort cases (which require more records-acquisition effort and have lower historical completion rates) during the forecast period, capacity pressure will be higher than the demand count alone implies.

**Risk Level:** Medium

**Validation Path:** Monitor intake mix monthly alongside the demand forecast. If mass-tort intake share increases by > 5 percentage points, flag the implied capacity impact to the Director of Operations even if total demand numbers are within forecast.

---

## Category 5: Operational Assumptions

### A-16 — `days_in_stage` Reflects Current Stage Only

**Statement:** The field `cases.days_in_stage` reflects the number of days the matter has been in its **current** stage as of the snapshot date. It does not reflect cumulative time across all historical stages.

**Implications:** Cycle-time analysis at the stage level is limited. True stage-level cycle time would require a separate `stage_history` audit table (one row per stage entry/exit per matter). This is not in the current schema.

**Risk Level:** Low-Medium

**Validation Path:** In a production deployment with a live case management system, request a stage-history export (if available) or implement an audit trigger on `cases.current_stage` changes.

---

### A-17 — `last_activity_date` Is Not Cross-Validated Against `activities`

**Statement:** `cases.last_activity_date` is a denormalized field on the `cases` table. It is assumed to reflect the maximum `activities.activity_date` for that case, but this has not been formally validated — the field could be manually updated or derived differently in the source system.

**Implications:** Inactive-case detection (KPI-08) depends on this field. If it is stale or incorrectly populated, stalled matters may be missed.

**Risk Level:** Medium

**Validation Path:** In production, add a data quality check that compares `cases.last_activity_date` against `MAX(activities.activity_date)` for each case. Flag discrepancies > 7 days.

---

### A-18 — `monthly_capacity` Is a Stated Target

**Statement:** `case_managers.monthly_capacity` represents the number of matters a case manager is *expected* to handle per month, as set by management or self-reported. It is not a measured throughput figure derived from activity logs.

**Implications:** Backlog-to-capacity ratios (KPI-06) may overstate or understate actual capacity. A case manager with a stated capacity of 35 may be able to handle 40 in practice, or only 25 depending on case complexity.

**Risk Level:** Medium

**Validation Path:** Validate `monthly_capacity` against observed throughput (completions/month per CM) quarterly. Adjust stated capacity values to reflect empirical throughput rates.

---

## Category 6: Stakeholder Assumptions

### A-19 — Stakeholder Requirements Are Assumed

**Statement:** Stakeholder requirements documented in `documentation/stakeholder_requirements.md` were derived by the business analyst based on the operational context and standard legal-ops stakeholder engagement patterns. No formal stakeholder interviews or requirements workshops were conducted for this portfolio project.

**Implications:** Specific business questions, reporting preferences, and KPI targets may differ from what actual firm stakeholders would specify.

**Risk Level:** Medium

**Validation Path:** Conduct stakeholder discovery sessions with each role group (Managing Partner, Director of Operations, etc.) before production deployment. Use the stakeholder requirements document as a conversation starter, not a final specification.

---

### A-20 — Platform Does Not Replace Judgment

**Statement:** The predictive model, at-risk queue, and SLA alerts are decision-support tools, not decision-making authorities. Case managers and supervisors must apply professional judgment to all triage and prioritization decisions surfaced by the platform.

**Implications:** The platform does not automate any legal, operational, or HR decision. All actions on flagged matters remain human-driven.

**Risk Level:** Low

---

## Summary Assumption Register

| ID | Category | Description | Risk Level | Validated? |
|---|---|---|---|---|
| A-01 | Data | Synthetic data only | High (production) | No |
| A-02 | Data | 2025-06-30 snapshot date | Medium | No |
| A-03 | Data | Duplicate detection by exact identity key | Medium | No |
| A-04 | Data | Automatic data quality repairs | Medium | No |
| A-05 | Data | Multiple cases per client allowed | Low | No |
| A-06 | Metric | Workup rate uses all cases as denominator | Low | No |
| A-07 | Metric | Settlement rate uses resolved cases only | Low | No |
| A-08 | Metric | SLA targets are assumed, not confirmed | **High** | No |
| A-09 | Metric | Pipeline value uses historical rate × avg | Medium | No |
| A-10 | Modeling | Leakage columns excluded, incl. `days_in_stage` (critical) | **Critical** | Yes |
| A-11 | Modeling | Model on synthetic data; CV AUC 0.700 ± 0.020, test AUC 0.696 | **High** | No |
| A-12 | Modeling | Single score per matter (not time-varying) | Low | No |
| A-13 | Modeling | No case-type normalization in CM rankings | **High** | No |
| A-14 | Forecasting | Targets demand (not right-censored completions); MAPE 12.5% | Low-Medium | Partial |
| A-15 | Forecasting | No case-mix shift modeled in demand forecast | Medium | No |
| A-16 | Operational | `days_in_stage` = current stage only | Low-Medium | No |
| A-17 | Operational | `last_activity_date` not cross-validated | Medium | No |
| A-18 | Operational | `monthly_capacity` is stated target | Medium | No |
| A-19 | Stakeholder | Stakeholder requirements are assumed | Medium | No |
| A-20 | Stakeholder | Platform is decision-support, not automation | Low | Yes |

---

*Cross-references: `documentation/business_requirements_document.md` (R-01 through R-08, risks), `documentation/kpi_dictionary.md` (KPI-specific caveats), `documentation/data_dictionary.md` (data quality notes per table), `python/outputs/cleaning_report.txt` (repair counts), `python/outputs/model_metrics.txt` (model validation results).*
