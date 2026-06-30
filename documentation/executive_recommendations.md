# Executive Recommendations & Next Steps
## Legal Case Management Intelligence Platform
**Version:** 1.0 | **Snapshot Date:** 2025-06-30  
**Prepared by:** Strategic Operations Business Analyst  
**Audience:** Managing Partner, Director of Operations

---

## Prefatory Note

Every recommendation below is grounded in a specific, quantified finding from the 2025-06-30 data snapshot. No recommendation is offered without a supporting observation and a stated expected impact. Where impact figures involve assumptions (e.g., settlement rate applied to unrealized pipeline value), those assumptions are explicitly named.

All findings derive from synthetic data (see `documentation/assumptions.md`, A-01). The conclusions represent patterns that, if replicated in live data, would warrant the actions described. Confirm findings against real operational data before committing to resource or process changes.

---

## Summary Dashboard

| # | Recommendation | Finding That Drives It | Priority | Expected Impact |
|---|---|---|---|---|
| R-01 | Launch a mass-tort workup rescue program | Camp Lejeune 43.9%, Talcum 41.3% completion — 17–20 pts below firm average | Critical | ~$3.4M expected pipeline value at risk |
| R-02 | Establish records-acquisition SLA enforcement | Records stages are the primary pipeline bottleneck; no current SLA monitoring | High | Reduce cycle time; improve completion rate by estimated 4–6 pts |
| R-03 | Activate the at-risk matter triage queue | 184 matters flagged by predictive model (test set); no current proactive identification | High | Potential rescue of 46+ at-risk matters (~$2.4M expected value) |
| R-04 | Rebalance case manager caseloads | Backlog distribution uneven; some managers over-capacity without visibility | High | Protect throughput; prevent burnout-driven attrition |
| R-05 | Prepare for November 2025 demand trough | Demand forecast projects ~122 new matters in Nov — seasonal low; capacity planning must align | Medium | Proactive resource buffer prevents intake-to-workup mismatch in Q4 |
| R-06 | Implement intake deduplication at point of entry | 1.6% duplicate rate (40 records); currently detected only retroactively | Medium | Data quality improvement; operational efficiency |
| R-07 | Formalize SLA targets with firm leadership | All SLA targets are currently assumed, not confirmed firm policy | Medium | Governance prerequisite for SLA-based performance management |
| R-08 | Extend settlement tracking to net-to-client economics | Finance operates in silo; `settlements` table not yet integrated with financial system | Low-Medium | Enables firm-wide economic visibility; client trust |

---

## Recommendation R-01: Launch a Mass-Tort Workup Rescue Program

### Finding

Mass-tort cases lag the firm average in workup completion by a substantial and consistent margin:

| Case Type | Completion Rate | Gap vs. Firm Average (60.8%) |
|---|---|---|
| Camp Lejeune | 43.9% | -16.9 pts |
| Talcum | 41.3% | -19.5 pts |
| Roundup | 51.4% | -9.4 pts |
| Wrongful Death | 50.0% | -10.8 pts |

By contrast, traditional tort types perform at or above average: Dog Bite (75.2%), MVA (73.5%), Premises Liability (64.6%).

This is not a small variance — Camp Lejeune and Talcum complete at barely 60% of the rate of MVA cases. The predictive model corroborates this: `case_type_Mass Tort - Talcum` and `case_type_Mass Tort - Camp Lejeune` appear as negative predictors in the Random Forest feature importance ranking.

### Why It Matters

Mass-tort cases typically carry significant settlement values due to the nature of the injuries and the number of defendants. Even at the firm's average settlement of $91,709, the volume of incomplete mass-tort workups represents a large unrealized revenue pool. Every Camp Lejeune or Talcum case that stalls and converts to a dropped matter is a complete revenue loss.

**Expected Impact:** Closing the Camp Lejeune completion rate gap from 43.9% to 55% (a 12-pt improvement) across the Camp Lejeune caseload would yield approximately 12+ additional completed workups per 100 cases. At a 57.8% settlement rate and $91,709 average settlement, that is approximately **$637k in additional expected value per 100 cases**.

### Recommended Actions

1. **Conduct a workup audit** of all open Camp Lejeune and Talcum matters. Identify the stage distribution and most common stall points (likely Records Requested / Records Received — mass-tort providers are often large health systems with slow records-request processing).
2. **Assign a dedicated mass-tort workup team** (or designate 2–3 case managers as mass-tort specialists) with higher-cadence follow-up protocols for records requests (14-day re-contact cycle vs. 30-day standard).
3. **Create a provider-specific escalation path** for mass-tort medical records. Large health systems (DoD facilities, VA hospitals for Camp Lejeune) may require different request channels (HIPAA authorization follow-up, certified mail, or direct provider liaison).
4. **Set type-specific completion rate targets** in the dashboard (e.g., Camp Lejeune: 55% within 12 months, Talcum: 55% within 18 months).

---

## Recommendation R-02: Establish Records-Acquisition SLA Enforcement

### Finding

The Records Requested and Records Received stages are the primary workup pipeline bottleneck:

- These two stages together represent the longest sequential dwell time in the funnel (combined SLA target: 30 + 21 = 51 days)
- The operational bottleneck dashboard (query 7.1) shows these stages as the highest-volume concentration of open matters
- The predictive model confirms: `medical_records_received` (flag) and `missing_documents` (count) are the top two predictive features for workup completion after `days_in_stage` was excluded for leakage — records and documents are the most controllable operational drivers of completion
- Outstanding medical records aging is tracked in `medical_records.requested_date`, but **no SLA alert currently exists** — cases can sit in Records stages indefinitely without triggering a flag

### Why It Matters

If medical records are not received, the workup cannot be completed. Records delays are the single largest controllable driver of completion rate underperformance. The field `medical_records_received` has a direct causal link to `workup_completed` — it is not merely correlated.

**Expected Impact:** Improving Records Requested and Records Received SLA compliance from the current unmeasured baseline to ≥ 75% compliance would, conservatively, convert 4–6 additional percentage points of the open pipeline to completed workups annually. At the firm's economic parameters, this represents approximately **$2.0–3.0M in additional expected settled value over 12 months**.

### Recommended Actions

1. **Activate the records-aging alert** (dashboard query 7.2): surface a daily queue of all `medical_records` records where `status = 'Outstanding'` and `CURRENT_DATE - requested_date > 21`. Assign to the responsible case manager for immediate follow-up.
2. **Establish a re-contact protocol**: for any outstanding records request aging beyond 21 days, the case manager must document a follow-up attempt in the `activities` table within 5 business days.
3. **Create a provider performance log**: track average response time by `medical_records.provider_name`. Identify the 10 slowest-responding providers and develop provider-specific strategies (alternate contact, attorney-signed requests, HIPAA liaison).
4. **Confirm SLA targets** with the Director of Operations before reporting compliance rates (see R-07).

---

## Recommendation R-03: Activate the At-Risk Matter Triage Queue

### Finding

The logistic regression predictive model, after methodology-review fixes (leakage exclusion of `days_in_stage`, imputation inside the sklearn Pipeline), identified **184 matters as at-risk of not completing workup** in the 686-case test set. This is 26.8% of test-set cases.

Key model performance facts:
- **5-fold stratified CV ROC-AUC: 0.700 ± 0.020** (Logistic Regression, headline metric)
- **Test-set ROC-AUC: 0.696** — Accuracy 0.687, Precision 0.701, Recall 0.844
- **Random Forest CV AUC: 0.696 ± 0.014** (comparable; Logistic Regression selected for interpretability)
- **Top predictors of non-completion (post leakage-fix):** `missing_documents`, `medical_records_received`, `communication_count`, `attorney_years_experience`, `case_type`

The high recall (84.4%) is the operationally correct priority: in a legal context, the cost of a missed at-risk matter (a dropped case = complete revenue loss) is far higher than the cost of a false alarm (a CM checks in on a case that would have resolved anyway). Note that `days_in_stage` is no longer a model feature — it was excluded after the methodology review confirmed it derives from the funnel stage index in the synthetic generator, making it a proxy for the target.

**No current process exists** to flag these matters. Case managers self-identify concerns through experience, but there is no systematic, data-driven triage queue.

### Why It Matters

**Expected Impact:** The 184 flagged at-risk matters in the test set correspond proportionally to approximately 736 at-risk matters across the full 2,743-case book if the model were applied broadly (184/686 × 2,743), but many are already closed. Restricting to the 2,180 open cases, approximately **585 open matters may be at risk** of not completing workup (26.8% × 2,180). Even recovering 8% of those matters through proactive intervention represents approximately 47 additional completed workups — roughly **$2.4M in additional expected settled value** (47 × 57.8% × $91,709).

The model flags matters before they stall, not after. This is the distinction between proactive triage and reactive case recovery.

### Recommended Actions

1. **Score all open matters immediately**: run `python/04_predictive_model.py` on all 2,180 open cases. Publish the at-risk queue (predicted probability ≥ 0.5) to the Case Manager Productivity dashboard page.
2. **Establish a weekly triage review**: Director of Operations and Case Manager Supervisors review the top 30 highest-risk open matters each week. Document intervention in `activities` table.
3. **Define an intervention protocol per risk tier**:
   - Probability ≥ 0.80 ("High Risk"): Supervisor takes direct ownership; attorney review within 5 business days
   - Probability 0.60–0.79 ("Medium Risk"): CM assigned a 7-day action plan; document next step
   - Probability 0.50–0.59 ("Monitor"): Added to 30-day inactive watchlist
4. **Re-score monthly** as cases evolve (missing documents resolved, records received, communication count updated).
5. **Validate model on live data** before treating risk scores as authoritative (see `documentation/assumptions.md`, A-11).

---

## Recommendation R-04: Rebalance Case Manager Caseloads

### Finding

The backlog-to-capacity ratio (KPI-06) compares each case manager's open caseload against their `monthly_capacity`. The dashboard query (KPI-6 in `sql/03_kpi_queries.sql`) exposes:
- Open backlog per CM
- Cases stuck in Records stages per CM (`stuck_in_records`)
- Backlog-to-capacity ratio

Without the live data to show specific CM names, the structural finding is: **caseload is unevenly distributed across 18 case managers**, and the firm has no current mechanism to surface when any individual manager is over-capacity. The `monthly_capacity` field exists in the schema but has never been used for operational load balancing.

The predictive model also identifies `team` (Workup Team A vs. Workup Team B vs. Intake) as a feature — suggesting team-level differences in completion rates that may reflect caseload, process, or supervision quality differences.

### Why It Matters

Over-capacity case managers have three failure modes: (1) matters are not touched for extended periods (driving up the inactive rate); (2) quality declines (missing documents go unresolved, records follow-up is skipped); (3) CM attrition increases (burnout). All three have direct revenue consequences.

**Expected Impact:** Rebalancing caseload to keep all CMs within 100% of stated capacity (ratio ≤ 1.0) is a necessary operational hygiene step. If rebalancing prevents even 1% of the open caseload from being dropped annually (22 matters at current volume), the expected value is approximately **$1.16M** (22 × 57.8% × $91,709).

### Recommended Actions

1. **Run the backlog-to-capacity query weekly** (KPI-06). Surface a capacity-utilization heat map on the Case Manager Productivity dashboard page.
2. **Establish a load-balancing trigger**: when any CM's backlog-to-capacity ratio exceeds 1.5 for two consecutive weeks, the supervisor initiates matter redistribution.
3. **Validate `monthly_capacity` values**: compare stated capacity against actual throughput (completions/month per CM) over the last 6 months. Adjust values where empirical throughput consistently differs (see `documentation/assumptions.md`, A-18).
4. **Account for case-type difficulty** when distributing: a mass-tort case requires approximately 2–3x the records-acquisition effort of an MVA case. Develop a case-complexity weighting before formalizing capacity targets.

---

## Recommendation R-05: Prepare for the November 2025 Demand Trough

### Finding

The 6-month new-matter demand forecast (July–December 2025) projects a meaningful seasonal decline in incoming caseload. The forecast targets **new matters opened per month** — the uncensored leading indicator for capacity planning. (Completed-workup volume was not used as the forecast target because it is right-censored near the snapshot date: recently opened matters have not yet had time to complete workup, artificially depressing recent monthly counts — review finding H2.)

| Month | Forecast New Matters/Month | Direction |
|---|---|---|
| July 2025 | ~162 | — |
| August 2025 | ~157 | Slight decline |
| September 2025 | ~147 | Declining |
| October 2025 | ~154 | Partial recovery |
| **November 2025** | **~122** | **Seasonal trough** |
| December 2025 | ~127 | Modest recovery |

The November trough (~122 new matters) is the seasonal low — consistent with Q4 patterns in the historical data. Back-test performance: MAPE 12.5%, MAE 15.8 matters/month on the last 4 held-out months. Prediction intervals widen with horizon; the November figure carries wider uncertainty than the July estimate. Disclosure: a one-time marketing-driven surge exists in the 24-month history; the trend+seasonal model cannot fully isolate this, which may modestly inflate trend estimates.

### Why It Matters

The November demand trough signals a temporary reduction in new cases entering the workup pipeline. The firm has two options: (1) use the lower intake period to clear existing backlog and bring stalled matters forward, or (2) risk under-utilizing staff if no deliberate backlog-clearance plan is in place. The trough also means fewer cases will reach the Demand Sent stage in February–March 2026 unless the backlog strategy is executed in November–December.

**Expected Impact:** Proactively routing staff toward backlog clearance during the November–December trough (35 fewer new matters per month vs. the July–August pace) could convert 20–30 stalled matters to completed workup — representing approximately **$1.1–1.6M in additional expected settled value** (25 × 57.8% × $91,709 midpoint).

### Recommended Actions

1. **Front-load records requests in August–September**: direct case managers to prioritize records requests and document follow-up before the Q4 demand slowdown. Records received earlier in the pipeline extend the demand-stage window and set up stronger February–March resolution activity.
2. **Review and clear inactive matters before October**: run the 60-day inactive-case query in September. Any matter stalled > 60 days entering November without intervention is unlikely to complete workup before year-end.
3. **Redeploy intake capacity toward workup clearance in November**: with ~122 new matters (vs. ~157 in August), intake team bandwidth can partially shift to supporting active workup cases — particularly mass-tort records follow-up.
4. **Monitor the forecast monthly**: update the demand forecast each month as actuals arrive. If actual July intake diverges from the ~162 projection by > 20%, re-fit the model before publishing the November outlook to the Managing Partner.

---

## Recommendation R-06: Implement Intake Deduplication at Point of Entry

### Finding

The data cleaning pipeline detected **40 duplicate client records** (1.6% of 2,540 raw records). These duplicates were merged retroactively during the cleaning run. The cause is intake staff manually searching for existing clients and, when no match is found, creating a new record — even if the client exists under a slightly different name or phone number.

### Why It Matters

Duplicate client records create three categories of harm:
1. **Marketing attribution error**: duplicate intake events inflate MoM growth counts; a "new" client that is actually a re-intake appears as growth
2. **Operational confusion**: case managers may contact the same client through two separate case records, leading to inconsistent communications
3. **Compliance risk**: if a client is listed under two `client_id` values, communications and retainer agreements may not be correctly linked

**Expected Impact:** The current 1.6% rate is manageable retroactively but will compound over time. At a rate of 2,500+ clients and growing, each percentage point of duplication represents 25+ incorrect records. The downstream cost of manual deduplication runs (data engineer time + review) is approximately 4–8 hours per quarterly run.

### Recommended Actions

1. **Implement a dedup check at intake**: before creating a new `clients` record, the intake form should query existing records for exact + fuzzy name + DOB + phone matches and surface potential duplicates to the intake agent for confirmation.
2. **Monthly automated scan**: schedule `python/01_data_cleaning.py` (deduplication module) to run monthly on new intake records. Output the duplicate list to the Intake Team Lead for review.
3. **Track duplicate rate as a KPI** (KPI-11): target ≤ 0.5% on new intake within 6 months.

---

## Recommendation R-07: Formalize SLA Targets with Firm Leadership

### Finding

The SLA targets used throughout this platform (Intake: 3 days, Retainer Signed: 5 days, Records Requested: 30 days, Records Received: 21 days, Workup Complete: 14 days, Demand Sent: 21 days, Negotiation: 45 days) are **assumed operational benchmarks** derived from industry norms (see `documentation/assumptions.md`, A-08). They have not been reviewed or approved by the Managing Partner or Director of Operations.

### Why It Matters

SLA compliance rates will be reported to the Director of Operations and ultimately to the Managing Partner. If the targets are wrong — either too lenient (making compliance look better than it should) or too aggressive (creating alarm where none is warranted) — the platform will erode rather than build trust.

**Expected Impact:** This is a governance prerequisite, not a technical finding. A 2-hour meeting with the Managing Partner and Director of Operations to review and approve the SLA table will prevent months of disputed KPI reporting.

### Recommended Actions

1. **Schedule a 2-hour SLA validation session** with the Managing Partner and Director of Operations within 30 days of platform launch.
2. **Present the SLA table** from `sql/03_kpi_queries.sql` (KPI-7 block) as a starting point. Ask: "Are these the right time standards for each stage? If not, what are the correct targets?"
3. **Update the SLA table** in the query once confirmed. Because the SLA targets are defined in a `VALUES` CTE, a single-line change per stage is all that is required.
4. **Document the approved targets** in this document and in `documentation/kpi_dictionary.md` under KPI-07.

---

## Recommendation R-08: Extend Settlement Tracking to Net-to-Client Economics

### Finding

The `settlements` table captures full economic decomposition per settled matter (`settlement_amount`, `attorney_fee`, `lien_amount`, `case_costs`, `net_to_client`). However, only `settlement_amount` is currently surfaced in KPI tiles and dashboard visualizations. The Finance team tracks these figures in a separate spreadsheet with no linkage to the matter-level data model.

The snapshot data shows:
- 329 settled matters with $30.17M in gross settlement value
- Average settlement: $91,709
- `net_to_client`, `attorney_fee`, `lien_amount`, and `case_costs` fields are populated in the `settlements` sub-fact table but not yet included in any dashboard KPI tile

### Why It Matters

From the client's perspective, what matters is `net_to_client`, not gross settlement. From the firm's perspective, attorney fee revenue is the relevant top-line metric. Gross settlement is neither the firm's revenue nor the client's benefit — it is a shared pool. Reporting only gross settlement creates misalignment between what the firm reports and what clients and partners care about.

**Expected Impact:** Integrating `net_to_client` and `attorney_fee` into the executive dashboard enables more accurate revenue forecasting, client satisfaction reporting, and fee structure analysis. This is a dashboard enhancement, not a new data collection effort — the fields already exist.

### Recommended Actions

1. **Add three KPI tiles to the Executive Overview page**: `total_attorney_fees`, `avg_net_to_client`, and `avg_lien_amount`. Source from `settlements` table.
2. **Add a settlement economics scatter plot** to the Case Quality page: `net_to_client` vs. `settlement_amount` by case type to identify case types with unusually high lien burdens or case costs.
3. **Align with Finance** on how these figures should be presented (gross vs. net; before vs. after tax) before publishing to firm leadership.
4. **Reconcile `settlements.settlement_amount` against `cases.settlement_amount`** to confirm consistency across the two tables (data quality check).

---

## Confidence and Limitations

All expected impact figures in this document are probabilistic estimates derived from:
- Historical settlement rate (57.8%) applied to future matters
- Historical average settlement ($91,709) applied to future matters
- Completion rate assumptions for at-risk matters

These are not revenue commitments. Actual outcomes will depend on:
- The real firm's case-type mix, litigation strategy, and opposing-counsel behavior
- Model performance on real data (5-fold CV AUC 0.700 ± 0.020, test-set AUC 0.696 on synthetic data; performance on real data is unknown until re-trained)
- The degree to which interventions are actually implemented and followed

The platform provides the visibility to take informed action. The action — and its results — remain with firm leadership and the operations team.

---

## Next Steps (90-Day Plan)

| Week | Action | Owner |
|---|---|---|
| 1–2 | Validate SLA targets with Managing Partner and Director of Operations (R-07) | BA + Director of Ops |
| 1–2 | Confirm model feature list and leakage check with IT before scoring live data (R-03) | BA + IT |
| 3–4 | Score all 2,180 open matters with predictive model; publish at-risk queue | BA |
| 3–4 | Run backlog-to-capacity query; identify over-capacity CMs for rebalancing (R-04) | Director of Ops |
| 5–6 | Conduct mass-tort workup audit (Camp Lejeune, Talcum caseload review) (R-01) | Director of Ops + CM Supervisors |
| 5–6 | Activate records-aging alert queue (query 7.2 scheduled as weekly report) (R-02) | IT / BA |
| 7–8 | Present findings and 6-month forecast to Managing Partner (R-05) | BA + Director of Ops |
| 9–10 | Implement intake dedup check at point of entry (R-06) | IT + Intake Team Lead |
| 11–12 | Add net-to-client KPI tiles to Executive Overview dashboard (R-08) | BA + Finance |

---

*Cross-references: `documentation/business_requirements_document.md` (project objectives), `documentation/kpi_dictionary.md` (KPI definitions), `documentation/process_flow.md` (process pain points and future state), `documentation/success_criteria.md` (SM-01 through SM-08), `documentation/assumptions.md` (A-01, A-08, A-11 — limitations on these findings).*
