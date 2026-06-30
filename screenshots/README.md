# Screenshots

This folder holds the visual proof points for the dashboards. Until the BI
dashboards (Power BI / Sigma) are published, each page below has a **placeholder
spec** describing exactly what the screenshot should show and which numbers must
be visible. Drop the exported PNGs alongside each spec using the suggested file
name.

> **Live, code-generated charts already exist** in [`../python/outputs/`](../python/outputs/)
> (EDA, forecast, ROC curve, feature importance). Those are produced by the
> Python pipeline and can be embedded directly; the items below are the BI
> dashboard captures still to be taken.

| # | Dashboard page | Placeholder spec | Suggested screenshot file |
|---|----------------|------------------|---------------------------|
| 1 | Executive Overview | [01_executive_overview.md](01_executive_overview.md) | `executive_overview.png` |
| 2 | Client Workup Funnel | [02_client_workup_funnel.md](02_client_workup_funnel.md) | `client_workup_funnel.png` |
| 3 | Case Manager Productivity | [03_case_manager_productivity.md](03_case_manager_productivity.md) | `case_manager_productivity.png` |
| 4 | Case Quality Analytics | [04_case_quality_analytics.md](04_case_quality_analytics.md) | `case_quality_analytics.png` |
| 5 | Forecasting Dashboard | [05_forecasting_dashboard.md](05_forecasting_dashboard.md) | `forecasting_dashboard.png` |
| 6 | Data Quality Dashboard | [06_data_quality_dashboard.md](06_data_quality_dashboard.md) | `data_quality_dashboard.png` |
| 7 | Operational Bottleneck | [07_operational_bottleneck.md](07_operational_bottleneck.md) | `operational_bottleneck.png` |

See [`../dashboards/dashboard_specifications.md`](../dashboards/dashboard_specifications.md)
for the full design spec behind each page.
