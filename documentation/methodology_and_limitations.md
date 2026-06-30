# Methodology & Limitations

This project was put through an **adversarial methodology review** before the
numbers were trusted. That review is part of the deliverable on purpose: a
strong analyst characterizes the weaknesses of their own work. This document
records what was checked, what was fixed, and what remains a known limitation to
be disclosed in any walkthrough.

---

## 1. Methodology review findings & resolutions

The predictive-model and forecasting code (`python/03_forecasting.py`,
`python/04_predictive_model.py`) and the data generator were audited for data
leakage, train/test hygiene, and forecast validity. Findings and the action
taken:

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| C1 | **Critical** | `days_in_stage` leaked the target — in the generator it is derived from the funnel stage index, which is drawn *conditional on* `workup_completed`. | **Removed `days_in_stage` from the feature set** and re-reported. Test ROC-AUC fell ~0.715 → **0.696**; the lower number is the honest one. |
| H1 | High | **Circularity (disclosure):** the synthetic generator builds `workup_completed` from the same drivers (communication, missing docs, records, manager effectiveness) the model then recovers. Not leakage, but it means performance shows the pipeline is correct, not that a real-world effect size exists. | Disclosed (see Limitations §2). Reported metrics are an **upper bound** on what real operational data would yield. |
| H2 | High | The completion-volume forecast indexed completed workups by `date_opened` (attributing a future event to the open date) and the recent months were right-censored, corrupting the back-test. | **Reframed the forecast target** to *monthly workup demand = new matters entering the pipeline* (cases opened/month) — an exact, uncensored, decision-relevant series. Back-test MAPE **12.5%**. |
| M1 | Medium | Median imputation was fit on the full dataset before the split (mild train/test contamination). | **Moved imputation into the sklearn `Pipeline`** (`SimpleImputer` inside the `ColumnTransformer`), so it is fit on training folds only. |
| M2 | Medium | Metrics came from a single train/test split with no uncertainty. | **Added 5-fold stratified cross-validation**; headline AUC is now reported as **mean ± std** (0.700 ± 0.020). |
| M3 | Medium | The forecast band used in-sample residual std and was flat across horizon. | **Band now anchored on the back-test error and widens with horizon** (√h scaling). |

**Verified correct by the review (not just unchecked):** the leak-column
exclusion list is genuinely enforced; `StandardScaler`/`OneHotEncoder` are fit on
train folds only; the train/test split is stratified; the de-duplication
re-points case foreign keys to surviving client IDs before dropping duplicates
(no orphaned rows, no double counting).

---

## 2. Known limitations (disclose these)

1. **Synthetic data.** All data is generated (`python/generate_data.py`). It is
   internally consistent and realistic but is **not** real firm data; effect
   sizes are illustrative.
2. **Generator circularity.** Because the target is generated from known drivers,
   the classifier partly recovers the data-generating process. Treat the ROC-AUC
   (~0.70) as a *ceiling*, not a forecast of real-world lift. The value of the
   model here is the **pipeline, leakage discipline, and triage workflow**, not
   the specific AUC.
3. **`team` is a near-noise feature.** Managers are assigned to teams
   independently of their latent effectiveness, so `team` should carry almost no
   signal. If it ranks highly in importance, that is noise-fitting, not a real
   effect — a caveat when reading `feature_importance.png`.
4. **De-duplication may over-merge.** Duplicates are detected on
   `(first_name, last_name, date_of_birth)`. Two genuinely distinct clients who
   share a name and DOB would be incorrectly merged. Impact is small at this
   scale but the rule should be reviewed before production use.
5. **One-time intake surge.** The history contains a marketing-driven intake
   surge. A pure trend + seasonal model cannot fully capture a one-off event, so
   forecast error is concentrated around regime changes; the back-test MAPE
   (12.5%) reflects an average, not a guarantee at turning points.
6. **Single snapshot.** All "as-of" metrics use a fixed snapshot date
   (2025-06-30). There is no slowly-changing-dimension history, so trends in
   stage timing over time cannot be reconstructed from this extract.
7. **Auto-repair of dirty values.** The cleaning step repairs injected sign
   errors with `abs()`. In production, anomalous values should be **quarantined
   for review** rather than auto-corrected, since the true cause may not be a
   sign error.

---

## 3. What I'd do before production

- Re-fit on **real, point-in-time** operational data and re-validate the leakage
  boundary against the real event timeline.
- Replace the snapshot extract with a **slowly-changing-dimension** model to
  capture stage-timing history.
- Add **probability calibration** (e.g., isotonic) and choose the risk threshold
  from a cost matrix (cost of a missed at-risk matter vs. a false alarm), rather
  than a default 0.5.
- Monitor for **drift** (intake mix, channel mix, manager roster) and schedule
  periodic re-training.
- Promote the forecast to a proper time-series model (e.g., ETS/Prophet/SARIMA)
  with event regressors for marketing surges, and report calibrated intervals.

---

*This document is intentionally candid. In an interview, the leakage catch (C1)
and the forecast reframe (H2) are the two strongest talking points — they show
the analysis was stress-tested, not just produced.*
