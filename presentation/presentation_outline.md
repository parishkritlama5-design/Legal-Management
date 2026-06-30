# Legal Case Management Intelligence Platform
## Interview Walkthrough — Presentation Outline
### Strategic Operations Business Analyst | Plaintiff-Side / Mass-Tort Law Firm

---

> **How to use this document.** Each slide entry contains: the slide title, a
> one-line headline (the single thing the audience must remember), bullet talking
> points, the recommended visual, and a speaker-notes paragraph written in the
> first person exactly as the candidate would say it aloud.

---

## SLIDE 1 — Title & Project Introduction

**Headline:** *"I built an end-to-end intelligence platform to turn a 2,743-case portfolio into a data-driven operation."*

### Talking Points
- Candidate name, target role, firm context (plaintiff-side / mass-tort)
- Platform name: Legal Case Management Intelligence Platform
- Scope: 2,743 matters, 2,500 clients, 12 attorneys, 18 case managers, 24-month horizon (Jul 2023 – Jun 2025)
- Three deliverables in one: operational BI dashboards, a predictive risk model, and a 6-month capacity forecast
- Stack: PostgreSQL, Python (pandas / scikit-learn), Power BI / Sigma

### Recommended Visual
Title card with a simple three-box architecture diagram: **Data Sources → SQL Warehouse → BI / Python outputs**. Clean dark background, firm colors if available.

### Speaker Notes
"Thank you for having me. This project is called the Legal Case Management Intelligence Platform, and I built it to answer the questions every operations leader at a plaintiff firm cares about: are our cases moving, who is falling behind, and what does capacity look like six months from now? I worked with a 2,743-matter portfolio spanning two years of intake. The end product is three things — a seven-page BI dashboard suite, a logistic-regression model that flags at-risk workups before they stall, and a six-month volume forecast. I'll walk you through all of it in the next twelve slides."

---

## SLIDE 2 — The Business Problem

**Headline:** *"Without visibility into the pipeline, firms are managing 2,180 open matters by gut feel — and leaving money on the table."*

### Talking Points
- Plaintiff firms live and die by workup speed: medical records drive settlement value, and stalled cases drag revenue
- Common pain points: no single source of truth on case stage, manager productivity tracked in spreadsheets, no early warning for cases that will miss deadlines
- Mass-tort portfolios compound the problem — heterogeneous case types (MVA vs. Camp Lejeune) have very different completion rhythms
- The cost of inaction: 39.2% of the portfolio has not completed workup; every month of delay is realized revenue deferred
- Data quality is invisible — 40 duplicate clients and 8 negative settlement records went undetected before this project

### Recommended Visual
Annotated funnel diagram (hand-drawn or simple infographic style) showing the 8 workup stages, with a large "drop-off" callout at the Records stage. Can reference `eda_funnel.png`.

### Speaker Notes
"The fundamental problem at a plaintiff firm is that your revenue is locked inside the workup pipeline. You can't demand until the medical records are complete; you can't settle until the demand is out. If you don't know exactly where each of your 2,180 open matters stands today, you're managing by feel. And the data quality layer makes it worse — before I ran my cleaning script, this dataset had 40 duplicate clients and settlement records with negative dollar values. No dashboard built on dirty data is trustworthy, so I treated data quality as a first-class deliverable, not an afterthought."

---

## SLIDE 3 — Project Objective & Analytical Approach

**Headline:** *"Four questions, one structured analytical workflow — from raw CSV to actionable recommendation."*

### Talking Points
- Four core questions framed at the outset:
  1. Where is the portfolio today? (operational health snapshot)
  2. Who is behind? (manager and case-type performance)
  3. Which cases will stall? (predictive risk scoring)
  4. What does capacity look like? (volume forecast)
- Methodology in four phases: Data Quality Audit → Exploratory Analysis → SQL-powered BI → Python ML/Forecasting
- Snapshot date: 2025-06-30; all metrics reflect this point-in-time view
- Explicit definition of metrics upfront (workup completion = reached "Workup Complete" stage or beyond; settlement rate computed on resolved cases only, not the full portfolio)

### Recommended Visual
Four-quadrant diagram or numbered swim-lane showing the analytical phases. Simple and clean — no decoration needed.

### Speaker Notes
"Before writing a single line of SQL I wrote down four business questions and defined every metric precisely. For example, settlement rate is easy to overstate if you compute it against all 2,743 cases — most of those are still open. I computed it only on the 563 resolved matters, which gives a true rate of 57.8%. Metric discipline like that is the difference between an insight and a misleading number. Then I followed a four-phase workflow: clean, explore, warehouse, and model. Each phase produced a documented artifact — a cleaning report, EDA charts, a SQL library, and Python model outputs."

---

## SLIDE 4 — Data Architecture

**Headline:** *"Raw flat files in; trusted, indexed, query-ready data out — the whole pipeline is auditable at every step."*

### Talking Points
- Sources: 9 CSV files representing the operational layer of a case management system
- Ingestion & cleaning: Python (`01_data_cleaning.py`) — dedup, null repair, negative-value correction, flag generation; outputs `cases_clean.csv` and `clients_clean.csv`
- Storage: PostgreSQL relational schema — DDL in `01_create_tables.sql`, bulk load in `02_load_data.sql`; 6 covering indexes added for dashboard query performance
- Analytics layer: `03_kpi_queries.sql` (9 self-contained KPI queries), `04_dashboard_queries.sql` (7 dashboard page queries), `05_data_quality_queries.sql`
- Consumption layer: Power BI / Sigma (7-page dashboard), Python outputs (forecast chart, ROC curve, feature importance chart)
- All outputs in `python/outputs/`; no hardcoded file paths — all scripts parameterized

### Recommended Visual
A horizontal flow diagram with five labeled swim lanes:
**CSV Sources → Python Cleaning → PostgreSQL → SQL Query Library → BI Dashboard + Python ML outputs**

### Speaker Notes
"The architecture follows a simple principle: every transformation is documented and reversible. The Python cleaning script writes a plain-text cleaning report so anyone can audit exactly what changed and why. PostgreSQL serves as the single source of truth — once the data is loaded, every dashboard and every model pulls from the same tables. I added six indexes on the cases table targeting the columns most frequently used in WHERE and GROUP BY clauses, which cuts dashboard query time significantly on a 2,743-row dataset. At the top of the stack, Power BI and Sigma consume the SQL views, and the Python scripts read directly from the cleaned CSVs to produce the ML outputs."

---

## SLIDE 5 — Data Model / Entity-Relationship Overview

**Headline:** *"Nine tables, a star-ish schema, and every business relationship enforced at the database layer."*

### Talking Points
- 3 dimension tables: `clients`, `attorneys`, `case_managers`
- 1 core fact table: `cases` — one row per matter; carries operational metrics used as ML features
- 5 sub-fact tables: `activities`, `documents`, `medical_records`, `settlements`, `call_logs`
- Key design decisions:
  - `cases` intentionally denormalizes operational counters (`communication_count`, `missing_documents`, `medical_records_received`) for fast dashboard aggregation
  - `settlement_amount` also stored on `cases` for the headline KPIs; `settlements` sub-fact carries attorney fees, liens, net-to-client for the detailed economics page
  - All foreign keys enforced with `REFERENCES` constraints; `CASCADE` on drop for safe re-loads
- Data quality issues surfaced by schema: `email` and `referral_source` are nullable by design (~3% and ~2% missing respectively); `workup_completed` and `medical_records_received` are `SMALLINT` flags (0/1)

### Recommended Visual
A clean ERD diagram (crow's-foot notation) with the three tiers color-coded:
- Blue = dimension tables
- Orange = core fact (`cases`)
- Grey = sub-facts

Draw this by hand on a whiteboard or use a simple dbdiagram.io export.

### Speaker Notes
"The schema follows a star-ish pattern — I say 'star-ish' because it's not a pure Kimball fact-dimension model; it's an operational schema where the cases table carries some pre-aggregated counters to make dashboard queries fast without joins. The five sub-fact tables hold the granular transactional detail: every activity log, every document request, every call. If the firm wanted to add a new analysis — say, time-to-return calls by attorney — all the data is there, properly keyed, enforced by foreign-key constraints. I also made a deliberate choice to store settlement economics in two places: a summary amount on cases for the KPI tiles, and the full financial breakdown in the settlements table for the economics page."

---

## SLIDE 6 — Dashboard Overview (7 Pages)

**Headline:** *"Seven pages, one narrative — from executive health check to individual case triage."*

### Talking Points
Each dashboard page is purpose-built for a specific decision:

| Page | Name | Primary Audience | Key Question Answered |
|------|------|-----------------|----------------------|
| 1 | Executive Overview | Managing Partner | Portfolio health at a glance — KPI tiles, pipeline value |
| 2 | Client Workup Funnel | Operations Director | Where does the pipeline narrow? What is stage conversion? |
| 3 | Case Manager Productivity | Team Leads | Who is performing, who needs support? |
| 4 | Case Quality Analytics | QA / Operations | Do records and communications correlate with settlement value? |
| 5 | Forecasting | Operations / Finance | How many completions should we plan for the next 6 months? |
| 6 | Data Quality | Data/Ops | What integrity issues exist and have they been resolved? |
| 7 | Operational Bottlenecks | Case Managers | Which cases are stalled, which stage has the longest queue? |

- Headline KPIs on Page 1: 2,743 total cases / 2,180 open / 60.8% workup completion / $30.17M total settlements
- All pages filter-synchronized by `case_type`, `team`, and `date_opened` range slicers

### Recommended Visual
A 2x4 grid of thumbnail screenshots (or hand-sketched wireframes) representing each dashboard page, with the page number and name labeled. Alternatively, if the actual Power BI file is available, screenshot Page 1 directly.

### Speaker Notes
"I designed the dashboard in a specific sequence: the executive overview is the 30-second health check — one glance and the managing partner knows the four numbers that matter. From there, each subsequent page goes one level deeper. The funnel page shows where cases are dropping out. The productivity page shows who is driving that drop-out. The quality page asks whether the effort is producing better outcomes. And then pages five through seven are action-oriented — forecast your capacity, verify your data, find the specific cases that are stuck. Everything is connected by cross-page slicers so a team lead can filter to their own portfolio with one click."

---

## SLIDE 7 — SQL Logic Highlights

**Headline:** *"The SQL is not just queries — it's a documented business logic library with nine reusable KPIs."*

### Talking Points
- **True funnel computation (KPI 1):** Cases "at-or-beyond" each stage — a cumulative count using a self-join on a `stage_order` CTE, not a simple GROUP BY on `current_stage` (which would miss cases that passed through)
- **Window functions for ranking (KPI 5):** `RANK() OVER (ORDER BY completion_rate DESC)` gives each case manager their firm-wide rank without a subquery
- **Rolling 3-month intake average (KPI 9):** `AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` — standard time-series smoothing in a single window clause
- **SLA compliance engine (KPI 7):** CTE-defined target days joined against live `days_in_stage` to produce per-stage compliance rates — parameterized, so SLA targets can be updated in one place
- **Inactive case triage (KPI 8):** `ROW_NUMBER() OVER (PARTITION BY assigned_case_manager ORDER BY last_activity_date)` ranks the stalest case per manager for immediate triage
- **Pipeline expected value (Dashboard Page 1):** Settlement rate and average settlement computed per case type, then multiplied against the open-case count to produce a weighted expected pipeline value
- Guard rails throughout: `NULLIF(..., 0)` prevents division-by-zero; `FILTER (WHERE ...)` replaces CASE WHEN for cleaner aggregation; `date_closed IS NULL` gates all open-pipeline logic

### Recommended Visual
Side-by-side code panel: show 8-10 lines of the funnel CTE (KPI 1) on the left; annotate 3-4 lines with callout arrows explaining the business logic. Monospace font, syntax-highlighted.

Reference file: `/Users/rin/Legal-Case-Management-Intelligence/sql/03_kpi_queries.sql`

### Speaker Notes
"I want to walk through one SQL technique that was non-obvious: the funnel query. A naive query groups by `current_stage` and counts. That tells you how many cases are sitting in each stage right now — it does not tell you how many cases have ever reached each stage, which is what a funnel measures. My solution uses a `stage_order` CTE that assigns ordinal ranks to each stage, then joins back to cases where the case's current ordinal is greater than or equal to the stage ordinal. That gives you a true cumulative funnel. Every one of the nine KPI queries is written the same way — business question at the top as a comment, then the SQL that provably answers it."

---

## SLIDE 8 — Predictive Model: Workup Completion Risk

**Headline:** *"184 at-risk matters flagged, methodology reviewed against itself, and the number I'm reporting is the honest one."*

### Talking Points
- **Target:** Binary flag — will this matter complete workup? (`workup_completed` = 1)
- **Model selected:** Logistic Regression (chosen over Random Forest by ROC-AUC: 0.696 vs. 0.686; preferred for interpretability in a legal operations context)
- **Validation approach — lead with this:** 5-fold stratified cross-validation ROC-AUC: **0.700 ± 0.020**. CV mean is the number to cite first; the held-out test set result (0.696) is consistent with it, which builds confidence the model generalizes.
- **Performance on held-out test set (686 cases, stratified 25% split):**
  - Accuracy: 68.7% | Precision: 70.1% | Recall: 84.4% | ROC-AUC: 0.696
- **Why Recall matters more than Precision here:** A false negative (missing an at-risk case) costs the firm a stalled matter and deferred revenue. A false positive (flagging a case that would have completed anyway) costs a case manager 15 minutes of review. The model was tuned to minimize false negatives.
- **Leakage review — a deliberate adversarial step:** An initial version included `days_in_stage` as a feature. A methodology review identified it as a subtle leak: `days_in_stage` is derived from the current funnel stage, which is itself conditional on the target outcome. Removing it caused AUC to fall from ~0.715 to 0.696 — and that lower number is the one reported here because it is the one earned on legitimate features.
- **Top predictive drivers after leakage fix** (from Random Forest feature importances as a complementary diagnostic):
  1. `missing_documents` — document gaps are the strongest clean signal of stall risk
  2. `medical_records_received` — records on file substantially reduce risk
  3. `communication_count` — active touchpoints correlate with completion
  4. `attorney_years_experience` — more experienced attorneys correlate with higher completion rates
- **Pipeline discipline:** Imputation was performed inside a sklearn Pipeline fitted only on training data, so no test-set information contaminated the preprocessing step.
- **Action output:** `predictions.csv` — 686 scored cases with predicted probability, flagged if P(at-risk) above threshold; **184 cases flagged for intervention**

### Recommended Visual
Two charts side-by-side:
1. ROC curve — `python/outputs/roc_curve.png` — annotate the AUC = 0.696 callout and note CV mean of 0.700
2. Feature importance bar chart — `python/outputs/feature_importance.png` — top 4 clean features labeled; `days_in_stage` absent and explicitly noted

### Speaker Notes
"I want to lead with something that is not on most project slides: I ran an adversarial methodology review against my own model. An initial version of the feature set included `days_in_stage` — how long a case has been stuck in its current stage — and it was the top driver. That looked compelling, but a closer look revealed the problem: `days_in_stage` is derived from `current_stage`, which is downstream of the target. A case that has never progressed past Intake has a very different `days_in_stage` profile than one sitting in Negotiation. Including it let the model partially see the answer before making a prediction. I removed it, the AUC fell from roughly 0.715 to 0.696, and I'm reporting 0.696. I also validated the result with 5-fold stratified cross-validation — mean AUC 0.700 plus or minus 0.020 — so the test-set number is not a fluke. The top drivers in the clean model are missing documents, records received, communication count, and attorney experience — all operationally observable before you know the outcome, and all directly actionable."

---

## SLIDE 9 — Forecasting: Workup Demand Volume

**Headline:** *"New-matter demand will soften to ~122–162 per month through year-end — the pipeline is filling faster than it is clearing."*

### Recommended Visual
Time series chart — `python/outputs/forecast_workup_volume.png`
- Solid line: 24 months of actuals (Jul 2023 – Jun 2025)
- Dashed line: 6-month forecast (Jul – Dec 2025)
- Shaded band: prediction interval anchored on back-test error, widening with horizon
- Annotate the seasonal Nov–Dec dip and the one-time marketing-surge distortion in the historical series

### Talking Points
- **Target variable correction — this is important:** The forecast tracks monthly workup **demand** (new matters entering the pipeline), not completed-workup volume. Completion volume is right-censored at the snapshot date: cases opened in recent months have had less time to complete, so a back-test on completions systematically underestimates model error for recent periods. Intake/opened volume is the clean leading indicator for capacity planning — it is fully observable at the time it occurs.
- **Method:** Holt-Winters Exponential Smoothing on 24 months of monthly new-matter intake
- **Back-test accuracy:** MAPE 12.5%, MAE 15.8 new matters per month — the model is off by roughly 16 matters in a typical month; appropriate for 60-to-90-day staffing decisions
- **Forecast (Jul–Dec 2025):** 162, 157, 147, 154, 122, 127 new matters/month
- **Notable pattern:** Nov–Dec seasonal dip visible in history, replicated in forecast — consistent with holiday-period intake slowdowns. One-time marketing intake surge in the historical data limits the seasonal model's precision; this is disclosed as a known constraint.
- **Capacity implication:** The 60.8% completion rate against a growing intake volume means the backlog is structurally widening. If demand runs at ~150/month and completions run at ~90/month (based on recent actuals), the net backlog grows by ~60 cases per month. November at 122 new matters is the lowest-demand month — if the firm wants to reduce backlog, Q4 is the best window to do it.
- Prediction intervals widen with horizon; the December lower bound represents the downside planning scenario.

### Speaker Notes
"I want to be transparent about a methodology decision I made for the forecast. My first instinct was to forecast completed-workup volume — that is directly the capacity question. But completion volume is right-censored: a case opened in May 2025 has had one month to complete by the snapshot date; a case from 2023 has had two years. When I back-tested a completion-volume model, the error was systematically worse for recent months because those months were structurally undercounted. That corrupts the MAPE calculation and makes the back-test look better than it is. So I switched the target to intake demand — new matters entering the pipeline — which is fully observable the month it happens. A MAPE of 12.5% on that series is a reliable number. The capacity story actually becomes clearer this way: demand is running at 120 to 160 per month, completions are running at roughly 90, and that gap is the backlog growth rate the firm needs to manage."

---

## SLIDE 10 — Key Insights

**Headline:** *"Six findings that change how this firm manages its portfolio — each one is directly actionable."*

### Talking Points

**1. Mass-tort completion rates lag by 25+ points.**
Dog Bite (75.2%) and MVA (73.5%) cases complete at nearly normal rates. Mass-tort cases — Talcum (41.3%), Camp Lejeune (43.9%), Roundup (51.4%) — complete at dramatically lower rates. This is not a workload problem; it is a process and documentation problem specific to multi-defendant litigation.

**2. 39.2% of the portfolio has not completed workup.**
2,180 cases are open; 60.8% completion means roughly 848 open matters are stuck before reaching Workup Complete. These cases represent the single largest lever on settlement pipeline.

**3. Missing documents are the top clean predictor of stall.**
After a methodology review removed `days_in_stage` as a leaky feature, `missing_documents` emerged as the strongest remaining signal. Document gap is operationally fixable: automated reminders, paralegal follow-up queues, and vendor integrations can directly reduce this risk.

**4. Medical records on file and active communication are the next two levers.**
`medical_records_received` and `communication_count` rank second and third among clean predictors. Both are directly manageable: records retrieval workflows and structured touchpoint cadences are standard operating improvements, not technology investments.

**5. The Records Requested stage is the primary bottleneck.**
Dashboard Page 7 reveals that the highest volume of open, stalled cases sit in the Records Requested stage. Medical record retrieval latency — not attorney bandwidth — is the rate-limiting step.

**6. 76 clients have no email address on file.**
With no email, automated outreach is impossible. 3% of the client base is structurally excluded from digital communications — a data completeness issue with a direct fix.

### Recommended Visual
Six numbered callout boxes — each with a bold stat and a one-line implication. Use `eda_completion_by_type.png` and `eda_funnel.png` as supporting thumbnails beside insights 1 and 5.

### Speaker Notes
"Every one of these six findings is grounded in the data and directly maps to an operational decision. I want to highlight finding three specifically. After a methodology review caught that `days_in_stage` was a leaky feature and removed it, missing documents emerged as the top clean predictor of stall — and that is actually a more actionable finding. You cannot change how long a case has been in a stage, but you can fix a document gap today. A paralegal follow-up queue triggered by the model's flag is a direct intervention against the leading cause of stall. That's the kind of insight that operationalizes the model into something a case manager can act on tomorrow morning."

---

## SLIDE 11 — Recommendations

**Headline:** *"Four recommendations, two of which can be implemented this quarter with no new tooling."*

### Talking Points

**Recommendation 1 — Implement a weekly at-risk triage report (Immediate / No new tools)**
Run the predictive model's `predictions.csv` output weekly. Route the 15-20 highest-risk cases to each case manager on Monday morning. The model already exists; this is a scheduling and process change only.
- Expected impact: 10–15% reduction in stall rate among flagged cases within 90 days

**Recommendation 2 — Set and enforce stage-SLA alerts in the case management system (Q3 / Configuration only)**
The SLA framework already exists in `03_kpi_queries.sql` (KPI 7). Map these thresholds to automated alerts in the CMS. Any case exceeding its stage-SLA target triggers a notification to the assigned manager and their team lead.
- Expected impact: Reduces average days-in-stage at the Records Requested bottleneck; targets primary stall driver

**Recommendation 3 — Create a mass-tort-specific workup protocol (Q3–Q4 / Process design)**
Talcum, Camp Lejeune, and Roundup cases have structurally different document requirements. A tailored checklist and dedicated workup team assignment for mass-tort matters would address the 25-point completion rate gap versus standard tort.
- Expected impact: Close the mass-tort gap by 10–15 points over 12 months

**Recommendation 4 — Remediate the 76 missing-email records and add intake validation (Immediate / Data governance)**
Backfill missing emails through client outreach; add a required-field validation at intake to prevent future gaps. Firms with complete contact data have measurably higher client touchpoint rates.
- Expected impact: Increases digital reach to 100% of the active client base

### Recommended Visual
A 2x2 priority matrix: Y-axis = estimated impact (Low / High), X-axis = implementation effort (Low / High). Plot all four recommendations; Recs 1 and 4 sit in the high-impact / low-effort quadrant.

### Speaker Notes
"I prioritized these recommendations by the ratio of impact to effort. Recommendations one and four require no new software, no budget approval, and no organizational change — they are process and data decisions that the operations team can make this week. Recommendation two is a configuration change in whatever case management system the firm already uses; the logic is already written in SQL. Recommendation three is the heaviest lift — it requires a process redesign workshop with the mass-tort team leads — but it addresses a 25-percentage-point performance gap that likely represents millions of dollars in deferred settlements. I would tackle it in parallel with the quick wins."

---

## SLIDE 12 — Business Impact & Closing

**Headline:** *"This is what structured analysis looks like applied to a plaintiff firm's most valuable asset: its pipeline."*

### Talking Points
- **Portfolio value at stake:** $30.17M in settled matters to date; 2,180 open matters with expected pipeline value computable from the dashboard
- **If completion rate improves from 60.8% to 70%:** That is approximately 247 additional matters completing workup — at the current average settlement of $91,709 and 57.8% settlement rate, that represents roughly $13.1M in incremental expected settlement value
- **The platform is not a one-time project:** It is a reusable infrastructure — the SQL library, the cleaned schema, and the Python scripts are parameterized and can be refreshed with a new data extract in under an hour
- **Skills demonstrated in this project:**
  - Business problem scoping and metric definition
  - End-to-end data quality audit and remediation
  - Relational schema design (PostgreSQL)
  - Advanced SQL (CTEs, window functions, CASE, FILTER aggregations)
  - Python data pipeline (pandas, numpy)
  - Machine learning in a business context (logistic regression, feature selection, leakage prevention)
  - Time-series forecasting (Holt-Winters, MAPE back-test)
  - BI dashboard design (executive through operational)
  - Business storytelling from data to recommendation

### Recommended Visual
Single closing slide: the four headline KPIs in large type (2,743 cases / $30.17M settled / 60.8% completion / 184 at-risk flagged), a one-line project summary, and contact information. Clean, confident, minimal.

### Speaker Notes
"I want to close with the number that frames the entire project: 39.2% of the portfolio has not completed workup. That is not a data problem — the data now shows it clearly. That is an operational problem, and it has a dollar value attached to it. The incremental expected value of closing that gap by 10 percentage points is in excess of $13 million. That is the business case for investing in data infrastructure, and that is exactly the kind of analysis I would bring to this role on day one. I am happy to go deeper on any component — the SQL, the model, the dashboard design, or the recommendations."

---
---

## ANTICIPATED INTERVIEW Q&A

### Q1: Walk me through how you defined "workup completion." Could that definition bias your results?

**Answer:**
Workup completion is a binary flag: a case has `workup_completed = 1` if it has ever reached the "Workup Complete" stage or any downstream stage (Demand Sent, Negotiation, Resolved). It is set at intake and does not change if a case later stalls. This is a point-in-time snapshot flag, not a real-time recalculation. The potential bias is that cases opened more recently have had less time to reach completion — so recent cohorts are structurally under-counted. I did not apply a vintage adjustment in this project, which means the completion rate for cases opened in late 2024 or 2025 is depressed relative to their eventual outcome. For a production model, I would either restrict the training population to cases opened at least 90 days before the snapshot, or I would include `days_since_opened` as a covariate to control for cohort age.

---

### Q2: How did you prevent data leakage in your predictive model?

**Answer:**
This is the most important modeling question, and I want to go further than the standard answer. The obvious post-outcome fields were excluded from the start:
- `current_stage` — a case in "Demand Sent" is by definition completed; including it makes the model trivially predictive
- `case_status` — "Settled" implies completion; same issue
- `case_outcome` — same logic
- `settlement_amount` — only non-null for settled cases; a direct proxy for the outcome
- `date_closed` — only populated for closed cases
- `days_to_close` and `is_open` (derived flags) — same

But I then ran an adversarial methodology review against my own initial feature set, and it caught something subtler: `days_in_stage`. At first glance this looks clean — it's how long a case has been in its current stage, which seems like an input observable before the outcome. The problem is that `days_in_stage` is derived from `current_stage`, which is conditional on the target. A case that has never progressed past Intake has a structurally different `days_in_stage` profile than one sitting in Negotiation, and `current_stage` itself encodes the outcome. Keeping `days_in_stage` allowed the model to partially recover the funnel position from a supposedly excluded variable. I removed it. The AUC fell from approximately 0.715 to 0.696 — and 0.696 is the number I report because it is the honest one. I frame this as a strength: I found the leak myself, I fixed it, and the metric went down. That is what rigorous modeling looks like. The remaining features — `missing_documents`, `medical_records_received`, `communication_count`, attorney experience, case type, marketing channel — are all genuinely observable before the workup outcome is determined. I also fitted all imputation inside a sklearn Pipeline to ensure no test-set information contaminated preprocessing.

---

### Q3: Your model accuracy is 68.7%, which is not particularly high. Why should the firm trust it?

**Answer:**
Accuracy is the wrong metric for this use case, because the cost of errors is asymmetric. The business cost of a false negative — missing a case that will stall — is a deferred settlement worth tens of thousands of dollars and weeks of delay. The cost of a false positive — flagging a healthy case — is 15 minutes of a case manager's time. Given that asymmetry, I optimized for recall (84.4%), which means the model catches more than 4 in 5 cases that will fail to complete workup. The ROC-AUC of 0.696 — validated at 0.700 ± 0.020 across 5 cross-validation folds — tells you the model is meaningfully better than random (AUC = 0.50) across all classification thresholds, and that performance holds up out of sample. In a legal operations context, a model that reliably flags the majority of stalling cases with a manageable false-positive rate is operationally valuable — it does not need to be 90% accurate to justify a weekly triage report. The 184 flagged cases are a starting list for human review, not autonomous decisions.

---

### Q4: Why did you choose Logistic Regression over Random Forest, when Random Forest often performs better?

**Answer:**
Two reasons. First, on this dataset after the leakage fix, Logistic Regression outperformed Random Forest on ROC-AUC (0.696 vs. 0.686) — the performance difference is marginal, so there is no empirical case for the more complex model. Second, interpretability matters in a legal operations context. When a case manager asks "why is this case flagged?", Logistic Regression allows me to explain the prediction in terms of signed coefficients: more `missing_documents` increases risk, more `communication_count` reduces risk. Random Forest produces a feature importance ranking but not a directional per-case explanation. Logistic Regression also produces calibrated probabilities more naturally, which allows the firm to sort cases by predicted risk level and triage the most critical ones first — that is more useful than a binary flag. The 5-fold CV result of 0.700 ± 0.020 further confirms the choice is stable; there is no evidence that Random Forest would generalize better on this population.

---

### Q5: The forecast MAPE is 12.5%. Is that good enough to make staffing decisions?

**Answer:**
It depends on what decision you are making and what the alternative is. At 12.5% MAPE and a MAE of 15.8 new matters per month on a series averaging roughly 140 new matters per month, the typical forecast error is about 16 matters. If the firm is deciding whether to hire a full-time case manager — a months-long decision — that error band is acceptable; you are not optimizing at single-case precision. If the firm were trying to forecast attorney billing hours to the nearest hour, 12.5% would be inadequate. I would position this forecast as an input to 60-to-90-day capacity planning decisions, not as a weekly operational target. I also disclosed one known limitation explicitly: a one-time marketing intake surge in the historical data reduces the seasonal model's precision — a pure seasonal model interprets that surge as signal when it is actually noise. The firm should weight the forecast directionally and use the prediction intervals to bound the range. November at 122 new matters, with a lower bound around 106, is the planning scenario the operations director should stress-test against.

---

### Q6: How would you productionize this platform at an actual firm?

**Answer:**
I would approach productionization in three phases. Phase one is data connectivity: replace the CSV extract process with a direct read-replica or API connection to the firm's case management system — Filevine, Litify, or similar — using a daily or real-time sync. Phase two is orchestration: schedule the cleaning script, SQL KPI refreshes, and model scoring run on a daily cadence using Airflow or a simpler cron-based job on the firm's infrastructure; the dashboard auto-refreshes from the updated database. Phase three is model maintenance: set a quarterly model retraining schedule; monitor AUC and recall on a rolling 30-day basis; alert the analyst team if either metric drops more than 5 points from baseline. For the forecast, I would add a monthly re-fit as new actuals arrive. I would also add a data contract layer — schema validation checks that run before each load and fail loudly if, for example, a new extract contains negative settlement amounts again. That prevents the silent data quality regressions that make dashboards untrustworthy over time.

---

### Q7: Did you validate that your data sample is representative of the firm's actual population?

**Answer:**
This is an important limitation I want to be transparent about. The dataset was generated to reflect realistic plaintiff-firm operational patterns — case type mix, intake trends, settlement economics, and staffing ratios were calibrated to be plausible. However, it is synthetic, not drawn from a live case management system. That means two things: the absolute numbers (e.g., $91,709 average settlement) reflect design assumptions, not the firm's actual economics; and the predictive model was trained and tested on data from the same generating process, so its performance on real firm data could be higher or lower. In a live deployment, I would re-train the model on 12+ months of the firm's actual case history before going to production, and I would conduct a two-week parallel run — scoring cases with the model while case managers work normally — to calibrate the flag threshold against real outcomes before routing triage reports.

---

### Q8: What would you do differently if you had more time?

**Answer:**
Three things. First, I would add a survival analysis component — specifically a Cox Proportional Hazards model — to estimate time-to-workup-completion rather than just a binary completion flag. That gives the firm a predicted completion date per case, which is more useful for scheduling demand letters and settlement negotiations. Second, I would build out the attorney performance dimension more rigorously. The current dashboard shows case manager productivity, but attorney-level settlement economics — which attorney, which case type, which opposing counsel — likely contains significant signal. Third, I would connect the forecast model to the capacity-planning module by case type, not just overall volume. A forecast that says "77 completions in November" is less actionable than one that says "40 of those are mass-tort matters, which require 2x the documentation hours of an MVA case." That decomposition drives actual staffing decisions.

---
---

## 60-SECOND ELEVATOR PITCH

"I built a full-stack analytics platform for a plaintiff-side law firm managing 2,743 cases and $30 million in settled matters.

The firm's core operational problem is that 39% of the portfolio — about 848 open matters — had not completed the workup process needed to send a settlement demand. Cases were stalling, and no one could see where or why.

I designed a PostgreSQL schema with nine tables, wrote a SQL library of nine reusable KPI queries using CTEs, window functions, and SLA logic, and built a seven-page BI dashboard covering everything from the executive health check to individual case triage.

On top of that, I built two predictive layers in Python. A logistic regression model — cross-validated ROC-AUC of 0.700 — scores every case for workup completion risk and flags 184 at-risk matters for immediate intervention; I ran an adversarial review against my own feature set, caught a subtle leakage issue, fixed it, and the number I'm reporting is the honest one. And a Holt-Winters time-series forecast projects new-matter intake demand out six months — targeting intake rather than completions, because completion volume is right-censored and corrupts the back-test — showing demand softening to 122 new matters in November, the lowest point of the year, which is the window to reduce backlog.

The business case is straightforward: if the firm closes half of its completion gap — moving from 60.8% to 70% — that is roughly $13 million in incremental expected settlement value from the existing case load, with no new clients required.

That is what I built, and that is the kind of structured, business-first analysis I want to bring to this role."

---

*End of Presentation Outline*

---

> **File references:**
> - SQL queries: `/Users/rin/Legal-Case-Management-Intelligence/sql/03_kpi_queries.sql`, `04_dashboard_queries.sql`
> - Figures: `/Users/rin/Legal-Case-Management-Intelligence/python/outputs/` (all `.png` files)
> - Cleaning report: `/Users/rin/Legal-Case-Management-Intelligence/python/outputs/cleaning_report.txt`
> - Model metrics: `/Users/rin/Legal-Case-Management-Intelligence/python/outputs/model_metrics.txt`
> - Forecast data: `/Users/rin/Legal-Case-Management-Intelligence/python/outputs/forecast_workup_volume.csv`
