# Legal Case Management Intelligence Platform
## Dashboard Specification Document

**Project:** Legal Case Management Intelligence Platform
**Firm Type:** Plaintiff-Side / Mass Tort Law Firm
**BI Tool:** Power BI or Sigma Computing (specification is tool-agnostic; notes flag tool-specific implementation where relevant)
**Data Snapshot Date:** 2025-06-30
**Document Version:** 1.0
**Prepared:** 2026-06-29

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Global Filter and Slicer Strategy](#2-global-filter-and-slicer-strategy)
3. [Color and Format Style Guide](#3-color-and-format-style-guide)
4. [Data Architecture and Refresh Cadence](#4-data-architecture-and-refresh-cadence)
5. [Page 1 — Executive Overview](#5-page-1--executive-overview)
6. [Page 2 — Client Workup Funnel](#6-page-2--client-workup-funnel)
7. [Page 3 — Case Manager Productivity](#7-page-3--case-manager-productivity)
8. [Page 4 — Case Quality Analytics](#8-page-4--case-quality-analytics)
9. [Page 5 — Forecasting Dashboard](#9-page-5--forecasting-dashboard)
10. [Page 6 — Data Quality Dashboard](#10-page-6--data-quality-dashboard)
11. [Page 7 — Operational Bottleneck Dashboard](#11-page-7--operational-bottleneck-dashboard)
12. [Screenshots Checklist](#12-screenshots-checklist)

---

## 1. Design Principles

### 1.1 Audience-First Design

Each dashboard page is built around a single, clearly stated question that a specific audience must answer on a regular basis. Visual complexity is calibrated to the audience: firm leadership receives high-level aggregates with one-click drill paths; case managers receive operational worklists with individual-level detail. No page mixes audiences without a clear visual hierarchy separating their respective elements.

### 1.2 Honest Encoding

All bar and column charts use a zero-based value axis. No axis truncation is permitted. Dual-axis charts are prohibited unless both series share the same unit (e.g., two count series), in which case a note must confirm the scales are aligned. Area charts are reserved for cumulative quantities only. Pie and donut charts are limited to five or fewer segments and are used solely for part-of-whole relationships where the whole is meaningful; any segment under 3% is collapsed into an "Other" category. No 3D chart types are used anywhere in the portfolio.

Funnel charts represent the genuine cumulative pipeline, not stage-to-stage snapshots, because a case at "Demand Sent" has by definition passed through all prior stages. This avoids the visual implication that cases leave the firm between stages when they have not.

### 1.3 Accessibility

The default palette (Section 3) is colorblind-safe, validated against protanopia and deuteranopia simulations. Color is never the sole encoding; shape, position, or direct labels always carry the same information redundantly. All text meets WCAG AA contrast ratios (4.5:1 minimum for body, 3:1 for large headings). Tooltip text is enabled on all visuals for screen-reader compatibility in Sigma. In Power BI, alt-text is set on every visual object.

### 1.4 Consistent Formatting

Number format rules are applied globally via a style guide (Section 3). Titles follow the "insight-first" convention: the title states the takeaway or question, not merely the chart type (e.g., "Workup Completion Trails Intake by 39 Points" rather than "Bar Chart of Completion Rates"). Axis labels always include units. All percentages display one decimal place. Currency values display in dollars with a thousands separator and no cents (e.g., $91,709). Large dollar values use abbreviated notation (e.g., $30.2M) in KPI tiles only, with full precision available in tooltips.

### 1.5 Drill Path

Every dashboard follows a three-tier drill path: firm level (Executive Overview) → segment level (by case type, team, or stage) → case level (individual case worklist or detail table). Cross-page navigation buttons are placed consistently in the lower-right corner of each page. Selecting a bar segment or funnel stage on any aggregated visual filters the detail table on that same page to the subset, and also sets a page-level context bookmark that downstream pages respect via report-level filters where the BI tool supports it.

---

## 2. Global Filter and Slicer Strategy

The following slicers appear on a persistent filter panel (collapsible side panel in Sigma; a dedicated filter pane in Power BI) on every dashboard page. They operate as cross-page report filters unless a page-level override is documented in that page's specification.

| Slicer | Field | Type | Default |
|---|---|---|---|
| Date Range | `cases.intake_date` | Date range picker | Rolling 24 months |
| Case Type | `cases.case_type` | Multi-select dropdown | All selected |
| Case Status | `cases.case_status` | Multi-select checkbox | All selected |
| State | `cases.state` | Multi-select dropdown | All selected |
| Assigned Attorney | `attorneys.attorney_name` | Single-select dropdown | All |
| Assigned Case Manager | `case_managers.manager_name` | Multi-select dropdown | All selected |
| Current Stage | `cases.current_stage` | Multi-select checkbox | All selected |

**Implementation note:** The Date Range slicer filters on `intake_date` by default. Pages 5 (Forecasting) and 7 (Bottleneck) expose a secondary date filter on `date_opened` and `last_activity_date` respectively, allowing independent control without disrupting the global context.

**Reset button:** A "Clear All Filters" button is pinned to the top-right of the filter panel, resetting all slicers to their defaults in a single click.

---

## 3. Color and Format Style Guide

### 3.1 Categorical Palette (Case Type / Segment Differentiation)

This palette is Okabe-Ito, the most widely adopted colorblind-safe categorical palette. It distinguishes up to eight categories without ambiguity under the three most common forms of color vision deficiency.

| Slot | Hex | Name | Primary Use |
|---|---|---|---|
| C1 | `#E69F00` | Amber | Motor Vehicle Accident / primary series |
| C2 | `#56B4E9` | Sky Blue | Mass Tort series |
| C3 | `#009E73` | Bluish Green | Settled / positive outcome |
| C4 | `#F0E442` | Yellow | Warning / at-risk flag |
| C5 | `#0072B2` | Blue | Firm-wide benchmark / reference line |
| C6 | `#D55E00` | Vermillion | Alert / SLA breach / negative |
| C7 | `#CC79A7` | Reddish Purple | Secondary series |
| C8 | `#999999` | Grey | Inactive / suppressed / "Other" |

For more than eight categories, use C8 (Grey) for the combined "Other" segment and label it explicitly.

### 3.2 Sequential / Diverging Scales

| Use Case | Scale | Notes |
|---|---|---|
| Completion rate heatmap | White (#FFFFFF) to Bluish Green (`#009E73`) | Zero = white; 100% = full green |
| SLA compliance | Diverging: Vermillion (`#D55E00`) at 0% through Amber (`#E69F00`) at 50% to Bluish Green (`#009E73`) at 100% | Midpoint label states the SLA target |
| Data quality severity | White to Vermillion | More issues = deeper red |
| Forecast confidence interval | Sky Blue (`#56B4E9`) at 20% opacity | Shaded band around point forecast |

### 3.3 Number Formats

| Value Type | Format | Example |
|---|---|---|
| Count | Integer, thousands separator | 2,743 |
| Percentage | One decimal place, % suffix | 60.8% |
| Currency (KPI tile) | $M abbreviated, one decimal | $30.2M |
| Currency (table) | Dollar, thousands separator, no cents | $91,709 |
| Days | Integer, "d" suffix in labels | 14d |
| Ratio | Two decimal places | 1.24 |

### 3.4 Typography and Layout

- **Page title:** 20pt, bold, firm brand color (default: `#0072B2`)
- **Section header:** 14pt, semi-bold
- **KPI tile value:** 28pt, bold
- **KPI tile label:** 11pt, regular, grey (`#555555`)
- **Axis labels and legends:** 10pt, regular
- **Source/date footer:** 9pt, italic, grey — appears on every page: "Source: Case Management System | Snapshot: 2025-06-30 | n = 2,743 cases"

---

## 4. Data Architecture and Refresh Cadence

### 4.1 Data Flow

```
Case Management System (operational)
        |
        v
CSV Extracts (scheduled export, 9 tables)
        |
        v
Data Warehouse / PostgreSQL (star schema)
  dimensions: clients, attorneys, case_managers
  facts:       cases, activities, documents,
               medical_records, settlements, call_logs
        |
        v
BI Semantic Layer (views from 04_dashboard_queries.sql)
        |
        v
Power BI / Sigma Computing (dashboard pages)
```

The Python cleaning scripts (`01_data_cleaning.py`) produce `data/processed/cases_clean.csv` and `clients_clean.csv`, which feed the warehouse load (`02_load_data.sql`). Dashboard queries in `04_dashboard_queries.sql` are implemented as warehouse views. The BI tool connects to these views in DirectQuery mode (Sigma) or Import mode with scheduled refresh (Power BI).

### 4.2 Refresh Cadence

| Layer | Frequency | Notes |
|---|---|---|
| CSV export from case system | Daily, 02:00 local | Automated job; alert on failure |
| Warehouse load | Daily, 03:00 local | After CSV export completes |
| BI semantic layer (views) | On-demand / real-time | Views recompute at query time |
| Power BI scheduled refresh | Daily, 06:00 local | Imports from views into Power BI dataset |
| Forecast model output | Monthly, 1st of month | `python/03_forecasting.py` writes `forecast_workup_volume.csv`; loaded as static table |
| Predictive model output | Monthly, 1st of month | `python/04_predictive_model.py` writes `predictions.csv`; joined to cases view |

### 4.3 Data Model Summary

| Table | Type | Row Count (approx.) | Key Join Field |
|---|---|---|---|
| `clients` | Dimension | 2,500 distinct | `client_id` |
| `attorneys` | Dimension | 12 rows | `attorney_id` |
| `case_managers` | Dimension | 18 rows | `case_manager_id` |
| `cases` | Core Fact | 2,743 rows | `case_id`, `client_id` |
| `activities` | Sub-Fact | Variable | `case_id`, `case_manager_id` |
| `documents` | Sub-Fact | Variable | `case_id` |
| `medical_records` | Sub-Fact | Variable | `case_id` |
| `settlements` | Sub-Fact | Variable | `case_id` |
| `call_logs` | Sub-Fact | Variable | `case_id`, `case_manager_id` |

---

## 5. Page 1 — Executive Overview

### 5.1 Purpose

Provide firm leadership with a single-screen summary of portfolio health: caseload size, workup throughput, settlement economics, and pipeline risk. This page requires no interaction for the baseline read — the key metrics are visible without scrolling or filtering.

### 5.2 Target Audience

Managing partners, senior attorneys, firm administrators. Consumption frequency: daily morning review (30–60 seconds); monthly board-level reporting.

### 5.3 KPI Metric Tiles

Six KPI tiles in a single horizontal row at the top of the page.

| Tile | Metric Name | Definition | Format | Source Query |
|---|---|---|---|---|
| T1 | Total Cases | `COUNT(*)` from `cases` | Integer | Query 1.1 |
| T2 | Open Cases | `COUNT(*) FILTER (WHERE date_closed IS NULL)` | Integer, % of total in subtext | Query 1.1 |
| T3 | Workup Completion | `ROUND(100.0 * SUM(workup_completed) / COUNT(*), 1)` | Percent | Query 1.1 |
| T4 | Settlement Rate | Settled cases / resolved cases (Settled + Closed-Lost + Dropped) | Percent | Query 1.1 |
| T5 | Total Settlement Value | `SUM(settlement_amount) WHERE settlement_amount > 0` | $M, 1 decimal | Query 1.1 |
| T6 | Stalled Cases | Open cases with `last_activity_date` > 30 days ago | Integer, red if > 0 | Query 1.1 |

**Contextual footnote below tiles:** "Settlement rate computed on resolved cases only (n = 563). Open pipeline: 2,180 cases (79.5%). Snapshot: 2025-06-30."

**Conditional formatting on T6 (Stalled Cases):** Tile background shifts to Vermillion (`#D55E00`) if the count exceeds a configurable threshold (default: 50 cases). This is the only use of conditional color on a KPI tile; the mechanism is documented so it is not mistaken for a selection state.

### 5.4 Charts and Visuals

#### Visual 1-A: Case Mix by Type (Horizontal Bar Chart)

- **Visual type:** Horizontal bar chart, sorted descending by case count
- **X-axis:** Case count (integer), zero-baselined
- **Y-axis:** Case type (12 categories)
- **Color:** Single color (C1 Amber) for all bars — color differentiation is not needed here because position on the categorical axis already encodes type identity. A single-hue chart avoids implying that the colors carry meaning.
- **Data labels:** Count and percentage of book displayed inline at the end of each bar
- **Title:** "Case Mix — Motor Vehicle Accident Leads at ~28% of Portfolio"
- **Why horizontal bars:** With 12 category labels, vertical bars would require angled or rotated text. Horizontal bars allow full label legibility at a normal reading size. Length from a common zero baseline encodes quantity precisely — more accurate than angle (pie) or area.
- **Source query:** Query 1.2 (`04_dashboard_queries.sql` — Case mix by type)

#### Visual 1-B: Open Pipeline Expected Value by Case Type (Stacked Horizontal Bar Chart)

- **Visual type:** Horizontal bar chart showing `expected_pipeline_value` per case type, sorted descending
- **X-axis:** Expected pipeline value in dollars ($M), zero-baselined
- **Y-axis:** Case type
- **Color:** Single hue (C2 Sky Blue) — same rationale as 1-A; the metric is one-dimensional
- **Tooltip:** On hover shows `open_cases`, `avg_settlement`, and `expected_pipeline_value` for the type
- **Annotation:** A vertical reference line at the firm-wide average expected value per type, labeled "Firm Avg"
- **Title:** "Open Pipeline Expected Value — Where Economic Exposure Sits"
- **Caveat note beneath chart:** "Expected value = open cases × type-level average settlement × type-level settlement rate. This is a probabilistic estimate, not a guarantee. Cases with no settled comparables are excluded."
- **Why this encoding:** Bar length from zero is the most accurate positional encoding for a scalar quantity. A table alone would require mental arithmetic to identify the dominant segments; the bar chart externalizes that comparison instantly. The explicit caveat is mandatory to prevent leadership from treating expected value as booked revenue.
- **Source query:** Query 1.3 (`04_dashboard_queries.sql` — Open pipeline value estimate)

#### Visual 1-C: Monthly Intake Trend with 3-Month Rolling Average (Line Chart)

- **Visual type:** Line chart with dual series — monthly new clients (thin line, C8 Grey) and 3-month rolling average (thicker line, C5 Blue)
- **X-axis:** Month (Jul 2023 – Jun 2025, 24 points)
- **Y-axis:** New clients per month, zero-baselined
- **Color:** Grey for raw monthly counts (recedes), Blue for the rolling average (prominent). The rolling average line is the signal; the monthly count is the noise context.
- **Annotation:** A horizontal reference line at the 24-month mean intake, labeled with its value
- **Title:** "Monthly Client Intake — 24-Month Trend (with 3-Month Rolling Average)"
- **Why line chart:** Time-series data. Connecting points with a line correctly implies continuity over time. The rolling average overlay reduces noise and reveals the underlying trend without hiding the variability that leadership needs to understand seasonal demand.
- **Source query:** KPI Query 9 (`03_kpi_queries.sql` — Monthly intake trends with MoM growth and rolling average)

### 5.5 Filters and Slicers

Global filter panel applies. No page-specific overrides. Default date range covers the full 24-month intake history (Jul 2023 – Jun 2025).

### 5.6 Business Questions Answered

1. How large is the firm's current caseload, and how many matters remain open?
2. What share of matters have completed the workup process, and is this improving or declining over time?
3. What is the financial value of the portfolio — both realized (settlements) and unrealized (open pipeline)?
4. Which case types dominate the book, and where does economic exposure concentrate?
5. Are any cases going stale and requiring immediate management attention?

---

## 6. Page 2 — Client Workup Funnel

### 6.1 Purpose

Track the litigation pipeline through eight sequential workup stages. Identify where matters stall, which stage transitions have the lowest conversion rates, and which intake channels produce the most complete workups.

### 6.2 Target Audience

Director of Client Services, senior case managers, intake coordinators. Consumption frequency: weekly review meeting; daily monitoring by intake team leads.

### 6.3 KPI Metric Tiles

| Tile | Metric Name | Definition | Format | Source Query |
|---|---|---|---|---|
| T1 | Cases in Active Workup | Open cases between Retainer Signed and Workup Complete | Integer | Query 2.1 |
| T2 | Funnel Conversion (Intake → Resolved) | Resolved count / Intake count | Percent | Query 2.1 |
| T3 | Overall Workup Completion Rate | `SUM(workup_completed) / COUNT(*)` across all cases | Percent (60.8%) | Query 1.1 |
| T4 | Largest Single-Stage Dropout | Stage with the greatest absolute case count reduction from the prior stage | Stage name + count lost | Query 2.1 |

### 6.4 Charts and Visuals

#### Visual 2-A: Workup Pipeline Funnel (Funnel Chart)

- **Visual type:** Funnel chart — one horizontal band per stage, width proportional to case count
- **Stages (top to bottom):** Intake → Retainer Signed → Records Requested → Records Received → Workup Complete → Demand Sent → Negotiation → Resolved
- **Color:** Single sequential hue (Bluish Green, C3) ranging from light (top, high count) to full saturation (bottom, lowest count). A single sequential hue correctly communicates a gradient of funnel penetration without implying categories.
- **Labels on each band:** Stage name, case count, and percentage of intake (e.g., "Records Received — 1,840 | 67.1% of Intake")
- **Between-stage annotations:** Stage-to-stage conversion rate displayed in the gap between bands (e.g., "↓ 82.3% advance")
- **Title:** "Client Workup Pipeline — Stage Conversion and Drop-off"
- **Why funnel chart:** The data structure is genuinely cumulative and sequential. A funnel chart maps directly to this semantics: each band is a superset of the band below it (every case at "Records Received" also passed through "Intake"). A bar chart of at-or-beyond counts would be less intuitive; a bar chart of only-at-stage counts would misrepresent the pipeline by suggesting cases exit the firm between stages rather than stalling.
- **SLA reference table below funnel:** A compact table showing SLA target days per stage alongside the observed average days in stage, with a red flag icon if the average exceeds the SLA target.

| Stage | SLA Target (days) | Avg Days in Stage | SLA Status |
|---|---|---|---|
| Intake | 3 | — | — |
| Retainer Signed | 5 | — | — |
| Records Requested | 30 | — | — |
| Records Received | 21 | — | — |
| Workup Complete | 14 | — | — |
| Demand Sent | 21 | — | — |
| Negotiation | 45 | — | — |

*(Avg Days in Stage values are populated from the live query at render time.)*

- **Source query:** Query 2.1 (`04_dashboard_queries.sql` — Funnel counts at-or-beyond each stage)

#### Visual 2-B: Workup Completion Rate by Case Type (Horizontal Bar Chart with Benchmark Line)

- **Visual type:** Horizontal bar chart, sorted descending by completion rate
- **X-axis:** Completion rate (%), zero to 100%, zero-baselined
- **Y-axis:** Case type (12 categories)
- **Color:** Diverging fill — bars at or above the firm average (60.8%) fill in Bluish Green (C3); bars below fill in Vermillion (C6). The firm-wide average is encoded redundantly as a vertical reference line labeled "Firm Avg 60.8%".
- **Data labels:** Completion percentage at end of each bar
- **Title:** "Completion Rate by Case Type — Mass Torts Trail Firm Average by 10–20 Points"
- **Why diverging color on bars:** The 12 categories form a natural comparison against a meaningful benchmark (firm average). Coloring by above/below benchmark makes the at-a-glance read unambiguous. Using two hues is justified because both hues encode the same dimension (above vs. below) and the reference value is explicitly stated. This is distinct from a rainbow palette where colors carry no structured meaning.
- **Known values to verify against live data:** Dog Bite 75.2%, Motor Vehicle Accident 73.5%, Premises Liability 64.6%, Workers Comp 62.8%, Slip and Fall 56.5%, Nursing Home 56.3%, Product Liability 54.9%, Medical Malpractice 51.6%, Mass Tort-Roundup 51.4%, Wrongful Death 50.0%, Mass Tort-Camp Lejeune 43.9%, Mass Tort-Talcum 41.3%.
- **Source query:** KPI Query 2 (`03_kpi_queries.sql` — Case completion rate by type)

#### Visual 2-C: Workup Completion by Referral Source (Grouped Bar Chart)

- **Visual type:** Grouped bar chart — two bars per referral source: case count and completion rate (secondary bar or dot overlay)
- **Implementation note:** Because case count and completion rate are different units, this visual uses a bar for case count (left axis, counts) and a dot/lollipop for completion rate (right axis, %). Both axes start at zero. The right axis maximum is fixed at 100% regardless of the data range, so the rate scale is always honest. A brief note explains the dual-axis: "Left axis: case volume. Right axis: % completing workup. Scales are independent."
- **Color:** Count bars in C1 (Amber); rate dots in C5 (Blue). Shape differentiates encoding (bar vs. dot) so color is a secondary redundant cue.
- **Title:** "Referral Sources — Volume vs. Workup Conversion Rate"
- **Why this encoding:** This chart answers a specific business question: which intake channels produce high-quality leads that convert to completed workups? Volume alone would miss a low-volume channel with exceptional conversion; rate alone would miss a high-volume channel with moderate conversion. The dot-and-bar combination avoids the misleading implication of a standard dual-axis chart by using distinct mark types and explicit axis labels.
- **Source query:** Query 2.2 (`04_dashboard_queries.sql` — Funnel by referral source)

### 6.5 Filters and Slicers

Global filter panel applies. Additional page-level slicers:

- **Stage selector** (multi-select, pre-filters the funnel to show conversion from a chosen starting stage — useful for deep-dive on mid-pipeline bottlenecks)
- **Referral Source** (multi-select, filters Visual 2-C)

### 6.6 Business Questions Answered

1. How many cases are at each workup stage right now, and what is the stage-to-stage conversion rate?
2. At which stage does the firm lose the most cases relative to intake?
3. Which case types have the lowest workup completion rates and represent the largest quality risk?
4. Which referral channels bring in cases that actually complete the workup process?
5. Is the firm meeting its SLA targets for average time in each stage?

---

## 7. Page 3 — Case Manager Productivity

### 7.1 Purpose

Benchmark individual case manager performance on caseload, workup completion, activity volume, and SLA compliance. Surface capacity imbalances and identify managers who may need support or whose practices should be replicated.

### 7.2 Target Audience

Director of Operations, team leads, HR. This page is internally sensitive — access should be restricted to management roles. Consumption frequency: weekly team review; monthly performance cycle.

### 7.3 KPI Metric Tiles

| Tile | Metric Name | Definition | Format | Source Query |
|---|---|---|---|---|
| T1 | Total Case Managers | Count of active case managers | Integer (18) | Query 3.1 |
| T2 | Avg Caseload per Manager | Open cases / 18 managers | Integer | Query 3.1 |
| T3 | Firm-Wide Completion Rate | Firm total, matching Page 1 T3 | Percent (60.8%) | Query 1.1 |
| T4 | Managers Above Capacity | Count of managers where open backlog > `monthly_capacity` | Integer | KPI Query 6 |

### 7.4 Charts and Visuals

#### Visual 3-A: Case Manager Scorecard Table (Matrix / Table Visual)

- **Visual type:** Sortable table with conditional formatting (heat-encoded cells)
- **Columns:**

| Column | Definition | Format | Conditional Format |
|---|---|---|---|
| Manager Name | `manager_name` | Text | — |
| Team | `team` | Text | — |
| Caseload | `COUNT(case_id)` | Integer | — |
| Open Cases | Open caseload | Integer | Orange if > `monthly_capacity` |
| Completion % | `workup_completed / caseload` | Percent | Green-to-red scale (green = 100%) |
| Avg Touchpoints | `AVG(communication_count)` | Decimal (1 place) | — |
| Avg Days in Stage | `AVG(days_in_stage)` | Days (1 place) | Red if > stage SLA target |
| Backlog Ratio | `open_backlog / monthly_capacity` | Decimal (2 places) | Red if > 1.0 |

- **Sorting:** Default sort by Completion % descending
- **Row-level drill:** Clicking a manager name navigates to a filtered view of that manager's case list (detail table at page bottom)
- **Title:** "Case Manager Scorecard — Completion Rate and Capacity Utilization (18 Managers)"
- **Why a table here:** When the audience must compare 18 individuals across five dimensions simultaneously, a table is the right primary encoding. Charts (bar charts per metric) would require 18 × 5 = 90 marks; a table provides scannable rows. Conditional formatting within the table cells adds visual pre-attentive encoding without replacing the numeric precision that a management audience requires for performance reviews.
- **Source query:** Query 3.1 (`04_dashboard_queries.sql` — Manager scorecard); KPI Query 6 (`03_kpi_queries.sql` — Backlog by case manager)

#### Visual 3-B: Team Activity Trend by Month (Line Chart)

- **Visual type:** Multi-series line chart — one line per team, showing logged hours per month
- **X-axis:** Month (calendar timeline)
- **Y-axis:** Logged hours, zero-baselined
- **Color:** One color per team, from the categorical palette (C1 through C4 for up to four teams)
- **Annotation:** Reference band marking the firm's expected monthly hours target (if defined in the data model); otherwise, a note explains the absence
- **Title:** "Team Activity Volume — Monthly Logged Hours by Team"
- **Why line chart for this:** Activity volume is a time-series quantity observed at monthly intervals. Lines correctly encode continuity and trend. Multiple series allow team-to-team comparison over the same time axis. A bar chart would be acceptable but becomes cluttered at 24 months × N teams; lines are cleaner. Zero-baseline on the Y-axis is maintained.
- **Source query:** Query 3.2 (`04_dashboard_queries.sql` — Activity productivity trend by month per team)

#### Visual 3-C: Backlog vs. Capacity Scatter Plot

- **Visual type:** Scatter plot — one dot per case manager
- **X-axis:** `monthly_capacity` (stated capacity)
- **Y-axis:** `open_backlog` (current open cases)
- **Reference line:** Y = X diagonal, labeled "At Capacity." Points above the diagonal are over-capacity; points below are under-capacity.
- **Color:** C6 Vermillion for over-capacity managers; C3 Bluish Green for at-or-under-capacity
- **Label:** Manager name displayed as a data label next to each dot (or in tooltip if the page is crowded)
- **Title:** "Backlog vs. Monthly Capacity — Managers Above the Diagonal Are Over-Extended"
- **Why scatter plot:** With 18 individuals and two continuous variables (capacity, backlog), a scatter plot on a common axis is the most information-dense and accurate choice. A bar chart comparing backlog to capacity would require side-by-side bars for each manager, producing 36 bars — less readable. The diagonal reference line eliminates the need for a secondary calculated column and makes the comparison purely visual.
- **Source query:** KPI Query 6 (`03_kpi_queries.sql` — Backlog by case manager)

#### Visual 3-D: Individual Case Worklist (Detail Table — filtered by manager selection)

- **Visual type:** Sortable data table
- **Columns:** Case ID, Case Type, Client Name, Current Stage, Days in Stage, SLA Status (Within / Breached), Last Activity Date, Missing Documents
- **Default filter:** Reflects the row selected in Visual 3-A; shows all managers' open cases when no row is selected
- **Sort:** Default by Days in Stage descending (oldest-to-newest)
- **Source query:** KPI Query 8 (`03_kpi_queries.sql` — Inactive cases over 30 days) joined to the manager scorecard query

### 7.5 Filters and Slicers

Global filter panel applies. Additional page-level slicers:

- **Team** (single-select dropdown, filters all visuals on the page to the selected team)
- **Capacity Status** (toggle: All / Over Capacity / Under Capacity — filters Visual 3-A and 3-C)

### 7.6 Business Questions Answered

1. Which case managers have the highest and lowest workup completion rates, and is the gap explained by caseload size?
2. Which managers are carrying open backlogs that exceed their stated monthly capacity?
3. Is team activity volume (logged hours) trending up or down, and are any teams significantly diverging from peers?
4. Which specific open cases on a given manager's docket are at risk of SLA breach?
5. Are average days in stage consistent across managers, or are some managers' cases moving unusually slowly?

---

## 8. Page 4 — Case Quality Analytics

### 8.1 Purpose

Assess the quality of case preparation by examining records receipt rates, missing document volumes, communication adequacy, and the relationship between preparation quality and settlement outcomes. Guides prioritization of remediation efforts.

### 8.2 Target Audience

Senior attorneys, Director of Litigation, quality assurance team. Consumption frequency: bi-weekly quality review; monthly litigation strategy meeting.

### 8.3 KPI Metric Tiles

| Tile | Metric Name | Definition | Format | Source Query |
|---|---|---|---|---|
| T1 | Avg Missing Documents per Open Case | `AVG(missing_documents)` for open cases | Decimal (2 places) | Query 4.1 |
| T2 | Medical Records Received Rate | `AVG(medical_records_received)` | Percent | Query 4.1 |
| T3 | High-Quality Cases | Cases where records received = 1, missing docs = 0, communications ≥ 5 | Percent of total | Query 4.1 |
| T4 | Avg Settlement — High Quality vs. Other | Difference in average settlement amount between high-quality and other settled cases | Dollar delta | Query 4.2 |

### 8.4 Charts and Visuals

#### Visual 4-A: Case Quality Component Matrix by Case Type (Heatmap)

- **Visual type:** Matrix heatmap — rows = case type, columns = quality dimension, cell value = percentage or score
- **Quality dimensions (columns):**
  1. Medical Records Received (%)
  2. Avg Missing Documents (inverted: 0 docs = best)
  3. Avg Communication Count
  4. High-Quality Cases (composite %)
- **Color scale:** White (worst) to Bluish Green C3 (best) for columns 1, 3, 4. White (best) to Vermillion C6 (worst) for column 2 (missing docs), because higher values are adverse.
- **Cell labels:** The numeric value is displayed in every cell. Font color switches to white when the background is dark (to maintain contrast ≥ 4.5:1).
- **Title:** "Case Quality by Type — Where Preparation Gaps Concentrate"
- **Why a heatmap:** With 12 case types × 4 quality dimensions = 48 data cells, a heatmap enables the simultaneous pre-attentive detection of clusters (e.g., "Mass Tort rows are uniformly pale — meaning poor quality across all dimensions") that individual bar charts would require the viewer to mentally synthesize. The explicit cell labels preserve numeric precision, so the heatmap is not a substitute for the numbers but an overlay that adds pattern detection.
- **Source query:** Query 4.1 (`04_dashboard_queries.sql` — Case quality score components by type)

#### Visual 4-B: Settlement Amount vs. Communication Count (Scatter Plot)

- **Visual type:** Scatter plot — one dot per settled case
- **X-axis:** `communication_count` (integer, zero-baselined)
- **Y-axis:** `settlement_amount` (dollars, zero-baselined)
- **Color:** `case_type` using categorical palette (C1 through C8)
- **Shape:** Filled circles; dot size is uniform (not sized by a third variable — that would add a hard-to-read area encoding)
- **Trend line:** A single OLS regression line across all points, with a 95% confidence band (shaded C2 Sky Blue at 20% opacity). The trend line is labeled with its slope coefficient and a note: "Slope does not imply causation — higher-value cases may attract more communication naturally."
- **Title:** "Settlement Value vs. Touchpoint Frequency — Settled Cases Only (n = ~326)"
- **Why scatter plot with trend line:** This chart answers a correlation question between two continuous variables. A scatter plot is the canonical and honest encoding for this question. Bar charts would require binning at least one variable, losing precision. The trend line with confidence band communicates the direction and uncertainty of the relationship. The caution note is mandatory — without it, a reader may incorrectly infer that adding phone calls increases settlement value.
- **Source query:** Query 4.2 (`04_dashboard_queries.sql` — Settlement value vs. case quality)

#### Visual 4-C: Document Completeness Rate by Document Type (Horizontal Bar Chart)

- **Visual type:** Horizontal bar chart, sorted ascending by completeness rate (lowest completeness at top — worst-first triage order)
- **X-axis:** Completeness rate (%), zero to 100%, zero-baselined
- **Y-axis:** Document type
- **Color:** Diverging — bars below 80% fill Vermillion (C6); bars at or above 80% fill Bluish Green (C3). A vertical reference line at 80% is labeled "Completeness Threshold"
- **Title:** "Document Completeness by Type — Lowest Rates at Top for Triage"
- **Why worst-first sort:** Operations teams scanning this chart need to prioritize remediation. Placing the most problematic categories at the top — where the eye lands first — aligns the chart's visual emphasis with the reader's action priority.
- **Source query:** DQ Query 2b (`05_data_quality_queries.sql` — Document completeness rate by type)

### 8.5 Filters and Slicers

Global filter panel applies. Additional page-level slicers:

- **High Quality Only toggle** (Yes / No / All) — filters all visuals to the high-quality case subset for drilling
- **Medical Records Received** (Yes / No toggle)

### 8.6 Business Questions Answered

1. Which case types have the worst preparation quality, as measured by missing documents and records receipt rates?
2. Is there a measurable relationship between preparation quality and settlement value?
3. Which document types are most frequently incomplete, and where should document remediation efforts focus?
4. What share of the portfolio meets the firm's definition of a "high-quality" workup?

---

## 9. Page 5 — Forecasting Dashboard

### 9.1 Purpose

Present the six-month forward forecast for monthly workup **demand** — new matters entering the pipeline (cases opened per month) — contextualize it against 24 months of historical actuals, and display the capacity gap between incoming demand and workup throughput. Supports headcount planning and pipeline management decisions.

**Methodological note (display as an info callout on the page):** The forecast target was deliberately chosen as monthly case-opening volume rather than monthly workup-completion volume. Completion counts are right-censored: matters opened recently have not yet had time to finish their workup, so a back-test against completion volume would understate model error on the most recent observations (review finding H2). Case-opening volume is an uncensored leading indicator of future workup demand and is the operationally correct input for capacity planning.

### 9.2 Target Audience

Managing partners, Director of Operations, finance. Consumption frequency: monthly, at the beginning of the forecast period.

### 9.3 KPI Metric Tiles

| Tile | Metric Name | Definition | Format | Source Query |
|---|---|---|---|---|
| T1 | Forecast Demand (Next 6 Months) | Sum of Jul–Dec 2025 point forecasts for new matters opened | Integer (869) | Forecast CSV |
| T2 | Forecast Model MAPE | Back-test mean absolute percentage error, 24-month history | Percent (12.5%) | `model_metrics.csv` |
| T3 | Forecast Model MAE | Back-test mean absolute error in matters/month | Decimal (15.8) | `model_metrics.csv` |
| T4 | Avg Monthly Intake (L12M) | Average new clients per month, last 12 months | Integer | KPI Query 9 |
| T5 | Monthly Capacity Gap | Avg monthly intake (T4) minus avg monthly completions | Integer, red if positive | Query 5.2 |

**Caveat tile below KPI row:** "Forecast target: new matters opened per month (demand), not completion volume. Completion counts are right-censored and are not used as the forecast target. MAPE 12.5%, MAE 15.8 matters/month on 24-month back-test. Confidence band widens with forecast horizon. Forecast updated monthly by `python/03_forecasting.py`."

### 9.4 Charts and Visuals

#### Visual 5-A: Historical Actuals + 6-Month Forecast (Line Chart with Confidence Band)

- **Visual type:** Line chart with a shaded confidence interval
- **X-axis:** Month (Jul 2023 – Dec 2025 — 24 historical months + 6 forecast months)
- **Y-axis:** New matters opened per month (workup demand), zero-baselined
- **Series 1 (Historical):** Solid line, C5 Blue, labeled "Actuals — New Matters Opened"
- **Series 2 (Forecast):** Dashed line, C5 Blue (same hue, dashed to signal uncertainty), labeled "Forecast"
- **Confidence band:** Shaded region around the forecast line using C2 Sky Blue at 20% opacity; band is anchored on back-test error (MAPE 12.5%, MAE 15.8/month) and widens with forecast horizon to reflect compounding uncertainty. Band is labeled "Uncertainty Range (widens with horizon)."
- **Vertical divider:** A thin grey dashed vertical line at the actuals/forecast boundary (Jul 2025), labeled "Forecast Start"
- **Point annotations on forecast months:** Jul 162, Aug 157, Sep 147, Oct 154, Nov 122, Dec 127 — displayed as data labels on the dashed forecast line
- **Title:** "Monthly Workup Demand — 24-Month History and 6-Month Forecast (MAPE 12.5%, MAE 15.8/month)"
- **Why this encoding:** A line chart is the standard and correct encoding for a continuous time series. Connecting actuals to forecast with a dashed extension of the same line clearly communicates projection while the visual distinction (solid vs. dashed) signals the shift from observed to modeled. The confidence band quantifies uncertainty without hiding it — a crucial obligation when presenting forecasts to decision-makers. Omitting the band would imply false precision. The band widening with horizon is also required: a constant-width band would falsely suggest the model is equally certain about December as it is about July.
- **Source queries:** Query 5.1 (`04_dashboard_queries.sql` — Monthly cases opened); `python/outputs/forecast_workup_volume.csv` (model output, loaded as a static table; file now reflects demand series)

#### Visual 5-B: Intake vs. Completions — Capacity Gap (Area / Bar Chart)

- **Visual type:** Clustered bar chart — two bars per month (Intake in C1 Amber, Completions in C3 Bluish Green) with a line overlay showing the gap
- **X-axis:** Month
- **Y-axis:** Count, zero-baselined
- **Capacity Gap line:** A calculated series `intake - completions` plotted as a secondary line on the same count axis (same units, same scale — no dual-axis concern). Line color: C6 Vermillion. When the gap is positive (intake > completions), the line is above zero; when negative, below.
- **Zero reference line on gap line:** Horizontal line at y = 0, labeled "Intake = Completions"
- **Title:** "Monthly Intake vs. Completions — Capacity Gap Signals Backlog Growth Risk"
- **Why clustered bar + line:** The two bars per month show absolute volumes; the gap line shows the derived quantity that matters operationally. Using a line for the gap (rather than a third bar) avoids over-cluttering the chart. Because all three series are on the same count axis with the same units, no dual-axis distortion is introduced.
- **Source query:** Query 5.2 (`04_dashboard_queries.sql` — Intake vs. completion capacity gap by month)

#### Visual 5-C: Feature Importance — Predictive Workup Completion Model (Horizontal Bar Chart)

- **Visual type:** Horizontal bar chart, sorted descending by importance score
- **X-axis:** Relative importance (normalized 0–1 scale from the logistic regression model), zero-baselined
- **Y-axis:** Feature name (missing_documents, medical_records_received, communication_count, attorney_experience_years, and any remaining model features). Note: `days_in_stage` is explicitly excluded from this model — it was found to leak the target variable (a case far into a stage already encodes information about whether workup will complete) and was removed during the methodology review.
- **Color:** Single hue (C5 Blue) — all bars represent model features ranked by contribution; no color differentiation needed
- **Title:** "Top Predictors of Workup Completion — Logistic Regression Model"
- **Model context annotation:** "Logistic Regression | Accuracy 68.7% | Precision 70.1% | Recall 84.4% | ROC-AUC 0.696 | 5-Fold CV AUC 0.700 ± 0.020 | Test set n = 686 | 184 cases flagged at risk"
- **Caveat:** "Feature importance reflects the model's learned coefficients in a logistic regression; it does not imply causal order. `days_in_stage` was excluded as a feature because it encodes target leakage — cases very far into a stage correlate with outcome by construction, not by predictive signal. Use feature rankings to understand which case attributes are most predictive, not to prescribe specific interventions without further analysis."
- **Source:** `python/outputs/feature_importance.png` (static image for visual reference) and `python/outputs/model_metrics.csv` (for KPI tiles)

#### Visual 5-D: At-Risk Case List (Detail Table)

- **Visual type:** Sortable data table
- **Filter:** Shows only the 184 cases flagged at risk by the predictive model (`predictions.csv`, where `predicted_label = 0` i.e., predicted not to complete)
- **Columns:** Case ID, Case Type, Current Stage, Assigned Case Manager, Missing Documents, Medical Records Received (Yes/No), Communication Count, Predicted Completion Probability
- **Sort:** Default by Predicted Completion Probability ascending (lowest probability = highest risk = top of list)
- **Note:** `days_in_stage` is not included as a column in this model-driven table because it is not a model input (excluded due to target leakage). It remains available as an operational column on Page 7 (Bottleneck Dashboard) where it is used outside the model context.
- **Title:** "184 Cases Flagged At Risk — Prioritize for Immediate Review"
- **Source query:** `python/outputs/predictions.csv` joined to `cases` via `case_id`

### 9.5 Filters and Slicers

Global filter panel applies. Page-specific note: the Date Range slicer affects the historical actuals only; the forecast series is static from the model output CSV and updates monthly when the script is re-run.

### 9.6 Business Questions Answered

1. How many new matters should the firm expect to enter the pipeline each month over the next six months, and how should staffing and records-request capacity be planned accordingly?
2. How reliable is the demand forecast, and what is the expected error range in absolute matters per month?
3. Is the firm's workup throughput keeping pace with incoming demand, or is the backlog growing?
4. Which case attributes — excluding target-leaking features — most strongly predict whether a matter will complete the workup?
5. Which specific open cases are at the highest risk of failing to complete workup, based on the corrected model?

---

## 10. Page 6 — Data Quality Dashboard

### 10.1 Purpose

Provide a transparent audit of known data integrity issues in the case management dataset. Quantify the scope of each issue type, track remediation progress over time, and prevent these issues from silently corrupting the KPIs displayed on other pages.

### 10.2 Target Audience

Data analyst, IT/systems team, operations manager. Consumption frequency: daily (automated anomaly alert threshold); weekly quality review.

### 10.3 KPI Metric Tiles

Six issue-category tiles in a 2×3 grid.

| Tile | Issue | Definition | Count (Snapshot) | Severity |
|---|---|---|---|---|
| T1 | Duplicate Clients | Client rows sharing name + DOB | 40 | High — inflates intake KPIs |
| T2 | Negative Settlement Amounts | `settlement_amount < 0` in `cases` | 8 | High — corrupts revenue KPIs |
| T3 | Negative Days in Stage | `days_in_stage < 0` in `cases` | 10 | High — corrupts SLA metrics |
| T4 | Close Before Open | `date_closed < date_opened` | 6 | High — corrupts cycle time KPIs |
| T5 | Missing Client Emails | `email IS NULL` in `clients` | 76 (3.0%) | Medium — blocks communication |
| T6 | Missing Referral Source | `referral_source IS NULL` in `clients` | 50 | Medium — blocks channel analytics |

**Tile formatting:** Each tile displays the count, a severity badge (High / Medium / Low in Vermillion / Amber / Grey respectively), and a one-line description of the KPI impacted. Tiles with a count of zero display in Bluish Green to signal a clean state.

**Overall Data Quality Score tile:** A composite score tile displayed prominently at top center: `((total_rows - total_issues) / total_rows) × 100`. This single score should not be used as a substitute for investigating individual issue types, and a note to that effect appears beneath it.

### 10.4 Charts and Visuals

#### Visual 6-A: Data Issue Summary by Category (Horizontal Bar Chart)

- **Visual type:** Horizontal bar chart — one bar per issue type, sorted by issue count descending
- **X-axis:** Issue count, zero-baselined
- **Y-axis:** Issue category
- **Color:** C6 Vermillion for High severity issues; C1 Amber for Medium severity; C8 Grey for Low
- **Title:** "Data Quality Issues by Category — Duplicate Clients and Missing Fields Dominate"
- **Source queries:** DQ Query 6 (`05_data_quality_queries.sql` — Overall data quality scorecard); DQ Query 4 (completeness); DQ Query 3 (logical violations)

#### Visual 6-B: Issue Detail Tables (Tabbed or Stacked Tables)

Four detail tables, accessible via tabs (Sigma) or bookmarks (Power BI):

**Tab 1 — Duplicate Clients**
- Columns: Identity Key (name + DOB), Occurrences, Recommended Keep ID, All Duplicate IDs
- Source: DQ Query 1 (`05_data_quality_queries.sql`)

**Tab 2 — Logical Violations**
- Sub-table A: Negative settlement amounts — Case ID, Case Type, Settlement Amount
- Sub-table B: Negative days in stage — Case ID, Current Stage, Days in Stage
- Sub-table C: Close before open — Case ID, Date Opened, Date Closed
- Source: DQ Query 3a, 3b, 3d (`05_data_quality_queries.sql`)

**Tab 3 — Document Completeness**
- Columns: Document Type, Total, Received, Completeness %
- Source: DQ Query 2b (`05_data_quality_queries.sql`)

**Tab 4 — Referential Integrity**
- Columns: Check Name, Violation Count
- Expected: All rows show 0 violations if referential integrity is intact
- Source: DQ Query 5 (`05_data_quality_queries.sql`)

#### Visual 6-C: Data Quality Trend Over Time (Line Chart — requires historical snapshots)

- **Visual type:** Line chart with one series per issue category
- **X-axis:** Snapshot date (populated as the quality audit is run over time)
- **Y-axis:** Issue count, zero-baselined
- **Color:** C6 (Vermillion) for high-severity, C1 (Amber) for medium
- **Title:** "Data Quality Issue Counts Over Time — Remediation Progress"
- **Note:** This chart is functional only once multiple snapshot dates are loaded. On initial deployment with a single snapshot (2025-06-30), display a placeholder: "Trend data will populate as daily quality audits are stored. Target: all High-severity counts at zero within 30 days."

### 10.5 Filters and Slicers

Global filter panel is suppressed on this page (data quality issues should be evaluated across the full dataset, not within a filtered subset, to avoid hiding issues). A single page-level filter:

- **Severity** (High / Medium / Low / All) — filters the summary chart and detail tables
- **Issue Category** (dropdown) — filters to a single issue type

### 10.6 Business Questions Answered

1. What are the current data integrity issues in the case management system, and how many records are affected?
2. Which issues pose the greatest risk to KPI accuracy, and which KPIs are currently compromised?
3. Are data quality issues being remediated over time, or are they accumulating?
4. Which specific client records are duplicates and need to be merged?
5. Is referential integrity intact across the nine tables (no orphaned records)?

---

## 11. Page 7 — Operational Bottleneck Dashboard

### 11.1 Purpose

Identify where cases pile up in the pipeline, quantify stall risk by stage and case type, and surface the medical records request backlog as the firm's most operationally consequential bottleneck. Drives daily triage and escalation decisions.

### 11.2 Target Audience

Director of Operations, team leads, intake coordinators, records request team. Consumption frequency: daily (operational team); weekly (management review).

### 11.3 KPI Metric Tiles

| Tile | Metric Name | Definition | Format | Source Query |
|---|---|---|---|---|
| T1 | Cases Stalled 30+ Days | Open cases with `last_activity_date` > 30 days ago | Integer | Query 1.1 / Query 7.1 |
| T2 | Cases Stalled 60+ Days | Open cases inactive for 60+ days | Integer | KPI Query 8 |
| T3 | Cases Stalled 90+ Days | Open cases inactive for 90+ days (critical) | Integer, red if > 0 | KPI Query 8 |
| T4 | Stage with Most Stalled Cases | Stage name + stalled count | Text + Integer | Query 7.1 |
| T5 | Outstanding Medical Record Requests | Records with `received_date IS NULL` | Integer | Query 7.2 |

### 11.4 Charts and Visuals

#### Visual 7-A: Open Cases and Avg Days in Stage by Current Stage (Dual-Element Bar Chart)

- **Visual type:** Horizontal bar chart where bar length = open case count, and a dot overlay shows average days in stage. All on a single, shared count axis; a separate small callout box per bar shows the average days value to avoid a dual-axis construction.
- **X-axis:** Open case count, zero-baselined
- **Y-axis:** Current stage (8 stages, sorted by open case count descending)
- **Color:** Bars in C2 (Sky Blue) if avg_days_in_stage ≤ SLA target; C6 (Vermillion) if avg_days_in_stage > SLA target. The SLA targets are encoded in the chart as reference ticks on a secondary annotation row beneath the Y-axis labels (not a second value axis).
- **SLA target annotation method:** Rather than a dual-axis, a small text annotation beside each bar reads: "SLA: Xd | Avg: Yd" where Y > X in red text. This communicates the SLA comparison without implying a false visual equivalence between two differently-scaled axes.
- **Stalled count callout:** A third annotation per bar shows the `stalled_30d` count in Vermillion.
- **Title:** "Pipeline Bottlenecks — Stage Distribution of Open Cases and SLA Status"
- **Why avoid dual axis:** A true dual-axis chart (open cases on left, days on right) would visually imply a correlation between case count and days that may not exist, and would allow the chart designer to manipulate the relative scale of the two axes to exaggerate or minimize apparent relationships. Encoding both quantities on the same bars (via annotation) is more honest.
- **Source query:** Query 7.1 (`04_dashboard_queries.sql` — Open cases and avg age by stage)

#### Visual 7-B: Inactivity Bucket Distribution (Stacked Bar Chart)

- **Visual type:** Stacked bar chart — one bar per stage, stacked by inactivity bucket (Active ≤30d, 31–60d, 61–90d, 90+d)
- **X-axis:** Open case count, zero-baselined
- **Y-axis:** Current stage
- **Color (4 inactivity buckets):** Active ≤30d in C3 (Bluish Green); 31–60d in C1 (Amber); 61–90d in C6 (Vermillion); 90+d in deep red (C6 darkened or a reserved alert color). Direct labels on each stack segment show the count.
- **Title:** "Inactivity Distribution by Stage — How Long Cases Have Sat Without Action"
- **Why stacked bar:** The question is "what is the composition of inactivity severity at each stage?" A stacked bar encodes part-of-whole within each stage bar (which categories make up the open count) while preserving the total count as the overall bar length. A 100% normalized stacked bar would answer a different question (what proportion, regardless of stage size) and is not appropriate here because the absolute count matters operationally.
- **Source query:** KPI Query 8 (`03_kpi_queries.sql` — Inactive cases, bucketed by inactivity duration)

#### Visual 7-C: Medical Records Backlog — Outstanding Requests by Status (Horizontal Bar Chart)

- **Visual type:** Horizontal bar chart — one bar per records status category, bar length = outstanding record request count, secondary annotation = avg days outstanding
- **X-axis:** Record count, zero-baselined
- **Y-axis:** Request status (e.g., Requested, Pending, Overdue)
- **Color:** C1 Amber for Requested; C6 Vermillion for Overdue. Status labels in the Y-axis encode the meaning; color adds urgency differentiation.
- **Avg days outstanding annotation:** A text callout to the right of each bar shows the average days outstanding for that status, formatted as "Avg Xd outstanding"
- **Title:** "Medical Records Backlog — Outstanding Requests by Status and Age"
- **Source query:** Query 7.2 (`04_dashboard_queries.sql` — Records bottleneck, outstanding medical records aging)

#### Visual 7-D: Stalled Case Worklist (Detail Table — operational triage)

- **Visual type:** Sortable, filterable data table with row-level action context
- **Columns:** Case ID, Client Name, Case Type, Current Stage, Case Manager, Last Activity Date, Days Inactive, Inactivity Bucket, Missing Documents, Medical Records Received
- **Default filter:** Cases inactive for 30+ days (`days_inactive > 30`)
- **Default sort:** Days Inactive descending
- **Conditional row color:** Rows with 90+ days inactive have a light Vermillion row background. Rows with 61–90 days inactive have a light Amber background. Active rows (≤30d) are white.
- **Title:** "Open Cases Stalled 30+ Days — Sorted by Inactivity (Oldest First)"
- **Source query:** KPI Query 8 (`03_kpi_queries.sql` — Inactive cases worklist with `staleness_rank_in_cm`)

### 11.5 Filters and Slicers

Global filter panel applies. Additional page-level slicers:

- **Inactivity Threshold** (dropdown: 30d / 60d / 90d) — adjusts the stalled-case definition across all visuals on the page
- **Case Manager** (single-select) — filters the worklist and bottleneck charts to a specific manager's caseload
- **Stage** (multi-select) — filters to specific pipeline stages

A secondary date filter on `last_activity_date` is exposed on this page only, in addition to the global `intake_date` range filter.

### 11.6 Business Questions Answered

1. Which pipeline stages contain the most open cases, and which are exceeding their SLA targets?
2. How many open cases have been inactive for more than 30, 60, or 90 days, and where do they sit in the pipeline?
3. What is the size and age of the outstanding medical records request backlog?
4. Which specific cases require immediate action, and which case managers own them?
5. Is there a stage in the pipeline that consistently produces stalls — suggesting a systemic process failure rather than isolated case-level issues?

---

## 12. Screenshots Checklist

The following screenshots should be captured once the dashboards are published and populated with the 2025-06-30 snapshot data. Screenshots are saved to `/Users/rin/Legal-Case-Management-Intelligence/screenshots/` using the naming convention specified below. All screenshots should be captured at 1920×1080 resolution with all global filters reset to defaults (full date range, all case types, all managers).

### Page 1 — Executive Overview

- [ ] `01_executive_overview_full.png` — Full-page view with all six KPI tiles and all three visuals visible
- [ ] `01_executive_kpi_tiles.png` — Close-up of the six KPI tiles row (crop to the tile band)
- [ ] `01_case_mix_bar.png` — Visual 1-A (case mix horizontal bar chart)
- [ ] `01_pipeline_value_bar.png` — Visual 1-B (open pipeline expected value)
- [ ] `01_intake_trend_line.png` — Visual 1-C (monthly intake trend with rolling average)

### Page 2 — Client Workup Funnel

- [ ] `02_workup_funnel_full.png` — Full-page view
- [ ] `02_funnel_chart.png` — Visual 2-A (funnel chart with stage conversion labels)
- [ ] `02_completion_by_type.png` — Visual 2-B (completion rate by case type with benchmark line)
- [ ] `02_referral_source_chart.png` — Visual 2-C (referral source conversion chart)

### Page 3 — Case Manager Productivity

- [ ] `03_productivity_full.png` — Full-page view
- [ ] `03_scorecard_table.png` — Visual 3-A (manager scorecard table with conditional formatting visible)
- [ ] `03_activity_trend.png` — Visual 3-B (team activity trend line chart)
- [ ] `03_backlog_scatter.png` — Visual 3-C (backlog vs. capacity scatter plot with diagonal)

### Page 4 — Case Quality Analytics

- [ ] `04_quality_full.png` — Full-page view
- [ ] `04_quality_heatmap.png` — Visual 4-A (quality component heatmap)
- [ ] `04_settlement_scatter.png` — Visual 4-B (settlement value vs. communication count scatter)
- [ ] `04_document_completeness.png` — Visual 4-C (document completeness horizontal bar)

### Page 5 — Forecasting Dashboard

- [ ] `05_forecast_full.png` — Full-page view
- [ ] `05_forecast_line.png` — Visual 5-A (historical actuals + forecast with confidence band)
- [ ] `05_capacity_gap.png` — Visual 5-B (intake vs. completions clustered bar + gap line)
- [ ] `05_feature_importance.png` — Visual 5-C (feature importance horizontal bar)
- [ ] `05_at_risk_table.png` — Visual 5-D (at-risk case list — blurred/anonymized for portfolio use)

### Page 6 — Data Quality Dashboard

- [ ] `06_quality_dashboard_full.png` — Full-page view with all six issue tiles visible
- [ ] `06_issue_summary_bar.png` — Visual 6-A (issue summary bar chart)
- [ ] `06_duplicate_clients_table.png` — Visual 6-B Tab 1 (duplicate client detail table)
- [ ] `06_logical_violations_table.png` — Visual 6-B Tab 2 (logical violation detail tables)

### Page 7 — Operational Bottleneck Dashboard

- [ ] `07_bottleneck_full.png` — Full-page view
- [ ] `07_stage_pipeline_bar.png` — Visual 7-A (open cases and SLA status by stage)
- [ ] `07_inactivity_stacked_bar.png` — Visual 7-B (inactivity bucket distribution by stage)
- [ ] `07_records_backlog_bar.png` — Visual 7-C (medical records backlog)
- [ ] `07_stalled_worklist.png` — Visual 7-D (stalled case worklist — blurred for portfolio)

### Navigation and Style

- [ ] `00_dashboard_nav_overview.png` — Screenshot of the page navigation strip showing all seven page tabs
- [ ] `00_global_filter_panel.png` — Global filter/slicer panel in its expanded state

---

*Document end. Total pages specified: 7. Total visuals specified: 23 (excluding KPI tiles). All visuals reference queries in `sql/04_dashboard_queries.sql` or `sql/03_kpi_queries.sql` or `sql/05_data_quality_queries.sql` as noted. Python model outputs referenced as static CSV tables: `python/outputs/forecast_workup_volume.csv`, `python/outputs/predictions.csv`, `python/outputs/model_metrics.csv`.*

*Source: Case Management System | Snapshot: 2025-06-30 | n = 2,743 cases | 2,500 clients | 12 attorneys | 18 case managers*
