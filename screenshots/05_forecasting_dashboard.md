# Screenshot Placeholder — Forecasting Dashboard

**File to capture:** `forecasting_dashboard.png`
**Audience:** Director of Operations, Finance

## What this screenshot should show
Workup-demand capacity planning: actuals plus the 6-month forecast. The forecast
target is **monthly workup demand — new matters entering the pipeline (cases
opened/month)** — not completed-workup volume, which is right-censored near the
snapshot and would corrupt the back-test (methodology review H2).

**Visuals:**
- **Line with forecast overlay + 80% interval**: monthly new-matter demand,
  actual (2023-07 → 2025-06) and forecast (Jul–Dec 2025 ≈ 162, 157, 147, 154, 122, 127).
  Use the generated chart [`../python/outputs/forecast_workup_volume.png`](../python/outputs/forecast_workup_volume.png).
- **Bar/line combo**: intake (demand) vs. completion per month → **capacity gap**.
- **Tile**: model accuracy — back-test **MAPE 12.5%** (MAE ≈ 15.8 matters/month).

**Slicers:** date range, case type.

## Capture checklist
- [ ] Forecast visually distinct from actuals (dashed + shaded interval)
- [ ] Uncertainty band shown (not a false-precision single line)
- [ ] MAPE / back-test accuracy disclosed on the page
- [ ] Capacity gap (intake − completions) called out
