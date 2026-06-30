# Business Requirements Document (BRD)
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Status:** Approved — Baseline  
**Snapshot Date:** 2025-06-30 | **Prepared by:** Strategic Operations Business Analyst  
**Last Revised:** 2025-06-30

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Business Problem & Background](#2-business-problem--background)
3. [Project Scope](#3-project-scope)
4. [Objectives & Success Metrics](#4-objectives--success-metrics)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Data Sources & Lineage](#7-data-sources--lineage)
8. [Deliverables](#8-deliverables)
9. [Milestones & Phases](#9-milestones--phases)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [RACI — Roles & Responsibilities](#11-raci--roles--responsibilities)

---

## 1. Executive Summary

A plaintiff-side mass-tort and personal-injury law firm is operating with 2,743 active and historical matters across 10 case types, yet has no consolidated operational intelligence layer. Case managers work from disconnected spreadsheets. Managing partners review revenue performance quarterly, not in real time. SLA breaches go undetected until a client complaint surfaces. The records-acquisition bottleneck — a structural delay in the workup pipeline — has never been formally quantified.

This project delivers a **Legal Case Management Intelligence Platform**: a full-stack analytics solution comprising a normalized PostgreSQL data model, a library of operational KPI queries, Python-based predictive and forecasting models, and a multi-page BI dashboard (Power BI / Sigma). The platform transforms raw operational data into actionable intelligence for every stakeholder tier — from case manager daily workflow to executive pipeline valuation.

At snapshot date (2025-06-30), the platform surfaces an immediate concern: **only 60.8% of matters have completed workup**, mass-tort categories lag the firm average by 10–20 percentage points, and the 6-month new-matter demand forecast projects a seasonal trough of ~122 new matters in November 2025, signaling a capacity-planning window that the firm must address proactively. This BRD defines the requirements necessary to close those gaps.

---

## 2. Business Problem & Background

### 2.1 Background

The firm handles a diverse mix of personal-injury and mass-tort litigation, including Motor Vehicle Accidents (MVA), Premises Liability, Workers' Compensation, Slip & Fall, Nursing Home Abuse, Products Liability, Medical Malpractice, Roundup herbicide claims, Camp Lejeune water contamination claims, and Talcum powder claims. Each matter progresses through a defined workup funnel (Intake → Retainer Signed → Records Requested → Records Received → Workup Complete → Demand Sent → Negotiation → Resolved) before it can be presented for settlement or trial.

As of the snapshot date, the firm carries:
- **2,743 total matters** across 2,500 unique clients (40 duplicate client records were identified)
- **2,180 open matters** (79.5% of the book), representing substantial work-in-progress pipeline value
- **329 settlements** totaling **$30.17M** (average settlement: $91,709)
- **18 case managers** and **12 attorneys**

### 2.2 Business Problem Statement

The firm cannot answer its most critical operational questions with confidence:

| Business Question | Current State |
|---|---|
| Which matters are at risk of stalling before workup completion? | No systematic flagging; reliance on manager judgment |
| How many workups will complete over the next 6 months? | No forecast exists; capacity planning is reactive |
| Which case managers are over-capacity or under-performing? | No normalized productivity metric; no capacity-to-backlog comparison |
| Where do matters spend the most time, and why? | No stage-level time tracking beyond a single `days_in_stage` field |
| What is the expected revenue value of the open pipeline? | No pipeline valuation methodology |
| Which clients are duplicates, and what data is missing? | No data quality monitoring |

The downstream consequences are measurable: missed SLA thresholds result in client dissatisfaction; stalled records acquisition delays demand letters; undetected at-risk matters convert to dropped or closed-lost cases, representing direct revenue loss.

### 2.3 Strategic Alignment

This initiative aligns with three firm-wide strategic priorities:
1. **Revenue protection** — identify and rescue at-risk matters before they are dropped
2. **Operational efficiency** — eliminate manual, spreadsheet-based reporting; automate recurring KPI production
3. **Capacity management** — match intake growth to verifiable throughput capacity

---

## 3. Project Scope

### 3.1 In Scope

| # | Scope Item |
|---|---|
| S-01 | PostgreSQL data model: 9-table schema (3 dimensions, 1 core fact, 5 sub-facts) with FK integrity, indexes |
| S-02 | Synthetic data generation and loading (24-month history, 2023-07 to 2025-06) |
| S-03 | Data cleaning pipeline: deduplication, anomaly detection, null handling (Python/pandas) |
| S-04 | Core KPI query library: 9 KPI categories covering funnel, productivity, settlement economics, SLA, backlog, intake trends |
| S-05 | Dashboard queries (7 pages) optimized for Power BI / Sigma import |
| S-06 | Exploratory data analysis (EDA): intake trends, case mix, cycle time, funnel shape |
| S-07 | Time-series forecasting: monthly new-matter demand (cases opened per month), 6-month horizon, back-test MAPE 12.5% — target is the uncensored intake/demand series rather than completed-workup volume, which is right-censored near the snapshot date |
| S-08 | Binary classification model: workup completion prediction (Logistic Regression, 5-fold CV ROC-AUC 0.700 ± 0.020; test-set AUC 0.696), with leakage-safe feature set |
| S-09 | Multi-page BI dashboard: Executive Overview, Workup Funnel, Case Manager Productivity, Case Quality, Forecasting, Data Quality, Operational Bottleneck |
| S-10 | Documentation suite: BRD, KPI Dictionary, Data Dictionary, Process Flow, Stakeholder Requirements, Assumptions, Success Criteria, Executive Recommendations |

### 3.2 Out of Scope

| # | Out-of-Scope Item | Rationale |
|---|---|---|
| OS-01 | Production ETL / real-time data pipelines | Data engineering function; requires infrastructure decisions beyond BA scope |
| OS-02 | Integration with live case management system (e.g., Litify, Filevine) | Requires system access and IT project; this platform uses extracted data |
| OS-03 | Attorney performance evaluation for HR/compensation purposes | Sensitive; requires separate governance |
| OS-04 | Client-facing portal or communication tools | Product engineering scope |
| OS-05 | Legal document drafting automation | AI/legal-ops product scope |
| OS-06 | Trial outcome prediction | Insufficient resolved-trial sample size in current data |
| OS-07 | Financial accounting reconciliation | Finance system integration not in scope |

---

## 4. Objectives & Success Metrics

| Objective | Measurable Target | Measurement Method |
|---|---|---|
| O-1: Surface at-risk matters before they stall | 80%+ of stalling matters flagged 30+ days in advance | Recall of predictive model vs. actual dropout rate |
| O-2: Increase workup completion rate | From 60.8% to 68% within 12 months | Monthly KPI query on `cases.workup_completed` |
| O-3: Reduce SLA breach rate in Records stages | Records Requested and Records Received SLA compliance ≥ 75% | KPI-7 query on `cases.days_in_stage` vs. SLA target |
| O-4: Reduce missing-document rate | Average `missing_documents` per open matter < 1.0 | KPI query on `cases.missing_documents` |
| O-5: Eliminate duplicate client records | Duplicate client rate maintained ≤ 0.5% post-platform | Monthly deduplication scan |
| O-6: Enable pipeline valuation | Expected pipeline value calculated and updated monthly | Dashboard Page 1, query 1.3 |
| O-7: Reduce inactive-case rate | Open matters with 30+ day inactivity < 10% of open caseload | KPI-8 query |

---

## 5. Functional Requirements

### 5.1 Data Model Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The system shall maintain a single `cases` fact table as the authoritative source for all matter-level operational metrics. | Must Have |
| FR-02 | `cases.workup_completed` shall be a binary flag (1/0) set when a matter has progressed to stage "Workup Complete" or beyond. | Must Have |
| FR-03 | `cases.days_in_stage` shall represent calendar days elapsed in the current stage as of the snapshot date; negative values shall be treated as data quality errors and corrected to their absolute value or nulled. | Must Have |
| FR-04 | `cases.date_closed` shall be NULL for all open matters; closed matters shall have a non-null `date_closed` that is ≥ `date_opened`. | Must Have |
| FR-05 | The `settlements` sub-fact shall carry `attorney_fee`, `lien_amount`, `case_costs`, and `net_to_client` to support full economic decomposition. | Must Have |
| FR-06 | The `medical_records` table shall track `status` (Received / Outstanding) and `requested_date` to enable records-aging analysis. | Must Have |
| FR-07 | All FK relationships shall be enforced at the database level (PostgreSQL FK constraints). | Must Have |

### 5.2 KPI & Reporting Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-08 | The platform shall compute workup completion rate overall and by `case_type` using `cases.workup_completed`. | Must Have |
| FR-09 | Settlement rate shall be computed only on resolved matters (`case_status IN ('Settled','Closed-Lost','Dropped')`), not the total book. | Must Have |
| FR-10 | SLA compliance shall be computed per-stage using the fixed target-day thresholds defined in KPI-7; `days_in_stage < 0` rows shall be excluded. | Must Have |
| FR-11 | Case manager productivity shall be ranked firm-wide by completion rate and logged hours; capacity utilization shall compare open backlog to `case_managers.monthly_capacity`. | Must Have |
| FR-12 | The platform shall expose an "inactive matter" flag for open cases with `CURRENT_DATE - last_activity_date > 30`. | Must Have |
| FR-13 | Monthly intake volume shall be computed from `clients.intake_date` with MoM growth % and a 3-month rolling average. | Must Have |
| FR-14 | Expected pipeline value shall be calculated as: open cases by type × type-level average settlement × type-level historical settlement rate. | Should Have |

### 5.3 Predictive Model Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-15 | The binary workup-completion model shall use only pre-resolution features; `current_stage`, `case_status`, `case_outcome`, `settlement_amount`, `date_closed`, and `days_in_stage` shall be excluded to prevent data leakage. (`days_in_stage` is derived from the funnel stage index in the generator, making it conditionally dependent on the target — review finding C1.) | Must Have |
| FR-16 | The model shall output a probability score and binary flag for each matter, exportable to the dashboard at-risk queue. | Must Have |
| FR-17 | The model shall be validated on a held-out stratified test set (minimum 25% of records). | Must Have |
| FR-18 | The forecasting model shall produce a 6-month horizon for monthly new-matter demand (cases opened per month) with prediction intervals anchored on back-test error and widening with horizon. The target series is the uncensored demand series, not completed-workup volume, which is right-censored near the snapshot date and biases recent months downward. | Should Have |

### 5.4 Dashboard Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-19 | The Executive Overview page shall display: total cases, open cases, workup completion %, settlement rate %, total settlement value, and stalled case count as KPI tiles. | Must Have |
| FR-20 | The Workup Funnel page shall display a true funnel (cases at-or-beyond each stage), not a distribution of current stage. | Must Have |
| FR-21 | The Case Manager Productivity page shall include a rank-ordered scorecard with caseload, completion %, logged hours, and backlog-to-capacity ratio. | Must Have |
| FR-22 | The Data Quality page shall surface: missing email %, missing referral %, negative settlement count, negative `days_in_stage` count. | Should Have |
| FR-23 | The Forecasting page shall overlay actuals (2023-07 to 2025-06) with 6-month demand forecast and prediction interval bands that widen with horizon (not flat in-sample residuals). | Should Have |

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | Dashboard KPI queries shall return results in < 5 seconds on the full 2,743-row dataset. |
| NFR-02 | Accuracy | Predictive model 5-fold CV ROC-AUC shall be ≥ 0.68 on training folds; test-set AUC reported with CV context. Forecast MAPE shall be ≤ 15% on the back-test holdout period. |
| NFR-03 | Maintainability | All SQL queries shall be modular (CTE-based), documented with inline comments, and version-controlled in `/sql/`. |
| NFR-04 | Reproducibility | Python analysis scripts shall be self-contained with a `requirements.txt`; random seeds shall be set for reproducibility. |
| NFR-05 | Data Quality | The cleaning pipeline shall detect and log: duplicates, negative values, date-order violations, and null rates exceeding 5% on non-nullable fields. |
| NFR-06 | Documentation | All KPIs shall have a formal definition in the KPI Dictionary before dashboard publication. |
| NFR-07 | Portability | SQL shall target PostgreSQL 13+ dialect but avoid proprietary extensions that would prevent migration to other ANSI-compliant engines. |
| NFR-08 | Auditability | Each KPI output shall reference the source table(s), filter conditions, and snapshot date so results can be independently reproduced. |

---

## 7. Data Sources & Lineage

| Table | Row Count (Snapshot) | Source Layer | Primary Role |
|---|---|---|---|
| `clients` | 2,540 raw / 2,500 post-dedup | Dimension | Client demographics, intake date, marketing attribution |
| `attorneys` | 12 | Dimension | Attorney attributes; `years_experience` is a predictive feature |
| `case_managers` | 18 | Dimension | Staffing capacity; `monthly_capacity` drives backlog ratio |
| `cases` | 2,743 | Core Fact | All matter-level metrics; primary grain for KPIs and ML |
| `activities` | ~17,400 | Sub-Fact | Case manager time logs; feeds productivity KPI |
| `documents` | ~15,000 | Sub-Fact | Document completeness; status drives missing-doc KPI |
| `medical_records` | ~5,900 | Sub-Fact | Records-acquisition timing; drives bottleneck analysis |
| `settlements` | 329 | Sub-Fact | Full economic decomposition per resolved-settled matter |
| `call_logs` | ~15,000 | Sub-Fact | Communication volume and direction; context for engagement |

**Data generation:** All data is synthetic, generated by `python/generate_data.py` to reflect realistic plaintiff-firm operational distributions. See `documentation/assumptions.md` for all modeling assumptions.

---

## 8. Deliverables

| # | Deliverable | Format | Location |
|---|---|---|---|
| D-01 | Normalized schema (DDL) | SQL | `sql/01_create_tables.sql` |
| D-02 | Data loading script | SQL | `sql/02_load_data.sql` |
| D-03 | KPI query library | SQL | `sql/03_kpi_queries.sql` |
| D-04 | Dashboard query library | SQL | `sql/04_dashboard_queries.sql` |
| D-05 | Data quality query library | SQL | `sql/05_data_quality_queries.sql` |
| D-06 | Data cleaning pipeline | Python | `python/01_data_cleaning.py` |
| D-07 | Exploratory data analysis | Python + charts | `python/02_eda.py`, `python/outputs/eda_*.png` |
| D-08 | Forecasting model | Python + CSV | `python/03_forecasting.py`, `python/outputs/forecast_workup_volume.csv` |
| D-09 | Predictive model | Python + CSV | `python/04_predictive_model.py`, `python/outputs/predictions.csv` |
| D-10 | BI Dashboard (7 pages) | Power BI / Sigma | `dashboards/` |
| D-11 | Documentation suite (8 files) | Markdown | `documentation/` |

---

## 9. Milestones & Phases

| Phase | Name | Key Activities | Target Completion |
|---|---|---|---|
| 1 | Foundation | Schema design, synthetic data generation, DDL, data load | Week 1 |
| 2 | Data Quality | Cleaning pipeline, deduplication, anomaly repair, cleaning report | Week 2 |
| 3 | Analytics Core | KPI queries, EDA, dashboard query library | Week 3 |
| 4 | Advanced Analytics | Forecasting model, predictive model, feature engineering, model validation | Week 4 |
| 5 | Visualization | BI dashboard build (7 pages), chart export, layout review | Week 5 |
| 6 | Documentation & QA | Full documentation suite, cross-referencing, stakeholder review, final QA | Week 6 |

---

## 10. Risks & Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Predictive model trained on synthetic data may not generalize to real firm data | High | High | Document as assumption; re-train and re-validate model on live data before production deployment; treat current model as proof-of-concept |
| R-02 | Data leakage in ML model (outcome variables or proxy variables used as features) | Medium | Critical | Leakage columns explicitly excluded (see FR-15), including `days_in_stage` which is derived from funnel stage index in the synthetic generator (review finding C1); documented in `assumptions.md` and model output |
| R-03 | Duplicate client records inflate intake counts | High | Medium | Deduplication run at cleaning stage; 40 duplicates removed; monthly scan recommended |
| R-04 | SLA targets are assumed, not confirmed with firm leadership | Medium | Medium | SLA table defined in `03_kpi_queries.sql`; validation with Managing Partner is a Phase 6 action item |
| R-05 | `days_in_stage` reflects only current stage, not cumulative time per stage | Low | Medium | Documented as limitation; full stage-history table would require schema extension (out of scope) |
| R-06 | Forecast accuracy degrades beyond 3-month horizon | Medium | Low | Prediction intervals widen with horizon (not flat); back-test MAPE of 12.5% (MAE 15.8 matters/month) disclosed; horizon constrained to 6 months; one-time marketing-driven surge in history cannot be fully captured by trend+seasonal model |
| R-07 | Negative settlement amounts (8 records) indicate data entry errors | High | Low | Corrected to absolute value in cleaning pipeline; flagged in data quality dashboard |
| R-08 | Dashboard refresh cycle not yet defined (static snapshot vs. live) | Medium | Medium | Dashboard designed for snapshot use; live refresh requires ETL pipeline (out of scope, OS-01) |

---

## 11. RACI — Roles & Responsibilities

**R** = Responsible | **A** = Accountable | **C** = Consulted | **I** = Informed

| Activity | Managing Partner | Director of Operations | Case Mgr Supervisors | Intake Team Lead | IT / Data | Finance | BA / Analyst |
|---|---|---|---|---|---|---|---|
| Define business objectives | A | C | C | I | I | C | R |
| Approve project scope | A | C | I | I | I | I | R |
| Define KPI metrics & targets | C | A | C | C | I | C | R |
| Schema design & data model | I | C | I | I | A | I | R |
| Data cleaning & quality review | I | C | I | I | A | I | R |
| Build KPI queries | I | C | C | I | C | I | R |
| Build forecasting model | I | A | C | I | C | C | R |
| Build predictive model | I | A | C | I | C | I | R |
| Build BI dashboard | I | C | C | C | A | I | R |
| Validate KPI definitions | C | A | R | R | I | C | R |
| Approve SLA targets | A | C | C | I | I | I | C |
| Approve final deliverables | A | C | I | I | C | C | R |
| Communicate findings to firm | A | R | I | I | I | I | C |
| Monitor KPIs post-launch | I | A | R | R | C | I | I |

---

*Cross-references: See `documentation/kpi_dictionary.md` for metric definitions, `documentation/data_dictionary.md` for schema details, `documentation/assumptions.md` for all stated assumptions, and `documentation/success_criteria.md` for acceptance criteria.*
