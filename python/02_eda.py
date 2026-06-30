"""
02_eda.py
================================================================================
Exploratory data analysis on the cleaned case data. Prints a structured profile
to the console and saves publication-quality figures to python/outputs/.

Figures produced:
  eda_intake_trend.png       - monthly new-client intake over time
  eda_case_mix.png           - case volume by case type
  eda_completion_by_type.png - workup completion rate by case type
  eda_funnel.png             - workup funnel (cases at-or-beyond each stage)
  eda_cycle_time.png         - distribution of days-to-close

Run (after 01_data_cleaning.py):  python 02_eda.py
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
PROC = os.path.join(HERE, "..", "data", "processed")
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "savefig.bbox": "tight",
                     "axes.grid": True, "grid.alpha": 0.3, "font.size": 10})
NAVY = "#1f2a44"
TEAL = "#2a9d8f"

STAGES = ["Intake", "Retainer Signed", "Records Requested", "Records Received",
          "Workup Complete", "Demand Sent", "Negotiation", "Resolved"]


def main() -> None:
    cases = pd.read_csv(os.path.join(PROC, "cases_clean.csv"),
                        parse_dates=["intake_date", "date_opened",
                                     "date_closed", "last_activity_date"])
    clients = pd.read_csv(os.path.join(PROC, "clients_clean.csv"),
                          parse_dates=["intake_date"])

    print("=" * 70)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 70)
    print(f"\nCases: {len(cases):,} | Clients: {len(clients):,}")
    print(f"Date range (intake): {clients['intake_date'].min().date()} "
          f"-> {clients['intake_date'].max().date()}")
    print(f"\nOverall workup completion rate: "
          f"{100*cases['workup_completed'].mean():.1f}%")
    print(f"Open cases: {int(cases['is_open'].sum()):,} "
          f"({100*cases['is_open'].mean():.1f}%)")

    settled = cases[cases["case_status"] == "Settled"]
    resolved = cases[cases["case_status"].isin(["Settled", "Closed-Lost", "Dropped"])]
    print(f"\nSettlement rate (of resolved): "
          f"{100*len(settled)/max(len(resolved),1):.1f}%")
    print(f"Avg settlement (settled): "
          f"${settled['settlement_amount'].mean():,.0f}")
    print(f"Total settlement value: "
          f"${settled['settlement_amount'].sum():,.0f}")

    print("\nCompletion rate by case type:")
    by_type = (cases.groupby("case_type")["workup_completed"]
               .agg(["count", "mean"]).sort_values("mean", ascending=False))
    for t, r in by_type.iterrows():
        print(f"  {t:28s} n={int(r['count']):>4d}  {100*r['mean']:>5.1f}%")

    # ---------------- Figure 1: intake trend ---------------- #
    monthly = (clients.set_index("intake_date").resample("MS").size())
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(monthly.index, monthly.values, marker="o", color=NAVY, lw=2)
    ax.set_title("Monthly New-Client Intake")
    ax.set_xlabel("Month"); ax.set_ylabel("New clients")
    fig.savefig(os.path.join(OUT, "eda_intake_trend.png")); plt.close(fig)

    # ---------------- Figure 2: case mix ---------------- #
    mix = cases["case_type"].value_counts()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(mix.index[::-1], mix.values[::-1], color=TEAL)
    ax.set_title("Case Mix by Type"); ax.set_xlabel("Cases")
    fig.savefig(os.path.join(OUT, "eda_case_mix.png")); plt.close(fig)

    # ---------------- Figure 3: completion by type ---------------- #
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(by_type.index[::-1], (100*by_type["mean"])[::-1], color=NAVY)
    ax.set_title("Workup Completion Rate by Case Type")
    ax.set_xlabel("Completion rate (%)")
    fig.savefig(os.path.join(OUT, "eda_completion_by_type.png")); plt.close(fig)

    # ---------------- Figure 4: funnel ---------------- #
    order = {s: i for i, s in enumerate(STAGES)}
    cases["_stageord"] = cases["current_stage"].map(order)
    funnel = [int((cases["_stageord"] >= i).sum()) for i in range(len(STAGES))]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(STAGES[::-1], funnel[::-1], color=TEAL)
    for i, v in enumerate(funnel[::-1]):
        ax.text(v, i, f" {v:,}", va="center", fontsize=9)
    ax.set_title("Client Workup Funnel (cases at or beyond each stage)")
    ax.set_xlabel("Cases")
    fig.savefig(os.path.join(OUT, "eda_funnel.png")); plt.close(fig)

    # ---------------- Figure 5: cycle time ---------------- #
    dtc = cases["days_to_close"].dropna()
    dtc = dtc[(dtc >= 0) & (dtc <= dtc.quantile(0.99))]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(dtc, bins=40, color=NAVY, alpha=0.85)
    ax.axvline(dtc.median(), color=TEAL, lw=2, ls="--",
               label=f"median {dtc.median():.0f} d")
    ax.set_title("Days to Close (resolved cases)")
    ax.set_xlabel("Days"); ax.set_ylabel("Cases"); ax.legend()
    fig.savefig(os.path.join(OUT, "eda_cycle_time.png")); plt.close(fig)

    print(f"\nSaved 5 EDA figures to {OUT}/")


if __name__ == "__main__":
    main()
