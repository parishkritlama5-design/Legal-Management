# Data Dictionary
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Snapshot Date:** 2025-06-30  
**Prepared by:** Strategic Operations Business Analyst  
**Database:** PostgreSQL 13+ | **Schema:** `public`

---

## Schema Overview

The data model uses a star-ish operational design:

```
Dimensions       Core Fact       Sub-Facts
-----------      ---------       ---------
clients    ───┐
attorneys  ───┼──► cases ────► activities
case_mgrs  ───┘          ├──► documents
                         ├──► medical_records
                         ├──► settlements
                         └──► call_logs
```

| Layer | Tables | Row Count (Snapshot) |
|---|---|---|
| Dimension | `clients`, `attorneys`, `case_managers` | 2,500 / 12 / 18 |
| Core Fact | `cases` | 2,743 |
| Sub-Fact | `activities`, `documents`, `medical_records`, `settlements`, `call_logs` | ~17.4k / ~15k / ~5.9k / 329 / ~15k |

**Schema DDL:** `sql/01_create_tables.sql`  
**Data loading:** `sql/02_load_data.sql`  
**Cleaned exports:** `data/processed/clients_clean.csv`, `data/processed/cases_clean.csv`

---

## Table 1: `clients`

**Description:** Client dimension. One row per unique client. Raw load contains 2,540 rows; 40 duplicates removed during cleaning to produce 2,500 unique clients. Duplicate detection uses identity key: `last_name + first_name + date_of_birth + phone`.

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `client_id` | `VARCHAR(12)` | No | PK | Surrogate identifier for the client, assigned at intake. Format: alphanumeric. | `CLI-000001` | Natural key candidate: name + DOB + phone. |
| `first_name` | `VARCHAR(60)` | No | — | Client's legal first name as recorded at intake. | `Maria` | May not match ID; not used as join key. |
| `last_name` | `VARCHAR(60)` | No | — | Client's legal last name. | `Gonzalez` | Used in duplicate identity key. |
| `date_of_birth` | `DATE` | No | — | Client's date of birth in ISO 8601 format. | `1978-04-12` | Used in duplicate identity key; required for injury-claim eligibility. |
| `gender` | `VARCHAR(2)` | No | — | Client's self-identified gender code. Values observed: `M`, `F`. | `F` | Binary values in current synthetic dataset; may expand in production. |
| `state` | `CHAR(2)` | No | — | Two-letter U.S. state abbreviation of client's residence. | `TX` | Used for jurisdictional case-type eligibility analysis. |
| `phone` | `VARCHAR(20)` | No | — | Client's primary contact phone number. | `(512) 555-0147` | Used in duplicate identity key. Format not normalized. |
| `email` | `VARCHAR(120)` | **Yes** | — | Client's email address. Approximately 3% null (~76 records in snapshot). | `mgonzalez@email.com` | Nullable by design; missing rate tracked in data quality KPI-11. |
| `intake_date` | `DATE` | No | — | Date the client was first registered with the firm. | `2024-03-15` | Used for intake volume KPI-09 (`MoM Growth`). NOT NULL enforced. |
| `referral_source` | `VARCHAR(40)` | **Yes** | — | How the client was referred to the firm. ~50 records imputed to 'Unknown' during cleaning. Values: `TV Advertising`, `Attorney Referral`, `Web Search`, `Unknown`, etc. | `TV Advertising` | Nullable. Imputed to `'Unknown'` in clean dataset. Used in funnel-by-referral query. |
| `marketing_channel` | `VARCHAR(30)` | No | — | Marketing channel through which client was acquired. Values: `Broadcast`, `Paid Search`, `Organic`, `Referral`, `Direct`. | `Broadcast` | Used as feature in predictive model. |

**Data Quality Notes:**
- 40 duplicate records removed; merged into earliest `client_id` by identity key.
- 76 records (3.0%) have null `email` — tracked via KPI-10/11.
- 50 records had null `referral_source` — imputed to `'Unknown'` in `clients_clean.csv`.

---

## Table 2: `attorneys`

**Description:** Attorney dimension. One row per attorney at the firm. 12 attorneys in snapshot. Used for case assignment and as a source of predictive features (`years_experience`).

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `attorney_id` | `VARCHAR(12)` | No | PK | Surrogate identifier for the attorney. | `ATT-001` | Referenced as FK in `cases.attorney_id`. |
| `attorney_name` | `VARCHAR(120)` | No | — | Full legal name of the attorney. | `James R. Whitfield` | Display field; not used as join key. |
| `bar_state` | `CHAR(2)` | No | — | U.S. state in which attorney is primarily bar-admitted. | `TX` | May differ from `cases.state`; multi-state bar admissions not modeled. |
| `specialty` | `VARCHAR(40)` | No | — | Attorney's primary practice specialty. Values: `Personal Injury`, `Mass Tort`, `Workers Compensation`. | `Mass Tort` | Used for capacity planning and case-type routing. |
| `years_experience` | `INTEGER` | No | — | Years of licensed practice as of snapshot date. | `12` | Top-5 predictive feature in workup completion model (Random Forest importance: 0.051). |
| `hire_date` | `DATE` | No | — | Date the attorney joined the firm. | `2018-06-01` | Enables firm-tenure analysis; not used in current KPIs. |

**Data Quality Notes:** No anomalies detected in attorney dimension at snapshot date. 12 rows, all fields populated.

---

## Table 3: `case_managers`

**Description:** Case manager dimension. One row per case manager. 18 case managers in snapshot. `monthly_capacity` is the key field driving KPI-06 (Backlog-to-Capacity Ratio).

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `case_manager_id` | `VARCHAR(12)` | No | PK | Surrogate identifier for the case manager. | `CM-001` | Referenced as FK in `cases.assigned_case_manager`, `activities.case_manager_id`, `call_logs.case_manager_id`. |
| `manager_name` | `VARCHAR(120)` | No | — | Full name of the case manager. | `Priya Nair` | Display field; not used as join key. |
| `team` | `VARCHAR(40)` | No | — | Operational team assignment. Values observed: `Intake`, `Workup Team A`, `Workup Team B`, `Settlement`. | `Workup Team A` | Used in productivity team-level aggregations. Also used as categorical feature in predictive model. |
| `hire_date` | `DATE` | No | — | Date the case manager joined the firm. | `2021-09-15` | Enables tenure-adjusted productivity analysis; not in current KPIs. |
| `monthly_capacity` | `INTEGER` | No | — | Stated maximum number of matters the manager can actively work in a single month. | `35` | Used as denominator in KPI-06. Assumption: this is a self-reported or HR-assigned target, not an empirically validated throughput rate. |

**Data Quality Notes:** 18 rows; all fields populated; no anomalies at snapshot. `monthly_capacity` is an assumed operational parameter — validate against actual throughput data before using for formal performance reviews.

---

## Table 4: `cases`

**Description:** Core fact table. One row per legal matter. The primary analytical grain for all KPIs, the predictive model, and the forecasting model. Contains denormalized operational metrics (e.g., `missing_documents`, `communication_count`) that are snapshots as of the load date. 2,743 rows at snapshot.

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `case_id` | `VARCHAR(14)` | No | PK | Surrogate identifier for the matter. | `CASE-000001` | Referenced as FK in all sub-fact tables. |
| `client_id` | `VARCHAR(12)` | No | FK → `clients` | Links matter to the client dimension. NOT NULL enforced. | `CLI-000001` | After deduplication, refers to the canonical (earliest) `client_id`. |
| `case_type` | `VARCHAR(40)` | No | — | Legal case category. Values: `Motor Vehicle Accident`, `Premises Liability`, `Workers Compensation`, `Slip and Fall`, `Nursing Home Abuse`, `Product Liability`, `Medical Malpractice`, `Mass Tort - Roundup`, `Mass Tort - Camp Lejeune`, `Mass Tort - Talcum`, `Dog Bite`, `Wrongful Death`. | `Motor Vehicle Accident` | Used for completion rate drill-down, pipeline valuation, and as categorical feature in ML model. |
| `state` | `CHAR(2)` | No | — | U.S. state jurisdiction in which the case is filed or pending. | `CA` | May differ from `clients.state` (client may reside in different state). |
| `intake_date` | `DATE` | No | — | Date the matter was first opened in the case management system at the case level. | `2024-03-15` | May differ slightly from `clients.intake_date` for same client; both fields tracked. |
| `date_opened` | `DATE` | No | — | Date the matter was formally opened after intake processing. | `2024-03-18` | Used in cycle-time calculation (`date_closed - date_opened`). |
| `date_closed` | `DATE` | **Yes** | — | Date the matter was closed (settled, lost, or dropped). NULL for all open matters (2,180 open as of snapshot). | `2025-01-22` | 6 records had `date_closed < date_opened` — nulled for review in cleaning pipeline. **Excluded from ML features (leakage).** |
| `case_status` | `VARCHAR(30)` | No | — | Current administrative status. Values: `Open`, `Settled`, `Closed-Lost`, `Dropped`. | `Open` | **Excluded from ML features (leakage).** Used in settlement rate KPI-02 denominator. |
| `current_stage` | `VARCHAR(30)` | No | — | Current position in the workup funnel. Values (ordered): `Intake`, `Retainer Signed`, `Records Requested`, `Records Received`, `Workup Complete`, `Demand Sent`, `Negotiation`, `Resolved`. | `Records Requested` | **Excluded from ML features (leakage).** Used in funnel, SLA, and bottleneck KPIs. |
| `assigned_case_manager` | `VARCHAR(12)` | No | FK → `case_managers` | Case manager currently responsible for the matter. | `CM-007` | Used in KPI-05 and KPI-06 (productivity and backlog). |
| `attorney_id` | `VARCHAR(12)` | No | FK → `attorneys` | Attorney assigned to the matter. | `ATT-003` | `attorneys.years_experience` is a top-5 predictive feature. |
| `days_in_stage` | `INTEGER` | No | — | Calendar days elapsed in the current `current_stage` as of snapshot date. | `18` | 10 records had negative values (data error) — corrected to absolute value in cleaning pipeline. Guard clause `days_in_stage >= 0` applied in KPI-07. **Excluded from ML features** — in the synthetic generator this field is derived from the funnel stage index, making it conditionally dependent on the target (review finding C1). Used for SLA and bottleneck KPIs only. |
| `medical_records_received` | `SMALLINT` | No | — | Binary flag: 1 = at least one medical record has been received for this matter; 0 = none received. | `1` | Used in KPI-10 and as top predictive feature (top driver after leakage exclusion). |
| `missing_documents` | `SMALLINT` | No | — | Count of outstanding (Missing or Pending) documents at time of snapshot. | `2` | Used in KPI-10 and as top predictive feature (top driver after leakage exclusion). |
| `communication_count` | `INTEGER` | No | — | Total number of documented communication touchpoints (calls, emails, notes) on this matter. | `7` | Used in Case Quality KPI and as a top predictive feature. |
| `workup_completed` | `SMALLINT` | No | — | Binary flag: 1 = matter has reached or passed "Workup Complete" stage; 0 = has not. | `1` | **Target variable for predictive model.** **Excluded from ML features (leakage).** Numerator for KPI-01. |
| `workup_completed_date` | `DATE` | **Yes** | — | Date the matter reached "Workup Complete" stage. NULL for matters that have not yet completed workup, or for recently opened matters where completion has not been observed by the 2025-06-30 snapshot (right-censored). | `2025-03-22` | Used for workup cycle-time analysis (`workup_completed_date - date_opened`). Right-censoring of this field is the reason the forecast targets new-matter demand volume rather than completed-workup volume — completed counts in recent months are artificially depressed for matters still in progress. See `documentation/assumptions.md`, A-14. |
| `case_outcome` | `VARCHAR(20)` | **Yes** | — | Disposition at closure. Values: `Settled`, `Dismissed`, `Withdrawn`, NULL (open cases). | `Settled` | **Excluded from ML features (leakage).** |
| `settlement_amount` | `NUMERIC(14,2)` | **Yes** | — | Gross settlement amount in USD. NULL for open, lost, and dropped matters. 8 records had negative values in raw data — corrected to absolute value in cleaning pipeline. | `87500.00` | **Excluded from ML features (leakage).** Used in KPI-02, KPI-03, KPI-12. |
| `last_activity_date` | `DATE` | No | — | Date of the most recent activity or touchpoint recorded on this matter. | `2025-05-30` | Used in KPI-08 (inactive case rate): `CURRENT_DATE - last_activity_date > 30`. |

**Data Quality Notes:**
- 10 records with `days_in_stage < 0` repaired to absolute value.
- 6 records with `date_closed < date_opened` nulled for manual review.
- 8 records with `settlement_amount < 0` repaired to absolute value.
- `workup_completed`, `case_status`, `current_stage`, `case_outcome`, `settlement_amount`, `date_closed`, and `days_in_stage` are all **excluded from ML model features** to prevent target leakage. See `documentation/assumptions.md`.

**Indexes:** `idx_cases_cm` (assigned_case_manager), `idx_cases_attorney` (attorney_id), `idx_cases_status` (case_status), `idx_cases_stage` (current_stage), `idx_cases_intake` (intake_date).

---

## Table 5: `activities`

**Description:** Sub-fact table. One row per case manager touchpoint or time-logged activity on a matter. ~17,400 rows at snapshot. Used for KPI-05 (case manager logged hours and activity volume). Feeds the team productivity trend query (dashboard query 3.2).

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `activity_id` | `VARCHAR(14)` | No | PK | Surrogate identifier for the activity record. | `ACT-0000001` | |
| `case_id` | `VARCHAR(14)` | No | FK → `cases` | Links activity to the matter. | `CASE-000042` | NOT NULL enforced. |
| `case_manager_id` | `VARCHAR(12)` | No | FK → `case_managers` | Case manager who performed the activity. | `CM-012` | Nullable FK in DDL; should be non-null in practice. |
| `activity_type` | `VARCHAR(40)` | No | — | Category of the activity. Values: `Phone Call`, `Document Review`, `Records Request`, `Email`, `Internal Note`, `Court Filing`, `Client Meeting`. | `Records Request` | Used for activity-type breakdown analysis. |
| `activity_date` | `DATE` | No | — | Date the activity was performed. | `2025-03-10` | Used in monthly productivity trend query (3.2). |
| `duration_minutes` | `INTEGER` | No | — | Time spent on the activity in minutes. | `45` | Aggregated to logged hours: `SUM(duration_minutes) / 60.0`. |

**Data Quality Notes:** No anomalies detected in activities at snapshot. Check for outlier `duration_minutes` values (e.g., > 480 minutes in a single activity) in production.

---

## Table 6: `documents`

**Description:** Sub-fact table. One row per document requested or received for a matter. ~15,000 rows at snapshot. Used for the missing-document rate KPI and Case Quality analysis.

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `document_id` | `VARCHAR(14)` | No | PK | Surrogate identifier for the document record. | `DOC-0000001` | |
| `case_id` | `VARCHAR(14)` | No | FK → `cases` | Links document to the matter. | `CASE-000100` | NOT NULL enforced. |
| `document_type` | `VARCHAR(40)` | No | — | Type of legal or supporting document. Values: `Retainer Agreement`, `Demand Letter`, `Insurance Records`, `Police Report`, `Employment Records`, `Photographs`, `Expert Report`. | `Police Report` | Used for document-type completeness analysis. |
| `status` | `VARCHAR(15)` | No | — | Current status of the document. Values: `Received`, `Missing`, `Pending`. | `Pending` | `Missing` and `Pending` statuses drive the missing-document KPI-10. |
| `requested_date` | `DATE` | No | — | Date the document was first requested from the relevant party. | `2024-04-01` | Used for document aging analysis. |
| `received_date` | `DATE` | **Yes** | — | Date the document was received. NULL if `status` is `Missing` or `Pending`. | `2024-04-22` | Null for unresolved documents. |

**Data Quality Notes:** `received_date` is null for all non-`Received` status records — expected behavior. Cross-check that `cases.missing_documents` count reconciles with `COUNT(*) WHERE status IN ('Missing','Pending')` grouped by `case_id`; drift may occur if denormalized field is not refreshed at ETL time.

---

## Table 7: `medical_records`

**Description:** Sub-fact table. One row per medical records request sent to a healthcare provider for a matter. ~5,900 rows at snapshot. Critical for the records-acquisition bottleneck analysis (dashboard query 7.2). Medical records receipt status (`medical_records_received` on `cases`) is the #3 predictive feature in the workup completion model.

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `record_id` | `VARCHAR(14)` | No | PK | Surrogate identifier for the medical record request. | `MR-0000001` | |
| `case_id` | `VARCHAR(14)` | No | FK → `cases` | Links medical record request to the matter. | `CASE-000088` | NOT NULL enforced. |
| `provider_name` | `VARCHAR(80)` | No | — | Name of the healthcare provider from whom records are requested. | `Mercy Regional Hospital` | Used for provider-level response-time analysis (not in current KPIs). |
| `requested_date` | `DATE` | No | — | Date the records request was submitted to the provider. | `2024-05-12` | Used in aging analysis: `CURRENT_DATE - requested_date` for outstanding records. |
| `received_date` | `DATE` | **Yes** | — | Date the medical records were received from the provider. NULL if `status = 'Outstanding'`. | `2024-06-18` | Null for outstanding records. |
| `status` | `VARCHAR(15)` | No | — | Current status of the records request. Values: `Received`, `Outstanding`. | `Outstanding` | Drives bottleneck KPI: cases stuck in `Records Requested` / `Records Received` stages. |
| `num_pages` | `INTEGER` | **Yes** | — | Number of pages in the received records packet. NULL if not yet received. | `142` | Useful for estimating review time; not yet in KPI set. |

**Data Quality Notes:** `received_date` and `num_pages` null for all `Outstanding` records — expected. Outstanding records aging (`AVG(CURRENT_DATE - requested_date)`) is surfaced in dashboard query 7.2.

---

## Table 8: `settlements`

**Description:** Sub-fact table. One row per settled matter with full economic decomposition. 329 rows at snapshot (all matters with `case_status = 'Settled'`). Provides the detailed financial breakdown beyond the gross `settlement_amount` stored on `cases`.

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `settlement_id` | `VARCHAR(12)` | No | PK | Surrogate identifier for the settlement record. | `SET-000001` | |
| `case_id` | `VARCHAR(14)` | No | FK → `cases` | Links settlement to the matter. | `CASE-000027` | NOT NULL enforced. One settlement per matter assumed (one-to-one in current model). |
| `settlement_amount` | `NUMERIC(14,2)` | No | — | Gross settlement amount in USD. | `112000.00` | Should reconcile with `cases.settlement_amount` after cleaning. |
| `settlement_date` | `DATE` | No | — | Date the settlement was executed/finalized. | `2025-02-14` | Used for settlement timing analysis (not in current KPIs). |
| `attorney_fee` | `NUMERIC(14,2)` | No | — | Attorney's contingency fee deducted from gross settlement. Typically 33–40% of gross. | `37333.33` | Used for attorney revenue analysis. |
| `lien_amount` | `NUMERIC(14,2)` | No | — | Total lien obligations (medical liens, Medicare/Medicaid subrogation, etc.) deducted from gross settlement. | `8200.00` | Lien management is a critical step in settlement disbursement. |
| `case_costs` | `NUMERIC(14,2)` | No | — | Litigation expenses advanced by the firm and recovered from settlement proceeds. | `4500.00` | Includes expert fees, filing fees, records costs, etc. |
| `net_to_client` | `NUMERIC(14,2)` | No | — | Net amount disbursed to the client after all deductions: `settlement_amount - attorney_fee - lien_amount - case_costs`. | `61966.67` | Key client-facing metric; distinct from firm revenue. |

**Data Quality Notes:** `settlement_amount` on `cases` had 8 negative values (repaired to absolute value); `settlements` table records should be verified to be consistent after cleaning. Verify `net_to_client = settlement_amount - attorney_fee - lien_amount - case_costs` for each row in production.

---

## Table 9: `call_logs`

**Description:** Sub-fact table. One row per logged phone interaction between case managers and clients. ~15,000 rows at snapshot. Provides directional call volume (inbound/outbound) and outcomes. `communication_count` on `cases` is a denormalized aggregate that includes calls and other touchpoints; `call_logs` provides the granular call-level detail.

| Column | Data Type | Nullable | PK/FK | Description | Example Value | Notes |
|---|---|---|---|---|---|---|
| `call_id` | `VARCHAR(14)` | No | PK | Surrogate identifier for the call record. | `CALL-0000001` | |
| `case_id` | `VARCHAR(14)` | **Yes** | FK → `cases` | Links call to the matter. Nullable FK — some intake calls may precede matter creation. | `CASE-000155` | Nullable FK in DDL; referential integrity relaxed for pre-intake calls. |
| `client_id` | `VARCHAR(12)` | **Yes** | FK → `clients` | Links call to the client (directly, not via case). | `CLI-001234` | Nullable FK. Allows tracking calls to clients who have not yet had a case opened. |
| `case_manager_id` | `VARCHAR(12)` | **Yes** | FK → `case_managers` | Case manager who handled the call. | `CM-008` | Nullable FK. |
| `call_date` | `DATE` | No | — | Date the call occurred. | `2025-04-03` | Used for communication trend analysis. |
| `direction` | `VARCHAR(10)` | No | — | Direction of the call. Values: `Inbound`, `Outbound`. | `Outbound` | Used to distinguish proactive outreach from client-initiated contact. |
| `duration_seconds` | `INTEGER` | No | — | Length of the call in seconds. | `312` | Convert to minutes (`/ 60`) for reporting. |
| `outcome` | `VARCHAR(30)` | No | — | Result of the call. Values: `Completed`, `Voicemail`, `No Answer`, `Callback Scheduled`. | `Completed` | Used to assess client-engagement effectiveness. |

**Data Quality Notes:** Three FK columns are nullable to accommodate pre-case calls. In production, validate that `case_id` is non-null for all calls occurring after a matter is opened. `duration_seconds = 0` may indicate dropped calls; flag for quality review.

---

## Field Cross-Reference: ML Model Features

The predictive model (`python/04_predictive_model.py`) uses the following fields. Leakage-risk fields are explicitly excluded.

| Field | Table | Used as Feature | Reason if Excluded |
|---|---|---|---|
| `missing_documents` | `cases` | Yes (numeric) | — |
| `medical_records_received` | `cases` | Yes (numeric) | — |
| `communication_count` | `cases` | Yes (numeric) | — |
| `case_type` | `cases` | Yes (categorical) | — |
| `attorneys.years_experience` | `attorneys` (via join) | Yes (numeric) | — |
| `case_managers.team` | `case_managers` (via join) | Yes (categorical) | — |
| `clients.marketing_channel` | `clients` (via join) | Yes (categorical) | — |
| `clients.referral_source` | `clients` (via join) | Yes (categorical) | — |
| `workup_completed` | `cases` | **TARGET** — excluded from features | Target variable |
| `days_in_stage` | `cases` | **EXCLUDED** | Leakage: in the synthetic generator this field is derived from the funnel stage index, which is conditional on the target (`workup_completed`). Excluded per methodology review finding C1. Used for SLA KPIs only. |
| `current_stage` | `cases` | **EXCLUDED** | Leakage: encodes current workup position |
| `case_status` | `cases` | **EXCLUDED** | Leakage: encodes resolution outcome |
| `case_outcome` | `cases` | **EXCLUDED** | Leakage: encodes resolution outcome |
| `settlement_amount` | `cases` | **EXCLUDED** | Leakage: only populated post-settlement |
| `date_closed` | `cases` | **EXCLUDED** | Leakage: only populated post-closure |
| `workup_completed_date` | `cases` | **EXCLUDED** | Leakage: only populated post-completion; also right-censored for recent matters |

---

*Cross-references: `sql/01_create_tables.sql` (DDL), `python/01_data_cleaning.py` (cleaning logic), `python/outputs/cleaning_report.txt` (cleaning summary), `documentation/kpi_dictionary.md` (field usage in KPIs), `documentation/assumptions.md` (modeling assumptions).*
