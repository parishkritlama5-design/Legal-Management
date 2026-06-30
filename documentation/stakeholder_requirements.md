# Stakeholder Requirements
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Snapshot Date:** 2025-06-30  
**Prepared by:** Strategic Operations Business Analyst

---

## 1. Purpose

This document defines the stakeholder register for the Legal Case Management Intelligence Platform. For each stakeholder group, it specifies: organizational role, interests and priorities, the specific business questions they need the platform to answer, the analytical outputs that serve those questions, and any constraints or sensitivities relevant to their engagement.

Stakeholder requirements were derived from the operational context described in the BRD, observed data patterns at snapshot date, and standard legal-operations stakeholder engagement frameworks. All requirements are assumptions pending formal stakeholder validation sessions (see `documentation/assumptions.md`, A-09).

---

## 2. Stakeholder Register

### 2.1 Managing Partner

| Attribute | Detail |
|---|---|
| **Role** | Senior equity partner; firm governance and strategic direction. Ultimate accountability for revenue performance and firm reputation. |
| **Level of Influence** | High — final approver on platform scope, resource allocation, and executive reporting cadence. |
| **Level of Interest** | Medium (strategic, not operational) — interested in aggregate performance and financial outcomes, not individual CM activity. |
| **Primary Interests** | Revenue generated (settlement value and rate), pipeline health, intake growth vs. capacity, firm-wide completion throughput, and strategic risk (mass-tort case lag). |
| **Communication Preference** | High-level summary dashboard; monthly executive brief; exception-based alerts for significant anomalies. |

**Key Questions the Platform Must Answer:**

| # | Business Question | Platform Answer |
|---|---|---|
| MP-01 | What is the total settlement value and settlement rate for the current and prior periods? | Executive Overview KPI tiles: `total_settlement_value` ($30.17M), `settlement_rate_pct` (57.8%) — KPI-02, KPI-03 |
| MP-02 | What is the estimated value of the open pipeline, and how does it break down by case type? | Expected Pipeline Value (KPI-12); dashboard query 1.3 by case type |
| MP-03 | Is the firm completing workups fast enough relative to intake volume? | Forecasting Page: intake vs. completion capacity gap chart (query 5.2); 6-month forecast (KPI-09) |
| MP-04 | Which case types are underperforming and represent the greatest risk to revenue? | Workup Funnel page: completion rate by type (KPI-01); mass-tort lag visible |
| MP-05 | How many matters are stalled, and what is the financial exposure? | Executive Overview: stalled case count tile; expected value of at-risk matters |
| MP-06 | What does incoming caseload look like over the next 6 months, and how should we plan capacity? | Forecasting page: 6-month new-matter demand forecast with widening prediction intervals (Jul-Dec 2025: ~162, 157, 147, 154, 122, 127 new matters/month; November is the seasonal trough) |

**Serving Dashboard/Report:** Executive Overview (Page 1), Forecasting Dashboard (Page 5)

**Sensitivities:** Attorney-level performance data should not be surfaced in the Managing Partner view without prior governance agreement; individual attorney metrics are appropriate for the attorney's direct supervisor, not the partner dashboard.

---

### 2.2 Director of Operations

| Attribute | Detail |
|---|---|
| **Role** | Responsible for day-to-day firm operations: case manager team performance, process compliance, SLA management, and throughput optimization. |
| **Level of Influence** | High — primary day-to-day owner of platform KPIs; drives operational responses to dashboard findings. |
| **Level of Interest** | High — uses the platform daily or weekly to manage throughput and identify bottlenecks. |
| **Primary Interests** | Workup completion rate trend, SLA compliance by stage, case manager backlog and capacity, records acquisition bottleneck, inactive matters, and mass-tort case health. |
| **Communication Preference** | Full multi-page dashboard access; weekly operational review meeting supported by dashboard exports; exception-based email alerts for SLA breaches > 20% non-compliant in any stage. |

**Key Questions the Platform Must Answer:**

| # | Business Question | Platform Answer |
|---|---|---|
| DO-01 | Which stages of the workup funnel have the most cases stuck, and how long have they been there? | Operational Bottleneck page (query 7.1): open count and avg days by stage |
| DO-02 | What are the SLA compliance rates per stage, and where are we breaching targets? | KPI-07 query; SLA compliance bar chart on Bottleneck page |
| DO-03 | Which case managers are over-capacity, and which have the lowest completion rates? | Case Manager Productivity page (queries 3.1, KPI-06): backlog-to-capacity ratio, completion rank |
| DO-04 | How many medical records requests are outstanding, and how long have they been pending? | Operational Bottleneck page (query 7.2): outstanding records count and avg days outstanding |
| DO-05 | Which matters are inactive and for how long? | KPI-08: inactive matter list with 30/60/90-day buckets; stalled rank within CM |
| DO-06 | Are there systemic data quality issues affecting our reporting? | Data Quality page (query 6.1): missing email %, negative values, missing referral % |
| DO-07 | Where is the intake-to-completion gap widest? | Forecasting page (query 5.2): monthly intake vs. completed workups capacity-gap chart |

**Serving Dashboard/Report:** All 7 dashboard pages; primary user of Operational Bottleneck (Page 7), Case Manager Productivity (Page 3), and Data Quality (Page 6)

**Sensitivities:** Director of Operations requires disaggregated case manager data. Agree on whether individual CM scorecards are shared with the full team or only with supervisors and the Director.

---

### 2.3 Case Manager Supervisors

| Attribute | Detail |
|---|---|
| **Role** | Team leads who directly supervise 4–6 case managers each. Responsible for individual CM coaching, workload balancing, and escalation of stalled matters. |
| **Level of Influence** | Medium — drive operational responses within their team but do not set firm-wide policy. |
| **Level of Interest** | High — use the platform weekly to manage their team's active caseload. |
| **Primary Interests** | Individual CM performance (completion rate, logged hours, backlog), at-risk matter queue for their team, inactive matters by CM, and missing-document flags. |
| **Communication Preference** | Filtered dashboard view for their team's case managers; weekly 1:1 review supported by CM scorecard; alert queue for at-risk or 30+-day inactive matters. |

**Key Questions the Platform Must Answer:**

| # | Business Question | Platform Answer |
|---|---|---|
| CS-01 | Which of my case managers have the highest backlog relative to their capacity? | KPI-06 (Backlog-to-Capacity Ratio); Case Manager Productivity page |
| CS-02 | Which specific matters are flagged as at-risk of not completing workup? | Predictive model output (`predictions.csv`); at-risk queue on Page 3 |
| CS-03 | Which matters have been inactive for 30+ days, and who owns them? | KPI-08: inactive matter list with `staleness_rank_in_cm` per CM |
| CS-04 | How does each CM's completion rate compare to the firm average? | CM scorecard with `completion_rank` (RANK() window function); KPI-05 |
| CS-05 | Which cases have the most missing documents, and why? | KPI-10 / Case Quality page (query 4.1): avg missing docs by CM and type |
| CS-06 | Which matters are stuck in the records stages and need escalation? | KPI-06 `stuck_in_records` metric; Bottleneck page stage distribution |

**Serving Dashboard/Report:** Case Manager Productivity (Page 3), Operational Bottleneck (Page 7), Case Quality Analytics (Page 4)

**Sensitivities:** Individual CM performance rankings should be framed in context of case-type mix. A supervisor managing mass-tort-heavy CMs will see structurally lower team completion rates. Rankings should be normalized by case type before use in formal evaluations (see `documentation/assumptions.md`, A-10).

---

### 2.4 Intake Team Lead

| Attribute | Detail |
|---|---|
| **Role** | Manages the intake process: new client registration, referral source tracking, initial retainer execution, and early-stage documentation. Responsible for data quality at the point of entry. |
| **Level of Influence** | Medium — controls data quality at intake; does not control downstream case management. |
| **Level of Interest** | Medium — focused on intake volume, referral source effectiveness, and data quality metrics (duplicate rate, missing email/referral). |
| **Primary Interests** | Intake volume and growth trends, referral source conversion rates (which channels produce completed workups), duplicate client detection, and missing email / referral source rates. |
| **Communication Preference** | Monthly intake volume report; data quality scorecard; weekly duplicate alert if threshold exceeded. |

**Key Questions the Platform Must Answer:**

| # | Business Question | Platform Answer |
|---|---|---|
| IT-01 | How many new clients did we intake this month, and how does it compare to the prior month? | KPI-09: monthly intake with MoM growth %; rolling 3-month average |
| IT-02 | Which referral sources and marketing channels produce the highest workup completion rates? | Workup Funnel page (query 2.2): completion % by referral source |
| IT-03 | How many duplicate client records were detected, and what is the current duplicate rate? | KPI-11: duplicate count and rate; Data Quality page |
| IT-04 | What percentage of clients are missing email addresses or referral sources? | Data Quality page (query 6.1): `pct_clients_missing_email`, `pct_clients_missing_referral` |
| IT-05 | Are intake volumes growing, and is the trend sustainable? | Forecasting page (query 5.2): intake vs. completion capacity gap |

**Serving Dashboard/Report:** Forecasting Dashboard (Page 5, intake trend), Data Quality (Page 6), Workup Funnel (Page 2, referral-source completion)

**Sensitivities:** Intake Team Lead owns the data entry process; Data Quality findings should be presented as process improvement opportunities, not individual blame. Agree on remediation ownership before surfacing error rates in firm-wide meetings.

---

### 2.5 IT / Data Team

| Attribute | Detail |
|---|---|
| **Role** | Responsible for the database infrastructure, data pipeline, schema maintenance, dashboard tooling, and any future ETL integration with the live case management system (Litify, Filevine, or equivalent). |
| **Level of Influence** | High for technical decisions; low for business metric definitions. |
| **Level of Interest** | Medium — interested in schema integrity, query performance, data refresh cadence, and maintainability of the analytics codebase. |
| **Primary Interests** | Schema design and FK integrity, index performance, data quality anomaly patterns (negative values, date violations), refresh cycle feasibility, and portability/maintainability of the SQL and Python codebase. |
| **Communication Preference** | Technical documentation (data dictionary, DDL, requirements), direct code review access, and data quality anomaly reports. |

**Key Questions the Platform Must Answer:**

| # | Business Question | Platform Answer |
|---|---|---|
| IT-T01 | Is the schema designed to support query performance at 2,000–10,000+ matters without full table scans? | DDL: 5 targeted indexes on `cases`; CTE-based queries avoid Cartesian joins; documented in `sql/01_create_tables.sql` |
| IT-T02 | What data quality rules need to be enforced at the ETL layer to prevent dirty data from reaching the dashboard? | Data Dictionary (nullable rules, constraint notes); cleaning pipeline logic in `python/01_data_cleaning.py` |
| IT-T03 | Can the SQL run on standard PostgreSQL without proprietary extensions? | NFR-07: ANSI-compatible dialect; no proprietary functions used |
| IT-T04 | How are the Python models structured for reproducibility? | `requirements.txt` in `python/`; fixed random seeds in `04_predictive_model.py` |
| IT-T05 | What is the recommended refresh cadence, and what triggers a full re-run vs. incremental? | Dashboard is snapshot-based; full refresh recommended monthly; incremental ETL is out of current scope (OS-01) |

**Serving Dashboard/Report:** Data Dictionary (`documentation/data_dictionary.md`), DDL (`sql/01_create_tables.sql`), Python source files (`python/`), Data Quality page (Page 6)

**Sensitivities:** IT team will flag if schema changes required by future business requirements conflict with downstream dashboard queries. Schema versioning and change management process should be established before production deployment.

---

### 2.6 Finance Team

| Attribute | Detail |
|---|---|
| **Role** | Responsible for settlement disbursement, attorney fee accounting, lien resolution, and revenue recognition. Relies on settlement data to reconcile firm financial statements. |
| **Level of Influence** | Low for operational KPIs; High for financial metric definitions and settlement accounting. |
| **Level of Interest** | Medium — interested in settlement economics, net-to-client figures, attorney fee totals, and expected revenue pipeline. |
| **Primary Interests** | Gross settlement value, attorney fees, lien amounts, case costs, net-to-client disbursements, and expected pipeline revenue by case type. |
| **Communication Preference** | Monthly settlement summary; expected pipeline value report; exception alerts for settlements with negative or anomalous values. |

**Key Questions the Platform Must Answer:**

| # | Business Question | Platform Answer |
|---|---|---|
| FI-01 | What is the total gross settlement value, and how does it break down by case type? | KPI-03: total settlement value ($30.17M, 329 settlements); avg settlement ($91,709) |
| FI-02 | What is the expected revenue value of the current open pipeline? | KPI-12: expected pipeline value by case type (query 1.3) |
| FI-03 | What is the average attorney fee, lien obligation, and net-to-client per settled matter? | `settlements` table: `attorney_fee`, `lien_amount`, `case_costs`, `net_to_client` columns; Case Quality page (query 4.2) |
| FI-04 | Are there any settlement amount anomalies (negative values, settled without amount)? | Data Quality page (query 6.1): `negative_settlements` count, `settled_without_amount` count |
| FI-05 | What is the month-over-month trend in settled matters and settlement value? | Not currently in KPI set — recommended as a Phase 2 addition (settlement velocity trend) |

**Serving Dashboard/Report:** Executive Overview (Page 1, settlement KPI tiles), Case Quality Analytics (Page 4, settlement value scatter), Data Quality (Page 6, anomaly counts)

**Sensitivities:** Finance team requires that the platform's settlement figures reconcile with their accounting system before the platform is used for financial reporting. Platform settlement data is derived from `cases.settlement_amount` (cleaned) and `settlements` table — reconciliation against source financial system is required before revenue-recognition use.

---

## 3. Stakeholder Influence / Interest Matrix

```
HIGH INFLUENCE
      |
      |  IT / Data -------- Director of Operations
      |  (Tech decisions)   (Operational KPIs)
      |
      |  Managing Partner
      |  (Strategy/Revenue)
      |
      |         Finance ---- Case Mgr Supervisors
      |         (Settlement) (Team mgmt)
      |
      |                Intake Team Lead
      |                (Data entry quality)
LOW INFLUENCE
      |__________________________|
      LOW INTEREST          HIGH INTEREST
```

| Stakeholder | Influence | Interest | Engagement Strategy |
|---|---|---|---|
| Managing Partner | High | Medium | Monthly executive dashboard review; exception alerts only |
| Director of Operations | High | High | Full dashboard access; weekly operational review |
| Case Mgr Supervisors | Medium | High | Filtered team view; weekly at-risk queue review |
| Intake Team Lead | Medium | Medium | Monthly intake/data quality report |
| IT / Data | High | Medium | Technical documentation; change management process |
| Finance | Low | Medium | Monthly settlement summary; pipeline value report |

---

## 4. Stakeholder Sign-Off Requirements

| Stakeholder | Sign-Off Required On |
|---|---|
| Managing Partner | Project scope (BRD); KPI targets; dashboard design (executive page) |
| Director of Operations | KPI definitions and targets; SLA thresholds; dashboard page layout |
| Case Mgr Supervisors | CM productivity scorecard format; at-risk queue design |
| Intake Team Lead | Intake KPI definitions; referral source value list; data quality thresholds |
| IT / Data | Schema DDL; index design; refresh cadence |
| Finance | Settlement KPI definitions; settlement amount reconciliation protocol |

---

*Cross-references: `documentation/business_requirements_document.md` (RACI table, Section 11), `documentation/kpi_dictionary.md` (KPI owners per metric), `documentation/success_criteria.md` (how each stakeholder measures success), `documentation/assumptions.md` (A-09: stakeholder requirements are assumed pending validation).*
