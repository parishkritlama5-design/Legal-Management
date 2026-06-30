"""
build_dashboard.py
================================================================================
Builds an interactive HTML dashboard from the cleaned case data using Plotly.

How it works, in plain English:
  1. Load the cleaned cases (and case managers) with pandas.
  2. Work out the headline numbers (the KPI tiles).
  3. Make one chart at a time, each in its own small function.
  4. Drop all the charts into one HTML page and save it.

Open the result by double-clicking it:
  dashboards/legal_case_dashboard.html   (works offline, no server needed)

Run (after the pipeline):  python build_dashboard.py
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs


# --------------------------------------------------------------------------- #
# 1. Settings: colors, the stage order, and where files live
# --------------------------------------------------------------------------- #
NAVY = "#1f2a44"
TEAL = "#2a9d8f"
CORAL = "#e76f51"
SLATE = "#577590"

# The order a case moves through the pipeline (left to right).
STAGES = ["Intake", "Retainer Signed", "Records Requested", "Records Received",
          "Workup Complete", "Demand Sent", "Negotiation", "Resolved"]

# Build absolute paths so the script works no matter where you run it from.
FOLDER = os.path.dirname(__file__)
CASES_FILE = os.path.join(FOLDER, "..", "data", "processed", "cases_clean.csv")
MANAGERS_FILE = os.path.join(FOLDER, "..", "data", "case_managers.csv")
FORECAST_FILE = os.path.join(FOLDER, "outputs", "forecast_workup_volume.csv")
OUTPUT_FILE = os.path.join(FOLDER, "..", "dashboards", "legal_case_dashboard.html")


def style_chart(fig, title):
    """Give every chart the same clean, consistent look."""
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=380,
        margin=dict(l=60, r=30, t=55, b=50),
        font=dict(family="Segoe UI, Arial", size=12, color="#23314e"),
        title_font=dict(size=16, color=NAVY),
    )
    return fig


# --------------------------------------------------------------------------- #
# 2. The KPI tiles (the row of big numbers at the top)
# --------------------------------------------------------------------------- #
def make_kpi_tiles(cases):
    """Return the HTML for the six headline-number cards."""
    total = len(cases)
    open_cases = int(cases["is_open"].sum())
    completion = 100 * cases["workup_completed"].mean()

    resolved = cases["case_status"].isin(["Settled", "Closed-Lost", "Dropped"]).sum()
    settled = (cases["case_status"] == "Settled").sum()
    settlement_rate = 100 * settled / max(resolved, 1)

    settlement_value = cases.loc[cases["settlement_amount"] > 0, "settlement_amount"].sum()
    stalled = int(((cases["is_open"] == 1) & (cases["days_inactive"] > 30)).sum())

    # Each tile is: (label, value, accent color)
    tiles = [
        ("Total Cases", f"{total:,}", NAVY),
        ("Open Cases", f"{open_cases:,}", SLATE),
        ("Workup Completion", f"{completion:.1f}%", TEAL),
        ("Settlement Rate", f"{settlement_rate:.1f}%", TEAL),
        ("Settlement Value", f"${settlement_value / 1e6:.1f}M", NAVY),
        ("Stalled >30d", f"{stalled:,}", CORAL),
    ]

    html = ""
    for label, value, color in tiles:
        html += (
            f'<div class="kpi">'
            f'  <div class="kpi-label">{label}</div>'
            f'  <div class="kpi-value" style="color:{color}">{value}</div>'
            f'</div>'
        )
    return html


# --------------------------------------------------------------------------- #
# 3. The charts -- one simple function each
# --------------------------------------------------------------------------- #
def chart_funnel(cases):
    """How many cases have reached (or passed) each pipeline stage."""
    # Give each stage a number so we can compare "how far along" a case is.
    stage_number = cases["current_stage"].map({name: i for i, name in enumerate(STAGES)})

    # A case "at or beyond" stage i has a stage number >= i.
    counts = []
    for i in range(len(STAGES)):
        counts.append(int((stage_number >= i).sum()))

    fig = go.Figure(go.Funnel(
        y=STAGES,
        x=counts,
        textposition="inside",
        texttemplate="%{x:,} (%{percentInitial})",
        marker_color=TEAL,
    ))
    return style_chart(fig, "Client Workup Funnel (cases at or beyond each stage)")


def chart_completion_by_type(cases):
    """Workup completion rate for each case type, vs. the firm average."""
    rate = cases.groupby("case_type")["workup_completed"].mean().mul(100).sort_values()
    firm_average = 100 * cases["workup_completed"].mean()

    # Green if at/above the firm average, coral if below.
    bar_colors = []
    for value in rate.values:
        bar_colors.append(TEAL if value >= firm_average else CORAL)

    fig = go.Figure(go.Bar(
        x=rate.values,
        y=rate.index,
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.0f}%" for v in rate.values],
        textposition="outside",
    ))
    fig.add_vline(x=firm_average, line_dash="dash", line_color=SLATE,
                  annotation_text=f"firm avg {firm_average:.0f}%")
    fig.update_xaxes(range=[0, 100], title="Completion rate (%)")
    return style_chart(fig, "Workup Completion Rate by Case Type")


def chart_forecast():
    """Monthly new-matter demand: history plus the 6-month forecast."""
    data = pd.read_csv(FORECAST_FILE, parse_dates=["month"])
    actual = data[data["type"] == "actual"]
    forecast = data[data["type"] == "forecast"]

    fig = go.Figure()

    # Shaded 80% confidence band around the forecast.
    fig.add_trace(go.Scatter(
        x=list(forecast["month"]) + list(forecast["month"][::-1]),
        y=list(forecast["upper_80"]) + list(forecast["lower_80"][::-1]),
        fill="toself", fillcolor="rgba(231,111,81,0.15)",
        line_color="rgba(0,0,0,0)", hoverinfo="skip", name="80% interval",
    ))
    # The actual history (solid navy line).
    fig.add_trace(go.Scatter(
        x=actual["month"], y=actual["new_matters"],
        mode="lines+markers", line=dict(color=NAVY, width=2), name="Actual",
    ))
    # The forecast (dashed coral line).
    fig.add_trace(go.Scatter(
        x=forecast["month"], y=forecast["new_matters"],
        mode="lines+markers", line=dict(color=CORAL, width=2, dash="dash"),
        name="Forecast",
    ))
    fig.update_layout(xaxis_title="Month", yaxis_title="New matters / month",
                      legend=dict(orientation="h", y=-0.25))
    return style_chart(fig, "Monthly Workup Demand (new matters) - Actual & 6-Month Forecast")


def chart_manager_productivity(cases, managers):
    """Workup completion rate for each case manager."""
    # Completion rate and caseload per manager.
    summary = (cases.groupby("assigned_case_manager")["workup_completed"]
               .agg(caseload="size", completion="mean")
               .reset_index())
    summary["completion"] = 100 * summary["completion"]

    # Add the manager names.
    summary = summary.merge(
        managers[["case_manager_id", "manager_name"]],
        left_on="assigned_case_manager", right_on="case_manager_id", how="left",
    ).sort_values("completion")

    fig = px.bar(
        summary, x="completion", y="manager_name", orientation="h",
        color="completion", color_continuous_scale="Teal",
        hover_data={"caseload": True, "completion": ":.1f"},
        labels={"completion": "Completion %", "manager_name": ""},
    )
    fig.update_coloraxes(showscale=False)
    fig = style_chart(fig, "Case-Manager Productivity (workup completion %)")
    fig.update_layout(height=460)
    return fig


def chart_bottleneck(cases):
    """Where open cases pile up: count and average days per stage."""
    open_cases = cases[cases["is_open"] == 1]
    open_stages = [s for s in STAGES if s != "Resolved"]

    counts = []
    avg_days = []
    for stage in open_stages:
        in_stage = open_cases[open_cases["current_stage"] == stage]
        counts.append(len(in_stage))
        valid_days = in_stage.loc[in_stage["days_in_stage"] >= 0, "days_in_stage"]
        avg_days.append(valid_days.mean())

    fig = go.Figure()
    # Bars: how many open cases sit in each stage.
    fig.add_trace(go.Bar(x=open_stages, y=counts, marker_color=NAVY,
                         name="Open cases"))
    # Line on a second axis: average days stuck in each stage.
    fig.add_trace(go.Scatter(x=open_stages, y=avg_days, mode="lines+markers",
                             line=dict(color=CORAL, width=2),
                             name="Avg days in stage", yaxis="y2"))
    fig.update_layout(
        yaxis=dict(title="Open cases"),
        yaxis2=dict(title="Avg days in stage", overlaying="y", side="right",
                    showgrid=False),
        legend=dict(orientation="h", y=-0.3),
    )
    fig.update_xaxes(tickangle=-30)
    fig = style_chart(fig, "Operational Bottleneck - Open Cases & Avg Days by Stage")
    fig.update_layout(height=400)
    return fig


def chart_case_mix(cases):
    """How many cases of each type the firm holds."""
    counts = cases["case_type"].value_counts().sort_values()
    fig = px.bar(x=counts.values, y=counts.index, orientation="h",
                 labels={"x": "Cases", "y": ""})
    fig.update_traces(marker_color=SLATE, text=counts.values, textposition="outside")
    return style_chart(fig, "Case Mix by Type")


def chart_status(cases):
    """The split of cases across statuses."""
    counts = cases["case_status"].value_counts()
    fig = px.pie(names=counts.index, values=counts.values, hole=0.45)
    return style_chart(fig, "Case Status Distribution")


# --------------------------------------------------------------------------- #
# 4. Build the HTML page and save it
# --------------------------------------------------------------------------- #
def chart_to_html(fig, name):
    """Turn one Plotly figure into an HTML snippet (no extra page wrapper)."""
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=name,
                       config={"displayModeBar": True, "responsive": True})


def main():
    # Load the data once.
    cases = pd.read_csv(CASES_FILE)
    managers = pd.read_csv(MANAGERS_FILE)

    # Build the KPI row.
    kpi_html = make_kpi_tiles(cases)

    # The forecast gets its own full-width row.
    forecast_html = chart_to_html(chart_forecast(), "forecast")

    # The rest go into a two-column grid.
    grid_charts = [
        ("funnel", chart_funnel(cases)),
        ("completion", chart_completion_by_type(cases)),
        ("manager", chart_manager_productivity(cases, managers)),
        ("bottleneck", chart_bottleneck(cases)),
        ("casemix", chart_case_mix(cases)),
        ("status", chart_status(cases)),
    ]
    grid_html = ""
    for name, fig in grid_charts:
        grid_html += f'<div class="card">{chart_to_html(fig, name)}</div>'

    # The page: a header, the KPI row, the forecast, then the grid.
    # get_plotlyjs() embeds the chart engine so the file works offline.
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Legal Case Management Intelligence - Dashboard</title>
<script>{get_plotlyjs()}</script>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#f4f6f9; font-family:'Segoe UI',Arial,sans-serif; color:#23314e; }}
  header {{ background:linear-gradient(120deg,#1f2a44,#2a9d8f); color:#fff; padding:22px 32px; }}
  header h1 {{ margin:0; font-size:22px; }}
  header p {{ margin:6px 0 0; opacity:.85; font-size:13px; }}
  .wrap {{ max-width:1320px; margin:0 auto; padding:20px 24px 48px; }}
  .kpi-row {{ display:grid; grid-template-columns:repeat(6,1fr); gap:14px; margin:18px 0; }}
  .kpi {{ background:#fff; border-radius:12px; padding:16px 14px;
          box-shadow:0 1px 3px rgba(20,30,60,.08); border-top:4px solid {TEAL}; }}
  .kpi-label {{ font-size:12px; color:#5a6b85; text-transform:uppercase; }}
  .kpi-value {{ font-size:26px; font-weight:700; margin-top:6px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:18px; }}
  .card {{ background:#fff; border-radius:12px; padding:8px 12px;
           box-shadow:0 1px 3px rgba(20,30,60,.08); }}
  .full {{ grid-column:1 / -1; }}
  @media (max-width:1000px) {{
    .kpi-row {{ grid-template-columns:repeat(3,1fr); }}
    .grid {{ grid-template-columns:1fr; }}
  }}
</style>
</head>
<body>
  <header>
    <h1>&#9878;&#65039; Legal Case Management Intelligence &mdash; Operations Dashboard</h1>
    <p>Plaintiff-side / mass-tort litigation pipeline &bull; snapshot 2025-06-30 &bull;
       synthetic data &bull; interactive (hover, zoom, pan)</p>
  </header>
  <div class="wrap">
    <div class="kpi-row">{kpi_html}</div>
    <div class="grid">
      <div class="card full">{forecast_html}</div>
      {grid_html}
    </div>
  </div>
</body>
</html>"""

    # Make sure the dashboards/ folder exists, then write the file.
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(page)

    size_mb = os.path.getsize(OUTPUT_FILE) / 1e6
    print(f"Dashboard saved -> {os.path.normpath(OUTPUT_FILE)} ({size_mb:.1f} MB)")
    print("Open it by double-clicking, or run: open dashboards/legal_case_dashboard.html")


if __name__ == "__main__":
    main()
