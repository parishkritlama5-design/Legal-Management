# Legal Case Management Intelligence — Project Documentation

A plain-English, start-to-finish explanation of the project: the business
problem, the data, the tools, the methods, **what every chart on the dashboard
means**, and the final conclusion.

---

## 1. The Business Problem

This project is built for a **plaintiff-side / mass-tort law firm** — a firm that
represents injured clients in cases like car accidents, medical malpractice, and
large mass-tort dockets (Roundup, Camp Lejeune, Talcum).

These firms make money by moving cases efficiently through a pipeline:

> **Intake → sign the client → collect medical records & documents →
> "work up" the case → send a demand → settle.**

The firm was running on **gut feel and spreadsheets**, which created six problems:

1. **No pipeline visibility** — leadership couldn't see where the ~2,180 open
   cases were stuck.
2. **A hidden records bottleneck** — collecting medical records and documents is
   the slowest stage and was quietly stretching out every case.
3. **Mass-tort underperformance** — suspected but never measured.
4. **Productivity blind spots** — case managers judged on raw counts, not on how
   many cases they actually completed given their workload.
5. **Reactive, not predictive** — the firm learned a case had stalled only after
   it aged out.
6. **Untrustworthy data** — duplicates and bad values corrupted every report.

**The goal:** replace intuition with a data platform that tracks intake, workup,
case quality, productivity, forecasting, and bottlenecks.

---

## 2. The Data

### 2a. How it was acquired
Because real client data is confidential, the project uses **synthetic
(computer-generated) data** created by `python/generate_data.py`. It uses a fixed
random seed (reproducible — same data every run), builds in realistic patterns,
and even injects realistic mistakes for the cleaning step to catch. It covers a
**24-month history (Jul 2023 → Jun 2025)** with a snapshot date of **30 Jun 2025**.

### 2b. What data was made (9 connected tables)
| Table | One row = | Rows | Key information |
|-------|-----------|-----:|-----------------|
| `clients` | one client | 2,540 | name, DOB, state, contact, intake date, referral source, marketing channel |
| `attorneys` | one attorney | 12 | name, bar state, specialty, years of experience |
| `case_managers` | one manager | 18 | name, team, monthly capacity |
| `cases` | **one legal matter** | 2,743 | case type, state, dates, status, current stage, manager, attorney, days in stage, records received, missing docs, communication count, **workup completed**, outcome, settlement amount |
| `activities` | one staff touchpoint | ~17,400 | type, date, duration |
| `documents` | one document | ~15,100 | type, status (received/missing/pending) |
| `medical_records` | one record | ~5,900 | provider, requested/received dates, pages |
| `settlements` | one settled case | 329 | gross amount, fee, liens, net to client |
| `call_logs` | one phone call | ~15,000 | direction, duration, outcome |

Cases move through an **8-stage workup funnel**: Intake → Retainer Signed →
Records Requested → Records Received → Workup Complete → Demand Sent →
Negotiation → Resolved.

### 2c. How it was cleaned (`python/01_data_cleaning.py`)
| Problem found | Count | Handling |
|---------------|------:|----------|
| Duplicate clients (same name + DOB) | 40 | merged; cases re-pointed to surviving client |
| Negative settlement amounts | 8 | corrected (sign error) |
| Negative "days in stage" | 10 | corrected |
| Close date before open date | 6 | flagged & blanked for review |
| Missing emails | 76 (3%) | flagged |
| Missing referral source | 50 | filled with "Unknown" |

Result: **2,500 unique clients** after de-duplication.

### 2d. How it was made analysis-ready
Cleaning also adds calculated columns — `is_open`, `days_to_close`,
`case_age_days`, `days_inactive`, `intake_month` — and saves the finished tables
to `data/processed/`.

---

## 3. Tools Used

| Tool / library | What it is | Used for |
|----------------|-----------|----------|
| **Python** | general programming language | the engine for everything below |
| **pandas** | data tables in Python | loading, cleaning, aggregating the data |
| **NumPy** | numerical computing | the random data generator and math |
| **scikit-learn** | machine-learning library | the forecast (Ridge regression) and the workup-completion classifier (Logistic Regression / Random Forest) |
| **Matplotlib** | charting library | the static analysis charts in `python/outputs/` |
| **Plotly** | interactive charting library | the **interactive HTML dashboard** |
| **SQL (PostgreSQL)** | database query language | the schema, KPI queries, and data-quality checks in `sql/` |
| **HTML + CSS** | web page structure & styling | the dashboard layout (KPI tiles, grid) |
| **Git + GitHub** | version control & hosting | storing the project |
| **GitHub Pages** | free static web hosting | publishing the live dashboard URL |

**In short:** the analysis is **Python + SQL**; the dashboard is **Python +
Plotly + HTML/CSS**; hosting is **GitHub + GitHub Pages**.

---

## 4. Analytical Methodology

### 4a. SQL
The `sql/` folder holds the schema and analytical queries (PostgreSQL), using
**CTEs**, **window functions** (`RANK`, `LAG`, running totals), **CASE**
statements, and dedicated **data-quality** checks.

### 4b. Python analysis & models
- **EDA** (`02_eda.py`) — profiles the data and produces static charts.
- **Forecasting** (`03_forecasting.py`) — predicts **monthly workup demand** (new
  matters per month) using **Ridge regression** with a **trend** term and
  **month-of-year seasonality**. Validated by a **back-test** (hold out the last
  4 months, predict them): **MAPE ≈ 12.5%**.
- **Predictive model** (`04_predictive_model.py`) — predicts **whether a case
  will complete workup** (Logistic Regression vs. Random Forest), scored with
  accuracy, precision, recall, ROC-AUC, and 5-fold cross-validation. Fields that
  would "leak" the answer were deliberately excluded to keep it honest.

### 4c. How the dashboard was made
The interactive dashboard (`python/build_dashboard.py` →
`dashboards/legal_case_dashboard.html`) is built with **Python + Plotly**. The
script reads the cleaned data, builds each chart, and writes **one
self-contained HTML file** (the Plotly engine is embedded, so it works offline by
double-clicking). It is published live via **GitHub Pages**. It follows the
7-page design spec in `dashboards/dashboard_specifications.md`.

---

## 5. The Dashboard — chart by chart

The dashboard has a row of KPI tiles, a full-width forecast, then a grid of
charts. Every chart is built with **Plotly** from `data/processed/cases_clean.csv`
(the forecast also uses `python/outputs/forecast_workup_volume.csv`).

### 5a. KPI tiles (the headline numbers)
**What it shows:** six big numbers — Total Cases (**2,743**), Open Cases
(**2,180 / 79.5%**), Workup Completion (**60.8%**), Settlement Rate (**57.8%**),
Settlement Value (**$30.2M**), and Stalled >30 days.
**How to read:** a one-glance health check of the whole firm.
**Built with:** Plotly/HTML text tiles from `cases` fields.

### 5b. Client Workup Funnel
**What it shows:** how many cases have reached **or passed** each of the 8 stages,
from Intake (all cases) down to Resolved (few).
**How to read:** each bar is shorter than the one above it; the biggest drop
between two bars is where cases leak out of the pipeline.
**Finding:** cases thin out around the **records and workup** stages.
**Built with:** Plotly funnel; from `current_stage`.

### 5c. Workup Completion Rate by Case Type
**What it shows:** the % of cases of each type that finished workup, with a dashed
**firm-average line**.
**How to read:** green bars are above average, coral bars below.
**Finding (the sharpest one):** regular injury cases finish far more often than
mass torts — Dog Bite **75%**, Motor Vehicle **74%** vs. Roundup **51%**, Camp
Lejeune **44%**, Talcum **41%** — a ~30-point gap.
**Built with:** Plotly bar; from `case_type` + `workup_completed`.

### 5d. Monthly Workup Demand — Actual & 6-Month Forecast
**What it shows:** new matters entering the pipeline each month — the navy line is
**actual** history, the dashed coral line is the **6-month forecast** (~162, 157,
147, 154, 122, 127), and the shaded band is the **80% interval**.
**How to read:** the band is the range of likely values; it **widens further into
the future** because longer-range forecasts are less certain. ~80% chance the
real number lands inside the band.
**Finding:** demand (~120–160/month) runs higher than completion throughput
(~90/month) — **the gap is the backlog growing.**
**Built with:** Plotly lines + shaded band; from `python/outputs/forecast_workup_volume.csv`,
which is produced from the `date_opened` field by a **Ridge regression**
(trend + seasonality). The band comes from the back-test error.

### 5e. Case-Manager Productivity
**What it shows:** each of the 18 managers and their **workup completion rate**
(caseload shown on hover).
**How to read:** sorted so you instantly see top and bottom performers — but it's
completion *rate*, so it's fair to managers with different workloads.
**Finding:** real performance differences emerge that raw case counts would hide.
**Built with:** Plotly bar; `cases` joined to `case_managers` for names.

### 5f. Operational Bottleneck — Open Cases & Avg Days by Stage
**What it shows:** a **dual-axis** chart — navy **bars** = how many *open* cases
sit in each stage; coral **line** = the average days they've waited there.
**How to read:** a tall bar = cases piling up; a high line = long waits. A
**bottleneck** is where you see both.
**Finding:** open cases bunch up and age in the **later stages** (Workup Complete,
Demand Sent, Negotiation) — where demands and negotiations happen.
**Built with:** Plotly bar + line on two axes; filtered to `is_open = 1`.

### 5g. Case Mix by Type
**What it shows:** how many cases of each type the firm holds.
**How to read:** longest bar = biggest segment.
**Finding:** **Motor Vehicle Accident** is the largest segment (~771 cases).
**Built with:** Plotly bar; from `case_type`.

### 5h. Case Status Distribution
**What it shows:** a donut of the case statuses (active stages, settled, closed,
dropped).
**How to read:** the share of the book that is active vs. resolved.
**Built with:** Plotly pie; from `case_status`.

---

## 6. Final Conclusion

The data tells one consistent story:

> **The firm takes in more cases than it can work up, loses the most time and
> value at the medical-records stage, and converts mass-tort cases at barely half
> the rate of its regular work — and all three problems are operationally
> fixable.**

Because settled cases average **~$92,000**, even a small lift in workup completion
(especially on mass torts) is worth a lot of money.

**Recommended actions:**
1. **Fix the records bottleneck** — a dedicated records-chasing team and a
   deadline (SLA) on each stage.
2. **Close the mass-tort gap** — a standardized mass-tort workup playbook, or
   tighter qualification at intake.
3. **Use the at-risk model** — feed flagged cases into a weekly triage so
   stalling cases get attention *before* they age out.
4. **Plan to capacity** — staff the workup team against the demand forecast.
5. **Govern the data** — stop duplicates and bad values at the source.

**The honest-analysis point:** the modeling was deliberately stress-tested. An
adversarial review caught a subtle data leak; it was removed and the accuracy was
re-reported (slightly lower, but trustworthy). **A number you can defend beats a
higher number you can't.** Full detail in
`documentation/methodology_and_limitations.md`.

---

*All data is synthetic; no real client information is used. Built to demonstrate
end-to-end analytics and business-analysis capability for legal operations.*
