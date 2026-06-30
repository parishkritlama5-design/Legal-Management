# Legal Case Management Intelligence — Project Documentation

A plain-English, start-to-finish explanation of the project: the business
problem, the data, the methods, what the dashboard shows, and the conclusion.

---

## 1. The Business Problem

This project is built for a **plaintiff-side / mass-tort law firm** — the kind of
firm that represents injured clients in cases like car accidents, medical
malpractice, and large mass-tort dockets (Roundup, Camp Lejeune, Talcum).

These firms make money by moving cases efficiently through a pipeline:

> **Intake → sign the client → collect medical records & documents →
> "work up" the case → send a demand → settle.**

The firm in this project was running on **gut feel and spreadsheets**, and that
created six real problems:

1. **No pipeline visibility** — leadership couldn't see where the ~2,180 open
   cases were stuck.
2. **A hidden records bottleneck** — collecting medical records and documents is
   the slowest stage, and it was quietly stretching out every case.
3. **Mass-tort underperformance** — the firm suspected mass-tort cases finished
   workup less often than regular injury cases, but nobody had measured it.
4. **Productivity blind spots** — case managers were judged on raw case counts,
   not on how many they actually completed given their workload.
5. **Reactive, not predictive** — the firm only learned a case had stalled
   *after* it had aged out.
6. **Untrustworthy data** — duplicate clients and bad values quietly corrupted
   every report.

**The goal:** replace intuition with a data platform that tracks intake, workup,
case quality, productivity, forecasting, and bottlenecks — i.e., give leadership
the numbers they need to make decisions.

---

## 2. The Data

### 2a. How the data was acquired
Because real client data is confidential, the project uses **synthetic
(computer-generated) data** created by a Python script
(`python/generate_data.py`). The script was written to behave like a real firm's
system: it uses a fixed random seed so it produces the **exact same data every
time** (reproducible), and it deliberately builds in realistic patterns and even
realistic mistakes (see cleaning, below).

The data covers a **24-month history (July 2023 → June 2025)**, with a "today"
snapshot date of **30 June 2025**.

### 2b. What data was made
Nine connected tables — three "reference" tables (the *who*) and six
"activity/fact" tables (the *what*):

| Table | One row = | Rows | Key information |
|-------|-----------|-----:|-----------------|
| `clients` | one client | 2,540 | name, DOB, state, contact, intake date, referral source, marketing channel |
| `attorneys` | one attorney | 12 | name, bar state, specialty, years of experience |
| `case_managers` | one manager | 18 | name, team, monthly capacity |
| `cases` | **one legal matter** | 2,743 | case type, state, dates, status, current stage, assigned manager & attorney, days in stage, records received, missing documents, communication count, **whether workup completed**, outcome, settlement amount |
| `activities` | one staff touchpoint | ~17,400 | activity type, date, duration |
| `documents` | one document | ~15,100 | type, status (received / missing / pending) |
| `medical_records` | one record | ~5,900 | provider, requested/received dates, page count |
| `settlements` | one settled case | 329 | gross amount, attorney fee, liens, net to client |
| `call_logs` | one phone call | ~15,000 | direction, duration, outcome |

The cases move through an **8-stage workup funnel**:
**Intake → Retainer Signed → Records Requested → Records Received → Workup
Complete → Demand Sent → Negotiation → Resolved.**

### 2c. How the data was cleaned
The generator intentionally injected realistic errors so the cleaning step
(`python/01_data_cleaning.py`) had real work to do. It found and fixed:

| Problem found | Count | How it was handled |
|---------------|------:|--------------------|
| Duplicate clients (same name + DOB) | 40 | merged into one record; cases re-pointed to the surviving client |
| Negative settlement amounts | 8 | corrected (sign-entry error) |
| Negative "days in stage" | 10 | corrected |
| Close date before open date | 6 | flagged and blanked for review |
| Missing emails | 76 (3%) | flagged |
| Missing referral source | 50 | filled with "Unknown" |

After cleaning, the client count drops from 2,540 to **2,500 unique clients**.

### 2d. How the data was made "analysis-ready"
The cleaning step also **adds helpful calculated columns** so downstream analysis
is easy, including: `is_open` (is the case still active?), `days_to_close`,
`case_age_days`, `days_inactive` (for the "stalled case" alerts), and
`intake_month`. The clean, ready-to-use tables are saved to
`data/processed/`.

---

## 3. Analytical Methodology

The analysis happens in three layers: **SQL**, **Python**, and the **dashboard**.

### 3a. SQL (querying the data)
The `sql/` folder holds the database schema and the analytical queries, written
in PostgreSQL using **advanced SQL techniques**:
- **CTEs** (named sub-queries) to build the funnel and KPIs step by step.
- **Window functions** (`RANK`, `LAG`, `ROW_NUMBER`, running totals) for ranking
  case managers, month-over-month growth, and stage conversion.
- **CASE statements** for bucketing (e.g., grouping stalled cases into
  31–60 / 61–90 / 90+ day buckets).
- **Data-quality checks** for duplicates, impossible values, and orphan records.

### 3b. Python (analysis, forecasting, machine learning)
- **Exploratory analysis** (`02_eda.py`) — profiled the data and produced charts
  (funnel, completion by type, cycle time).
- **Forecasting** (`03_forecasting.py`) — predicts **monthly workup demand** (new
  matters entering the pipeline) for the next 6 months using a regression model
  with trend + seasonality. It is honestly tested with a **back-test** (hold out
  the last 4 months, predict them, measure the error): **MAPE 12.5%** (average
  error ~12.5%).
- **Predictive model** (`04_predictive_model.py`) — predicts **whether a case
  will complete workup**, so the firm can flag at-risk cases early. It compares
  Logistic Regression and Random Forest, and is evaluated with accuracy,
  precision, recall, and ROC-AUC, plus 5-fold cross-validation.

**One important methodology note (data leakage):** the target is "did the case
complete workup," so any field that secretly reveals the answer was *excluded*
from the model (current stage, status, outcome, settlement amount, close date,
and `days_in_stage`). This keeps the model honest — its accuracy reflects real,
early-known information, not a peek at the answer.

### 3c. How the dashboard was made
The **interactive HTML dashboard** (`python/build_dashboard.py` →
`dashboards/legal_case_dashboard.html`) is built with **Python + Plotly**. It
reads the cleaned data, builds each chart, and writes one self-contained HTML
file that works offline in any browser. It is published live with GitHub Pages.

It follows the design spec in `dashboards/dashboard_specifications.md`
(7 pages: Executive Overview, Funnel, Productivity, Quality, Forecasting, Data
Quality, Bottlenecks).

---

## 4. Dashboard Walkthrough (the findings)

What each part of the dashboard shows:

**KPI tiles (top row)** — the firm at a glance:
- **2,743** total cases, **2,180 (79.5%)** still open
- **60.8%** workup completion rate
- **57.8%** settlement rate (of resolved cases)
- **$30.2M** total settlement value tracked
- a count of cases **stalled >30 days** with no activity

**Workup Funnel** — shows how cases thin out from Intake down to Resolved. The
biggest drop-offs cluster around the **records stages**, confirming where cases
get stuck.

**Completion Rate by Case Type** — the sharpest finding. Regular injury cases
finish workup far more often than mass torts:
- Dog Bite **75%**, Motor Vehicle Accident **74%**, Premises **65%**
- Roundup **51%**, Camp Lejeune **44%**, Talcum **41%**
A ~30-point gap on high-volume mass-tort dockets.

**Demand Forecast** — projected new matters per month for the next 6 months
(~162, 157, 147, 154, 122, 127), with a confidence band. Demand (~120–160/month)
runs higher than completion throughput (~90/month) — **the gap is the backlog
growing.**

**Case-Manager Productivity** — completion rate per manager (caseload-adjusted),
so leadership can see real performance, not just raw counts.

**Operational Bottleneck** — open cases and average days-in-stage per stage. The
records stages carry the most open cases and the longest waits.

**Case Mix & Status** — Motor Vehicle Accident is the largest segment; the status
breakdown shows how much of the book is active vs. resolved.

---

## 5. Final Conclusion

The data tells a clear, consistent story:

> **The firm is taking in more cases than it can work up, loses the most time and
> value at the medical-records stage, and converts mass-tort cases at barely half
> the rate of its regular injury work — and all three problems are operationally
> fixable.**

Because settled cases average **~$92,000**, even a small lift in workup
completion (especially on the lagging mass-tort dockets) is worth a lot of money.

**Recommended actions:**
1. **Fix the records bottleneck** — a dedicated records-chasing team and a
   service-level deadline on each stage.
2. **Close the mass-tort gap** — a standardized mass-tort workup playbook, or
   tighter qualification at intake.
3. **Use the at-risk model** — feed the flagged cases into a weekly triage so
   stalling cases get attention *before* they age out.
4. **Plan to capacity** — staff the workup team against the demand forecast
   instead of reacting to backlog.
5. **Govern the data** — prevent duplicates and bad values at the source so every
   report stays trustworthy.

**The honest-analysis point:** the modeling was deliberately stress-tested. An
adversarial review caught a subtle data leak; it was removed and the accuracy was
re-reported (slightly lower, but trustworthy). The headline is simple — **a
number you can defend beats a higher number you can't.**

---

*All data is synthetic; no real client information is used. Built to demonstrate
end-to-end analytics and business-analysis capability for legal operations.*
