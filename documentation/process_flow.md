# Process Flow Documentation
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Snapshot Date:** 2025-06-30  
**Prepared by:** Strategic Operations Business Analyst  
**Scope:** Client intake through matter resolution — current state vs. future state

---

## 1. Overview

This document maps the end-to-end legal matter lifecycle for a plaintiff-side personal-injury and mass-tort law firm. It contrasts the **current-state process** (pre-platform) with the **future-state process** enabled by the Legal Case Management Intelligence Platform, and provides a structured gap analysis.

The firm's workup funnel defines eight sequential stages:

```
Intake → Retainer Signed → Records Requested → Records Received
      → Workup Complete → Demand Sent → Negotiation → Resolved
```

As of the 2025-06-30 snapshot, only **60.8%** of 2,743 matters have completed the workup milestone. The analytics platform provides the operational visibility needed to increase that rate to 68% within 12 months.

---

## 2. Current-State Process (Pre-Platform)

### 2.1 High-Level Flow

```
[Lead / Referral]
      |
      v
[Intake Team: Phone / Web Form]
      |
      |--- Duplicate check: MANUAL (staff checks spreadsheet)
      |--- Client data entry: MANUAL (case mgmt system)
      |
      v
[Retainer Execution]
      |
      |--- Retainer sent: Email / DocuSign
      |--- Tracking: MANUAL (individual CM spreadsheet)
      |
      v
[Records Acquisition Phase]                     <<< PRIMARY BOTTLENECK >>>
      |
      |--- Records Requested: CM submits requests individually
      |--- Provider follow-up: MANUAL, ad hoc, no aging alerts
      |--- Records Received: CM notes receipt in case system
      |--- No automated escalation if provider is non-responsive
      |
      v
[Workup Assembly]
      |
      |--- CM reviews records, identifies gaps
      |--- Missing documents: flagged in personal notes or CM-local spreadsheet
      |--- No firmwide missing-document visibility
      |
      v
[Workup Complete / QC]
      |
      |--- Attorney reviews CM's workup summary
      |--- No standardized quality checklist
      |--- Approval: verbal or email confirmation
      |
      v
[Demand Letter Preparation]
      |
      |--- Attorney or paralegal drafts demand
      |--- Sent to opposing counsel / insurer
      |
      v
[Negotiation]
      |
      |--- Opposing counsel responds (timing: highly variable)
      |--- CM and attorney coordinate offer/counter
      |--- No centralized offer-tracking
      |
      v
[Resolution: Settled / Dismissed / Dropped]
      |
      |--- Settlement disbursement: Finance processes manually
      |--- Reporting: Quarterly Excel summary to Managing Partner
```

### 2.2 Current-State Pain Points

| # | Pain Point | Stage Affected | Business Impact |
|---|---|---|---|
| P-01 | **No real-time operational dashboard.** Managing Partner receives a quarterly Excel summary. Stalling matters are not identified until they become client complaints. | All stages | Revenue leakage from dropped/dismissed matters; reactive management |
| P-02 | **Duplicate client detection is manual.** Staff may create duplicate client records; no automated deduplication. 40 duplicates detected in snapshot data (1.6% raw rate). | Intake | Inflated intake counts; misdirected communications; compliance risk |
| P-03 | **Records acquisition has no SLA enforcement.** Providers routinely take 30–90+ days to respond; case managers have no firm-level alert system when requests age beyond thresholds. | Records Requested / Records Received | Pipeline stalls; cases linger in the most common bottleneck stage |
| P-04 | **Missing document tracking is CM-local.** Each case manager maintains their own list; no firmwide missing-document visibility. Supervision requires ad hoc one-on-one check-ins. | Records Received / Workup Complete | Supervisors cannot identify systemic document gaps; quality inconsistency |
| P-05 | **Case manager capacity is unmonitored.** No mechanism to compare open caseload to stated capacity; no early warning of overload. | All active stages | Burnout risk; uneven workload distribution; throughput degradation |
| P-06 | **At-risk matters are invisible.** No predictive flag for cases likely to stall or not complete workup. Triage is reactive — managers escalate when things are already overdue. | All pre-resolution stages | Preventable case losses; no proactive client communication |
| P-07 | **Mass-tort cases have no specialized monitoring.** Completion rates for Camp Lejeune (43.9%) and Talcum (41.3%) are 20 points below firm average, but no operational report surfaces this gap. | All stages (mass tort) | Significant revenue at risk; mass-tort intake growing without throughput to match |
| P-08 | **Intake-to-capacity gap is invisible.** The firm cannot compare new intake volume against workup throughput to identify whether new matters outpace the firm's ability to close them. | Intake / Forecasting | Unsustainable pipeline growth; backlog accumulation |
| P-09 | **Settlement economics are not tracked per matter.** Net-to-client, attorney fees, lien amounts, and case costs exist in separate spreadsheets, not linked to matter records. | Resolution | Inability to model average case economics; Finance operates in silo |
| P-10 | **Inactive matters have no alert.** A matter can go 60–90+ days without activity without triggering any alert to supervisors. | All active stages | Client dissatisfaction; statute of limitations risk (in extreme cases) |

---

## 3. Future-State Process (Post-Platform)

### 3.1 High-Level Flow

```
[Lead / Referral / Web Form / Broadcast Ad]
      |
      v
[Intake Team: Phone / Web Intake]
      |
      |--- Auto-dedup check: Python cleaning pipeline flags matches
      |    on name + DOB + phone before record creation
      |--- Marketing channel + referral source captured at intake
      |--- Client entered into `clients` table; case opened in `cases`
      |
      v
[Retainer Execution]
      |
      |--- DocuSign workflow initiated; `cases.current_stage` = 'Retainer Signed'
      |--- SLA clock starts: target = 5 days from Intake
      |--- DASHBOARD ALERT: Intake SLA tile turns amber at Day 3, red at Day 5
      |
      v
[Records Acquisition Phase]                     <<< MONITORED BOTTLENECK >>>
      |
      |--- Records Requested: CM submits; `cases.current_stage` = 'Records Requested'
      |--- `medical_records` row created per provider; `status` = 'Outstanding'
      |--- SLA: 30 days target; aging query (dashboard 7.2) flags outstanding records
      |--- DASHBOARD ALERT: Records aging > 21 days triggers case manager alert queue
      |--- Records Received: `medical_records.status` → 'Received'
      |    `cases.medical_records_received` = 1
      |--- Missing documents: `documents` table updated; `cases.missing_documents` count synced
      |--- DASHBOARD: Missing document rate by CM visible in real time (KPI-10)
      |
      v
[Workup Assembly — Analytics-Assisted]
      |
      |--- PREDICTIVE FLAG: Model scores each open matter for workup completion probability
      |    (Logistic Regression, 5-fold CV AUC 0.700 ± 0.020, test AUC 0.696;
      |     184/686 test cases flagged at-risk; top drivers: missing_documents,
      |     medical_records_received, communication_count, attorney experience)
      |--- At-risk queue surfaced to Case Manager Supervisors on dashboard page 3
      |--- CM resolves gaps; `cases.communication_count` incremented per touchpoint
      |--- `activities` logged per CM action; `call_logs` capture client contacts
      |
      v
[Workup Complete / QC]
      |
      |--- `cases.workup_completed` = 1; `cases.current_stage` = 'Workup Complete'
      |--- Attorney review triggered; SLA: 14 days
      |--- DASHBOARD: Workup completion rate updates on Executive Overview tile
      |
      v
[Demand Letter Preparation & Negotiation]
      |
      |--- Demand sent: `cases.current_stage` = 'Demand Sent'; SLA: 21 days
      |--- Negotiation: `cases.current_stage` = 'Negotiation'; SLA: 45 days
      |--- DASHBOARD: Stage-level SLA compliance rates visible (KPI-07)
      |
      v
[Resolution]
      |
      |--- Settled: `settlements` record created with full economic breakdown
      |    (`attorney_fee`, `lien_amount`, `case_costs`, `net_to_client`)
      |--- `cases.settlement_amount` updated; `cases.case_status` = 'Settled'
      |--- DASHBOARD: Total settlement value, avg settlement, settlement rate update (KPI-02/03)
      |
      v
[Executive Reporting — Automated]
      |
      |--- Managing Partner reviews Executive Overview page: 7 KPI tiles, pipeline value
      |--- 6-month new-matter demand forecast available (MAPE 12.5%, MAE 15.8/month)
      |    Jul-Dec 2025: ~162, 157, 147, 154, 122, 127 new matters/month
      |--- No quarterly Excel required; dashboard is always current to snapshot refresh
```

### 3.2 Future-State Process by Stage

#### Stage 1: Intake

| Attribute | Current State | Future State |
|---|---|---|
| Duplicate detection | Manual spreadsheet check | Automated dedup on name + DOB + phone in cleaning pipeline |
| Data capture | Variable; inconsistent referral source capture | Standardized fields; `marketing_channel` and `referral_source` captured at creation |
| SLA monitoring | None | SLA timer starts at `date_opened`; dashboard alert at 3-day threshold |
| Intake trend visibility | Quarterly | Real-time MoM growth chart (KPI-09) |

#### Stage 2: Records Acquisition

| Attribute | Current State | Future State |
|---|---|---|
| Provider tracking | CM-local list | `medical_records` table: one row per provider request; status tracked |
| Aging alerts | None | Dashboard query 7.2: avg days outstanding for `Outstanding` records |
| SLA compliance | Not measured | KPI-07: Records Requested (30-day) and Records Received (21-day) compliance rates |
| Missing document visibility | CM-local | KPI-10: firmwide missing-document rate; drill-down by case manager and case type |

#### Stage 3: Workup Assembly

| Attribute | Current State | Future State |
|---|---|---|
| At-risk identification | Reactive (supervisor flags) | Predictive model scores each matter; at-risk queue in dashboard |
| Communication tracking | Email/phone; unstructured | `call_logs` and `activities` tables; `communication_count` on `cases` |
| Quality checkpoint | Informal review | Case Quality dashboard (query 4.1): % records received, avg missing docs, % high-quality |

#### Stage 4–5: Demand & Negotiation

| Attribute | Current State | Future State |
|---|---|---|
| SLA monitoring | None | KPI-07: Demand Sent (21-day) and Negotiation (45-day) compliance |
| Inactivity alerts | None | KPI-08: Inactive matter flag at 30-day threshold; stalled-case tile on Executive Overview |

#### Stage 6: Resolution

| Attribute | Current State | Future State |
|---|---|---|
| Financial tracking | Separate Finance spreadsheet | `settlements` table: full economic decomposition per matter |
| Settlement rate reporting | Quarterly | Real-time settlement rate and average settlement value on Executive Overview |
| Pipeline valuation | Not calculated | Expected pipeline value by case type (KPI-12, query 1.3) |

---

## 4. Gap Analysis

| Gap ID | Gap Description | Current State Metric | Future-State Target | Platform Component |
|---|---|---|---|---|
| G-01 | Real-time operational dashboard | Quarterly Excel summary | Daily/weekly dashboard refresh | 7-page Power BI / Sigma dashboard |
| G-02 | Workup completion visibility by type | Unknown at operational level | Completion rate by type tracked weekly | KPI-01, dashboard Page 2 |
| G-03 | Mass-tort workup lag | Unidentified | Camp Lejeune and Talcum completion rates closed within 10 pts of firm avg | KPI-01 drill-down; Executive Recommendations |
| G-04 | Records acquisition bottleneck | Not quantified | Records SLA compliance ≥ 75% | KPI-07, dashboard Page 7 |
| G-05 | At-risk matter identification | Reactive | 80%+ of stalling matters flagged 30+ days before drop | Predictive model; at-risk queue on Page 3 |
| G-06 | Case manager capacity monitoring | Not tracked | Backlog-to-capacity ratio monitored monthly | KPI-06, dashboard Page 3 |
| G-07 | Duplicate client detection | Manual; 1.6% rate | ≤ 0.5% ongoing duplicate rate | Python cleaning pipeline; KPI-11 |
| G-08 | 6-month new-matter demand forecast | None | Demand forecast with MAPE ≤ 15%; widening prediction intervals; targets uncensored demand series | Forecasting model; dashboard Page 5 |
| G-09 | Settlement economic decomposition | Finance silo | Net-to-client tracked per matter | `settlements` table; Case Quality page |
| G-10 | Expected pipeline value | Not calculated | Pipeline value by case type, updated with each refresh | KPI-12, dashboard Page 1 |
| G-11 | Inactive matter alerts | None | < 10% of open caseload inactive > 30 days | KPI-08; Executive Overview stalled tile |
| G-12 | Intake-to-capacity gap visibility | None | Monthly new-matter demand vs. workup throughput capacity gap chart | Forecasting page, query 5.2 |

---

## 5. Process Performance Summary

| Metric | Current State (Snapshot) | Future-State Target |
|---|---|---|
| Workup completion rate | 60.8% | 68% within 12 months |
| Mass-tort completion rate (avg, Talcum + Camp Lejeune) | ~42.6% | 55% within 18 months |
| Records Requested SLA compliance | Not measured | ≥ 75% |
| At-risk matters flagged proactively | 0 | 184 flagged (test set, post leakage-fix); ongoing model scoring |
| Inactive cases (30+ days) | Not monitored | < 10% of open caseload |
| Duplicate client rate | 1.6% (raw) | ≤ 0.5% ongoing |
| Time to executive reporting | Quarterly | Dashboard refresh cycle (weekly/monthly) |

---

*Cross-references: `documentation/kpi_dictionary.md` (KPI definitions), `documentation/business_requirements_document.md` (functional requirements FR-08 through FR-18), `documentation/executive_recommendations.md` (specific recommendations from gap analysis), `sql/04_dashboard_queries.sql` (dashboard query implementations).*
