"""
03_forecasting.py
================================================================================
Forecasts monthly CASE-WORKUP DEMAND -- the number of new matters entering the
workup pipeline each month (cases opened) -- for the next 6 months.

Why this target (methodology note)
----------------------------------
We forecast intake/opened volume rather than *completion* volume on purpose:
  * It is the leading indicator the workup team plans capacity against ("how much
    work is coming"), which is the business question.
  * It is measured on a known, exact date (date_opened) with NO right-censoring.
    Completion volume, by contrast, is right-censored -- recently opened matters
    have not yet finished workup -- which biases the most recent months downward
    and corrupts a back-test (flagged in methodology review, finding H2).
The dataset still carries workup_completed_date for completion-cycle analysis;
we simply do not forecast a censored series.

Method
------
A transparent, auditable time-series regression rather than a black box:
    demand_t ~ linear_trend(t) + month-of-year seasonal dummies
fit with Ridge regression (scikit-learn). The series is short (~24 months), so a
small, regularized linear model with explicit seasonality is more honest than an
over-parameterized one.

Honest evaluation
-----------------
The last 4 months are held out as a back-test. We report MAE and MAPE on that
holdout BEFORE refitting on the full series to project the future. The forecast
interval is anchored on the back-test error (not in-sample residuals) and widens
with horizon. A one-time marketing-driven intake surge exists in the history;
a pure trend+seasonal model cannot fully capture a one-off, which we disclose.

Outputs
-------
  python/outputs/forecast_workup_volume.csv   (history + 6-month forecast)
  python/outputs/forecast_workup_volume.png

Run (after 01_data_cleaning.py):  python 03_forecasting.py
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline as sk_make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(__file__)
PROC = os.path.join(HERE, "..", "data", "processed")
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

HOLDOUT_MONTHS = 4
FORECAST_HORIZON = 6


def build_design(months_index: np.ndarray, month_of_year: np.ndarray) -> np.ndarray:
    """Design matrix: [trend, 11 seasonal dummies] (December as baseline)."""
    trend = months_index.reshape(-1, 1).astype(float)
    dummies = np.zeros((len(month_of_year), 11))
    for i, m in enumerate(month_of_year):
        if m != 12:
            dummies[i, m - 1] = 1.0
    return np.hstack([trend, dummies])


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if not mask.any():            # all-zero holdout -> MAPE undefined
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def main() -> None:
    cases = pd.read_csv(os.path.join(PROC, "cases_clean.csv"),
                        parse_dates=["date_opened"])

    # Monthly workup DEMAND = new matters entering the pipeline, indexed by the
    # exact, uncensored date the matter was opened.
    s = cases.set_index("date_opened").resample("MS").size().asfreq("MS", fill_value=0)

    # Guard: drop a trailing month only if it is clearly a partial/incomplete
    # period (well below the recent trend). date_opened is not censored, so this
    # rarely fires -- it is a safety net for a snapshot taken mid-month.
    while len(s) > 6 and s.iloc[-1] < 0.55 * s.iloc[-4:-1].mean():
        print(f"Dropping incomplete trailing month {s.index[-1].date()} "
              f"(value {int(s.iloc[-1])} << recent mean).")
        s = s.iloc[:-1]

    print("=" * 70)
    print("FORECAST - Monthly Workup Demand (new matters entering pipeline)")
    print("=" * 70)
    print(f"History: {s.index[0].date()} -> {s.index[-1].date()} "
          f"({len(s)} months)")

    y = s.values.astype(float)
    t = np.arange(len(y))
    moy = s.index.month.values

    # Need enough history to leave a usable training set after the holdout.
    if len(y) <= HOLDOUT_MONTHS + 6:
        raise SystemExit(
            f"Series too short for a back-test: {len(y)} months "
            f"(need > {HOLDOUT_MONTHS + 6}). Widen the intake window in "
            f"generate_data.py.")

    # ---- Back-test on the last HOLDOUT_MONTHS ---- #
    tr = slice(0, len(y) - HOLDOUT_MONTHS)
    te = slice(len(y) - HOLDOUT_MONTHS, len(y))
    Xtr = build_design(t[tr], moy[tr]); Xte = build_design(t[te], moy[te])
    # Standardize features so the trend column doesn't dominate the solver.
    bt = sk_make_pipeline(StandardScaler(), Ridge(alpha=1.0, solver="lsqr")).fit(Xtr, y[tr])
    pred_te = np.clip(bt.predict(Xte), 0, None)

    bt_mae = mean_absolute_error(y[te], pred_te)
    bt_mape = mape(y[te], pred_te)
    print(f"\nBack-test (last {HOLDOUT_MONTHS} months):")
    print(f"  MAE  = {bt_mae:.1f} workups/month")
    print(f"  MAPE = {bt_mape:.1f}%")
    print(f"  Mean actual over holdout = {y[te].mean():.1f}/month")

    # ---- Refit on full history, project forward ---- #
    Xfull = build_design(t, moy)
    model = sk_make_pipeline(StandardScaler(), Ridge(alpha=1.0, solver="lsqr")).fit(Xfull, y)

    future_idx = pd.date_range(s.index[-1] + pd.offsets.MonthBegin(1),
                               periods=FORECAST_HORIZON, freq="MS")
    ft = np.arange(len(y), len(y) + FORECAST_HORIZON)
    fmoy = future_idx.month.values
    Xf = build_design(ft, fmoy)
    fc = np.clip(model.predict(Xf), 0, None)

    # Uncertainty band anchored on the HONEST back-test error (not in-sample
    # residuals, which understate forecast error), and widened with the forecast
    # horizon (error compounds the further out we project). ~80% heuristic band.
    horizons = np.arange(1, FORECAST_HORIZON + 1)
    band = 1.6 * bt_mae * np.sqrt(horizons)   # MAE->~80% width, growing as sqrt(h)
    lo = np.clip(fc - band, 0, None)
    hi = fc + band

    print(f"\n6-month forecast (new matters/month):")
    for d, f in zip(future_idx, fc):
        print(f"  {d.strftime('%Y-%m')}: {f:,.0f}")

    # ---- Persist CSV ---- #
    # Column is new_matters (demand), NOT completions -- see module docstring.
    hist_df = pd.DataFrame({"month": s.index, "new_matters": y,
                            "type": "actual"})
    fc_df = pd.DataFrame({"month": future_idx, "new_matters": fc.round(1),
                          "type": "forecast", "lower_80": lo.round(1),
                          "upper_80": hi.round(1)})
    out = pd.concat([hist_df, fc_df], ignore_index=True)
    out.to_csv(os.path.join(OUT, "forecast_workup_volume.csv"), index=False)

    # ---- Plot ---- #
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(s.index, y, marker="o", color="#1f2a44", lw=2, label="Actual")
    ax.plot(future_idx, fc, marker="o", color="#e76f51", lw=2, ls="--",
            label="Forecast")
    ax.fill_between(future_idx, lo, hi, color="#e76f51", alpha=0.18,
                    label="80% interval")
    ax.set_title("Monthly Workup Demand (New Matters) - Actual & 6-Month Forecast")
    ax.set_xlabel("Month"); ax.set_ylabel("New matters entering pipeline")
    ax.grid(alpha=0.3); ax.legend()
    fig.savefig(os.path.join(OUT, "forecast_workup_volume.png"),
                bbox_inches="tight", dpi=110)
    plt.close(fig)

    print(f"\nSaved forecast CSV + chart to {OUT}/")


if __name__ == "__main__":
    main()
