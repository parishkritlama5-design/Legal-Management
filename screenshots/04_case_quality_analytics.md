# Screenshot Placeholder — Case Quality Analytics

**File to capture:** `case_quality_analytics.png`
**Audience:** Attorneys, Director of Operations

## What this screenshot should show
How case "workup quality" varies and how it relates to outcomes.

**Visuals:**
- **Bar**: % high-quality cases by type (records received + zero missing docs +
  adequate communication). Mass torts trail (Talcum 41.3%, Camp Lejeune 43.9%).
- **Matrix**: % records received, avg missing docs, avg communication by type.
- **Scatter**: settlement amount vs. communication count / missing docs
  (quality ↔ value relationship), one point per settled case.
- **Reference**: [`../python/outputs/eda_completion_by_type.png`](../python/outputs/eda_completion_by_type.png).

**Slicers:** case type, attorney, state.

## Capture checklist
- [ ] Quality components broken out, not just a black-box score
- [ ] Scatter uses zero-baseline axes and notes correlation ≠ causation
- [ ] Mass-tort underperformance clearly visible
