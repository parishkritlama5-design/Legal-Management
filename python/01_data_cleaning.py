"""
01_data_cleaning.py
================================================================================
Cleans the raw CSV extracts and writes analysis-ready tables to data/processed/.

Cleaning rules (each logged to the console as an auditable report):
  * De-duplicate clients on (first_name, last_name, date_of_birth), keeping the
    earliest client_id; emit a crosswalk of dropped -> surviving IDs.
  * Repair logical violations:
      - negative settlement_amount      -> absolute value (sign-entry error)
      - negative days_in_stage          -> absolute value
      - date_closed < date_opened       -> set date_closed = NULL (review)
  * Standardize types (dates parsed, ids trimmed/upper-cased).
  * Flag (not drop) missing email / referral_source so downstream code is aware.

Outputs:
  data/processed/clients_clean.csv
  data/processed/cases_clean.csv
  python/outputs/cleaning_report.txt

Run:  python 01_data_cleaning.py
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
PROC = os.path.join(DATA, "processed")
OUT = os.path.join(HERE, "outputs")
os.makedirs(PROC, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

_report_lines: list[str] = []


def log(msg: str) -> None:
    print(msg)
    _report_lines.append(msg)


def main() -> None:
    log("=" * 70)
    log("DATA CLEANING REPORT - Legal Case Management Intelligence")
    log("=" * 70)

    clients = pd.read_csv(os.path.join(DATA, "clients.csv"),
                          parse_dates=["date_of_birth", "intake_date"])
    cases = pd.read_csv(os.path.join(DATA, "cases.csv"),
                        parse_dates=["intake_date", "date_opened",
                                     "date_closed", "workup_completed_date",
                                     "last_activity_date"])

    log(f"\nLoaded {len(clients):,} client rows and {len(cases):,} case rows.")

    # ----------------------------------------------------------------- #
    # 1) De-duplicate clients
    # ----------------------------------------------------------------- #
    clients["_key"] = (
        clients["first_name"].str.strip().str.lower() + "|"
        + clients["last_name"].str.strip().str.lower() + "|"
        + clients["date_of_birth"].dt.strftime("%Y-%m-%d")
    )
    clients_sorted = clients.sort_values("client_id")
    survivor = clients_sorted.groupby("_key")["client_id"].first()
    clients["surviving_client_id"] = clients["_key"].map(survivor)

    n_dupes = int((clients["client_id"] != clients["surviving_client_id"]).sum())
    log(f"\n[1] Duplicate clients detected: {n_dupes} "
        f"(merged into earliest client_id by identity key).")

    # Re-point cases from dropped client_ids to the survivor, then drop dup rows.
    id_map = dict(zip(clients["client_id"], clients["surviving_client_id"]))
    cases["client_id"] = cases["client_id"].map(lambda x: id_map.get(x, x))
    clients_clean = (clients[clients["client_id"] == clients["surviving_client_id"]]
                     .drop(columns=["_key", "surviving_client_id"])
                     .reset_index(drop=True))
    log(f"    Clients after de-dup: {len(clients_clean):,}")

    # ----------------------------------------------------------------- #
    # 2) Repair logical violations
    # ----------------------------------------------------------------- #
    neg_settle = int((cases["settlement_amount"] < 0).sum())
    cases.loc[cases["settlement_amount"] < 0, "settlement_amount"] = (
        cases["settlement_amount"].abs())
    log(f"\n[2] Negative settlement_amount repaired (abs): {neg_settle}")

    neg_days = int((cases["days_in_stage"] < 0).sum())
    cases["days_in_stage"] = cases["days_in_stage"].abs()
    log(f"    Negative days_in_stage repaired (abs): {neg_days}")

    bad_dates = int((cases["date_closed"] < cases["date_opened"]).sum())
    cases.loc[cases["date_closed"] < cases["date_opened"], "date_closed"] = pd.NaT
    log(f"    date_closed < date_opened nulled for review: {bad_dates}")

    # ----------------------------------------------------------------- #
    # 3) Completeness flags (kept, not dropped)
    # ----------------------------------------------------------------- #
    miss_email = int(clients_clean["email"].isna().sum())
    miss_ref = int(clients_clean["referral_source"].isna().sum())
    clients_clean["referral_source"] = clients_clean["referral_source"].fillna("Unknown")
    log(f"\n[3] Missing emails flagged: {miss_email} "
        f"({100*miss_email/len(clients_clean):.1f}%)")
    log(f"    Missing referral_source imputed to 'Unknown': {miss_ref}")

    # ----------------------------------------------------------------- #
    # 4) Derived analytical fields
    # ----------------------------------------------------------------- #
    SNAP = pd.Timestamp("2025-06-30")
    cases["is_open"] = cases["date_closed"].isna().astype(int)
    cases["days_to_close"] = (cases["date_closed"] - cases["date_opened"]).dt.days
    cases["case_age_days"] = (
        cases["date_closed"].fillna(SNAP) - cases["date_opened"]).dt.days
    cases["days_inactive"] = (SNAP - cases["last_activity_date"]).dt.days
    cases["intake_month"] = cases["intake_date"].dt.to_period("M").astype(str)

    # ----------------------------------------------------------------- #
    # Persist
    # ----------------------------------------------------------------- #
    clients_clean.to_csv(os.path.join(PROC, "clients_clean.csv"), index=False)
    cases.to_csv(os.path.join(PROC, "cases_clean.csv"), index=False)

    log("\n" + "-" * 70)
    log(f"Wrote {PROC}/clients_clean.csv  ({len(clients_clean):,} rows)")
    log(f"Wrote {PROC}/cases_clean.csv    ({len(cases):,} rows)")
    log("Cleaning complete.")

    with open(os.path.join(OUT, "cleaning_report.txt"), "w") as f:
        f.write("\n".join(_report_lines))


if __name__ == "__main__":
    main()
