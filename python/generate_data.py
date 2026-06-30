"""
generate_data.py
================================================================================
Synthetic data generator for the Legal Case Management Intelligence Platform.

Produces nine internally-consistent CSV extracts that mimic the operational
data of a mid-size plaintiff-side / mass-tort law firm:

    clients, attorneys, case_managers, cases, activities, documents,
    medical_records, settlements, call_logs

Design goals
------------
1. Referential integrity  - every foreign key resolves to a real parent row.
2. Predictive signal       - `workup_completed` is driven by communication
                             volume, missing documents, medical-record receipt,
                             time-in-stage and case-manager effectiveness, so the
                             downstream classifier learns something real.
3. Realistic seasonality   - monthly intake has trend + seasonal swings so the
                             forecasting model has a meaningful series.
4. Intentional dirt        - duplicate clients, missing values and a few logical
                             anomalies are injected so the data-quality SQL and
                             the Python cleaning step have something to catch.

Run:
    python generate_data.py            # writes ../data/*.csv

Author: Strategic Operations Analytics
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 42
rng = np.random.default_rng(SEED)

N_CLIENTS = 2_500
N_ATTORNEYS = 12
N_CASE_MANAGERS = 18

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

INTAKE_START = date(2023, 7, 1)
INTAKE_END = date(2025, 6, 30)
SNAPSHOT_DATE = date(2025, 6, 30)  # "today" for days-in-stage / inactivity calcs

US_STATES = [
    "CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI",
    "NJ", "VA", "AZ", "TN", "MO", "LA", "AL", "MS",
]
# Weight a few high-volume plaintiff states heavier.
STATE_WEIGHTS = np.array(
    [16, 14, 12, 8, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 2], dtype=float
)
STATE_WEIGHTS /= STATE_WEIGHTS.sum()

CASE_TYPES = {
    # case_type: (relative_volume, base_settlement, completion_baseline)
    "Motor Vehicle Accident":   (0.28, 32_000, 0.78),
    "Premises Liability":       (0.10, 41_000, 0.70),
    "Slip and Fall":            (0.09, 28_000, 0.68),
    "Medical Malpractice":      (0.06, 240_000, 0.55),
    "Product Liability":        (0.05, 95_000, 0.60),
    "Workers Compensation":     (0.08, 36_000, 0.72),
    "Dog Bite":                 (0.04, 22_000, 0.74),
    "Wrongful Death":           (0.03, 380_000, 0.50),
    "Nursing Home Negligence":  (0.04, 160_000, 0.52),
    "Mass Tort - Roundup":      (0.07, 110_000, 0.45),
    "Mass Tort - Camp Lejeune": (0.06, 130_000, 0.42),
    "Mass Tort - Talcum":       (0.05, 90_000, 0.44),
}

REFERRAL_SOURCES = [
    "Google / SEO", "TV Advertising", "Attorney Referral", "Past Client",
    "Social Media", "Billboard", "Legal Directory", "Radio", "Other",
]
REFERRAL_WEIGHTS = np.array([26, 20, 14, 12, 10, 6, 5, 4, 3], dtype=float)
REFERRAL_WEIGHTS /= REFERRAL_WEIGHTS.sum()

# Linear funnel of workup stages. Index order matters (monotonic progression).
WORKUP_STAGES = [
    "Intake",
    "Retainer Signed",
    "Records Requested",
    "Records Received",
    "Workup Complete",
    "Demand Sent",
    "Negotiation",
    "Resolved",
]
WORKUP_COMPLETE_INDEX = WORKUP_STAGES.index("Workup Complete")

# Target service-level (in days) for time spent in each stage.
STAGE_SLA_DAYS = {
    "Intake": 3,
    "Retainer Signed": 5,
    "Records Requested": 30,
    "Records Received": 21,
    "Workup Complete": 14,
    "Demand Sent": 21,
    "Negotiation": 45,
    "Resolved": 0,
}

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Carlos", "Maria", "Andre",
    "Aisha", "Wei", "Mei", "Diego", "Sofia", "Hassan", "Fatima", "Kevin",
    "Nicole", "Brandon", "Destiny", "Tyler", "Ashley", "Jamal", "Keisha",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Nguyen", "Patel", "Okafor", "Cohen", "Ali",
]


def _rand_dates(start: date, end: date, size: int, weights=None) -> np.ndarray:
    """Vector of random dates in [start, end]; optional per-day weights."""
    span = (end - start).days
    if weights is None:
        offsets = rng.integers(0, span + 1, size=size)
    else:
        # weights must align 1:1 with the inclusive day range [start, end].
        assert len(weights) == span + 1, (
            f"weights length {len(weights)} != day count {span + 1}")
        offsets = rng.choice(np.arange(span + 1), size=size, p=weights)
    return np.array([start + timedelta(int(o)) for o in offsets])


def _monthly_intake_weights() -> np.ndarray:
    """Per-day probability weights producing trend + seasonality in intake."""
    span = (INTAKE_END - INTAKE_START).days + 1
    days = np.arange(span)
    months = days / 30.4
    trend = 1.0 + 0.020 * months                       # ~2% growth / month
    seasonal = 1.0 + 0.22 * np.sin(2 * np.pi * months / 12.0 + 0.6)
    # A marketing-driven surge window (~4-month TV campaign).
    surge = np.where((months >= 10) & (months <= 13), 1.30, 1.0)
    w = trend * seasonal * surge
    return w / w.sum()


# --------------------------------------------------------------------------- #
# Dimension tables
# --------------------------------------------------------------------------- #
def build_attorneys() -> pd.DataFrame:
    specialties = [
        "Personal Injury", "Mass Tort", "Medical Malpractice",
        "Product Liability", "Wrongful Death",
    ]
    rows = []
    for i in range(1, N_ATTORNEYS + 1):
        rows.append(
            {
                "attorney_id": f"ATT-{i:03d}",
                "attorney_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}, Esq.",
                "bar_state": rng.choice(US_STATES, p=STATE_WEIGHTS),
                "specialty": rng.choice(specialties),
                "years_experience": int(rng.integers(3, 31)),
                "hire_date": INTAKE_START - timedelta(int(rng.integers(365, 365 * 12))),
            }
        )
    return pd.DataFrame(rows)


def build_case_managers() -> pd.DataFrame:
    teams = ["Intake", "Workup Team A", "Workup Team B", "Litigation Support"]
    rows = []
    for i in range(1, N_CASE_MANAGERS + 1):
        # Latent effectiveness drives downstream completion probability.
        effectiveness = float(np.clip(rng.normal(0.0, 1.0), -2.2, 2.2))
        rows.append(
            {
                "case_manager_id": f"CM-{i:03d}",
                "manager_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                "team": rng.choice(teams, p=[0.18, 0.32, 0.32, 0.18]),
                "hire_date": INTAKE_START - timedelta(int(rng.integers(120, 365 * 8))),
                "monthly_capacity": int(rng.choice([35, 40, 45, 50, 55])),
                "_effectiveness": effectiveness,  # internal; dropped on export
            }
        )
    return pd.DataFrame(rows)


def build_clients() -> pd.DataFrame:
    intake_w = _monthly_intake_weights()
    intake_dates = _rand_dates(INTAKE_START, INTAKE_END, N_CLIENTS, weights=intake_w)
    rows = []
    for i in range(1, N_CLIENTS + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        intake = intake_dates[i - 1]
        # Age 18-82 at intake.
        age = int(rng.integers(18, 83))
        dob = date(intake.year - age, int(rng.integers(1, 13)), int(rng.integers(1, 29)))
        rows.append(
            {
                "client_id": f"CL-{i:05d}",
                "first_name": first,
                "last_name": last,
                "date_of_birth": dob,
                "gender": rng.choice(["F", "M", "X"], p=[0.49, 0.49, 0.02]),
                "state": rng.choice(US_STATES, p=STATE_WEIGHTS),
                "phone": f"({rng.integers(200,999)}) {rng.integers(200,999)}-{rng.integers(1000,9999)}",
                "email": f"{first.lower()}.{last.lower()}{rng.integers(1,999)}@example.com",
                "intake_date": intake,
                "referral_source": rng.choice(REFERRAL_SOURCES, p=REFERRAL_WEIGHTS),
                "marketing_channel": rng.choice(
                    ["Paid Search", "Organic", "Broadcast", "Referral", "Direct"],
                    p=[0.30, 0.18, 0.22, 0.20, 0.10],
                ),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Fact: cases  (the analytical core)
# --------------------------------------------------------------------------- #
def build_cases(clients: pd.DataFrame, attorneys: pd.DataFrame,
                managers: pd.DataFrame) -> pd.DataFrame:
    type_names = list(CASE_TYPES.keys())
    type_vol = np.array([CASE_TYPES[t][0] for t in type_names])
    type_vol /= type_vol.sum()

    att_ids = attorneys["attorney_id"].to_numpy()
    cm_ids = managers["case_manager_id"].to_numpy()
    cm_eff = dict(zip(managers["case_manager_id"], managers["_effectiveness"]))

    rows = []
    case_counter = 1
    for _, client in clients.iterrows():
        # ~10% of clients carry a second case (mass-tort co-claims, etc.).
        n_cases = 1 + (1 if rng.random() < 0.10 else 0)
        for _ in range(n_cases):
            case_type = rng.choice(type_names, p=type_vol)
            base_settle, completion_base = CASE_TYPES[case_type][1:]
            intake = client["intake_date"]
            attorney_id = rng.choice(att_ids)
            cm_id = rng.choice(cm_ids)

            # ---- Operational drivers ------------------------------------- #
            communication_count = int(np.clip(rng.poisson(9), 0, 60))
            medical_records_received = int(rng.random() < 0.70)
            missing_documents = int(np.clip(rng.poisson(1.6), 0, 9))

            # ---- Latent completion propensity (the signal) --------------- #
            z = (
                np.log(completion_base / (1 - completion_base))      # type baseline
                + 0.085 * (communication_count - 9)                  # engagement
                + 1.05 * medical_records_received                    # records in hand
                - 0.42 * missing_documents                           # doc friction
                + 0.80 * cm_eff[cm_id]                               # manager skill
                + rng.normal(0, 0.45)                                # noise
            )
            p_complete = 1.0 / (1.0 + np.exp(-z))
            workup_completed = int(rng.random() < p_complete)

            # ---- Stage / status consistent with completion --------------- #
            if workup_completed:
                stage_idx = int(rng.integers(WORKUP_COMPLETE_INDEX, len(WORKUP_STAGES)))
            else:
                stage_idx = int(rng.integers(0, WORKUP_COMPLETE_INDEX))
            current_stage = WORKUP_STAGES[stage_idx]

            # Days the case has lived, roughly proportional to stage reached.
            max_age = (SNAPSHOT_DATE - intake).days
            base_age = int((stage_idx + 1) / len(WORKUP_STAGES) * max(max_age, 1))
            case_age = int(np.clip(base_age + rng.integers(-20, 25), 1, max(max_age, 1)))
            days_in_stage = int(np.clip(rng.integers(1, 70) + (case_age // 30), 1, 240))

            # ---- Outcome / status ---------------------------------------- #
            resolved = current_stage == "Resolved"
            if resolved:
                settled = rng.random() < 0.74
                if settled:
                    case_status = "Settled"
                    case_outcome = "Settled"
                else:
                    case_status = rng.choice(["Closed-Lost", "Dropped"], p=[0.4, 0.6])
                    case_outcome = "Dismissed" if case_status == "Closed-Lost" else "Dropped"
            else:
                settled = False
                # A slice of in-flight cases get dropped mid-pipeline.
                if rng.random() < 0.06:
                    case_status, case_outcome = "Dropped", "Dropped"
                else:
                    case_status = {
                        "Intake": "Active - Intake",
                        "Retainer Signed": "Active - Signed",
                        "Records Requested": "Pending Records",
                        "Records Received": "In Workup",
                        "Workup Complete": "In Workup",
                        "Demand Sent": "In Negotiation",
                        "Negotiation": "In Negotiation",
                    }[current_stage]
                    case_outcome = "In Progress"

            date_opened = intake + timedelta(int(rng.integers(0, 6)))
            if case_status in ("Settled", "Closed-Lost", "Dropped"):
                date_closed = date_opened + timedelta(case_age)
                date_closed = min(date_closed, SNAPSHOT_DATE)
            else:
                date_closed = pd.NaT

            settlement_amount = np.nan
            if settled:
                settlement_amount = round(
                    float(base_settle * np.clip(rng.lognormal(0.0, 0.55), 0.2, 4.5)), 2
                )

            # Date the matter actually reached "Workup Complete" (only for
            # completed matters). Anchored to INTAKE plus a realistic workup lag
            # (slower when documents are missing or records aren't in yet) rather
            # than to the case's current age -- this spreads completion dates
            # smoothly instead of piling them at the snapshot. Deterministic (no
            # RNG) so every other column stays byte-for-byte reproducible. This
            # is the correct index for a "completed workups per month" forecast.
            workup_lag = (45
                          + 12 * missing_documents
                          + (0 if medical_records_received else 25)
                          + (communication_count % 15))
            if workup_completed and workup_lag <= case_age:
                # Enough time has actually elapsed for the workup to have finished
                # -> we observe a completion date (always <= snapshot).
                workup_completed_date = date_opened + timedelta(int(workup_lag))
            else:
                # Either not completed, or completed-flag set but too recently
                # opened to have finished by the snapshot (right-censored): the
                # completion is not yet observed, so no date.
                workup_completed_date = pd.NaT

            # last_activity_date powers the "inactive > 30 days" KPI.
            last_activity = SNAPSHOT_DATE - timedelta(int(np.clip(rng.exponential(18), 0, 160)))
            if not pd.isna(date_closed):
                last_activity = min(last_activity, date_closed)

            rows.append(
                {
                    "case_id": f"CASE-{case_counter:06d}",
                    "client_id": client["client_id"],
                    "case_type": case_type,
                    "state": client["state"],
                    "intake_date": intake,
                    "date_opened": date_opened,
                    "date_closed": date_closed,
                    "case_status": case_status,
                    "current_stage": current_stage,
                    "stage_index": stage_idx,
                    "assigned_case_manager": cm_id,
                    "attorney_id": attorney_id,
                    "days_in_stage": days_in_stage,
                    "case_age_days": case_age,
                    "medical_records_received": medical_records_received,
                    "missing_documents": missing_documents,
                    "communication_count": communication_count,
                    "workup_completed": workup_completed,
                    "case_outcome": case_outcome,
                    "settlement_amount": settlement_amount,
                    "workup_completed_date": workup_completed_date,
                    "last_activity_date": last_activity,
                }
            )
            case_counter += 1
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Fact: child tables keyed off cases
# --------------------------------------------------------------------------- #
def build_activities(cases: pd.DataFrame) -> pd.DataFrame:
    activity_types = [
        "Phone Call", "Email", "Document Request", "Medical Record Review",
        "Client Meeting", "Demand Drafting", "Status Update", "Negotiation Call",
        "Internal Note", "SMS",
    ]
    rows = []
    aid = 1
    for _, c in cases.iterrows():
        n = max(1, int(c["communication_count"] * rng.uniform(0.5, 1.0)))
        for _ in range(n):
            offset = int(rng.integers(0, max(c["case_age_days"], 1) + 1))
            adate = c["date_opened"] + timedelta(offset)
            if adate > SNAPSHOT_DATE:
                adate = SNAPSHOT_DATE
            rows.append(
                {
                    "activity_id": f"ACT-{aid:07d}",
                    "case_id": c["case_id"],
                    "case_manager_id": c["assigned_case_manager"],
                    "activity_type": rng.choice(activity_types),
                    "activity_date": adate,
                    "duration_minutes": int(np.clip(rng.normal(18, 10), 1, 120)),
                }
            )
            aid += 1
    return pd.DataFrame(rows)


def build_documents(cases: pd.DataFrame) -> pd.DataFrame:
    doc_types = [
        "Retainer Agreement", "HIPAA Authorization", "Police Report",
        "Medical Bill", "Wage Loss Statement", "Insurance Declaration",
        "Photo Evidence", "Witness Statement", "Demand Letter",
    ]
    rows = []
    did = 1
    for _, c in cases.iterrows():
        n_docs = int(rng.integers(3, 9))
        n_missing = min(int(c["missing_documents"]), n_docs)
        statuses = ["Received"] * (n_docs - n_missing) + ["Missing"] * n_missing
        rng.shuffle(statuses)
        for status in statuses:
            requested = c["date_opened"] + timedelta(int(rng.integers(0, 30)))
            received = (
                requested + timedelta(int(rng.integers(2, 45)))
                if status == "Received"
                else pd.NaT
            )
            if not pd.isna(received) and received > SNAPSHOT_DATE:
                received = pd.NaT
                status = "Pending"
            rows.append(
                {
                    "document_id": f"DOC-{did:07d}",
                    "case_id": c["case_id"],
                    "document_type": rng.choice(doc_types),
                    "status": status,
                    "requested_date": requested,
                    "received_date": received,
                }
            )
            did += 1
    return pd.DataFrame(rows)


def build_medical_records(cases: pd.DataFrame) -> pd.DataFrame:
    providers = [
        "St. Mary's Hospital", "Regional Medical Center", "OrthoCare Clinic",
        "City Imaging Associates", "Premier Physical Therapy",
        "Neurology Partners", "Urgent Care Express", "Spine & Pain Institute",
    ]
    rows = []
    rid = 1
    for _, c in cases.iterrows():
        if c["medical_records_received"] == 0 and rng.random() < 0.5:
            continue  # some cases simply have no records yet
        n = int(rng.integers(1, 5))
        for _ in range(n):
            requested = c["date_opened"] + timedelta(int(rng.integers(5, 40)))
            if c["medical_records_received"] == 1 and rng.random() < 0.85:
                received = requested + timedelta(int(rng.integers(10, 60)))
                status = "Received"
                pages = int(np.clip(rng.normal(85, 60), 1, 600))
            else:
                received, status, pages = pd.NaT, "Outstanding", 0
            if not pd.isna(received) and received > SNAPSHOT_DATE:
                received, status, pages = pd.NaT, "Outstanding", 0
            rows.append(
                {
                    "record_id": f"MR-{rid:07d}",
                    "case_id": c["case_id"],
                    "provider_name": rng.choice(providers),
                    "requested_date": requested,
                    "received_date": received,
                    "status": status,
                    "num_pages": pages,
                }
            )
            rid += 1
    return pd.DataFrame(rows)


def build_settlements(cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sid = 1
    settled = cases[cases["case_status"] == "Settled"]
    for _, c in settled.iterrows():
        gross = float(c["settlement_amount"])
        attorney_fee = round(gross * rng.choice([0.33, 0.40]), 2)
        liens = round(gross * rng.uniform(0.05, 0.25), 2)
        costs = round(gross * rng.uniform(0.02, 0.08), 2)
        net = round(gross - attorney_fee - liens - costs, 2)
        sdate = c["date_closed"] if not pd.isna(c["date_closed"]) else SNAPSHOT_DATE
        rows.append(
            {
                "settlement_id": f"SET-{sid:06d}",
                "case_id": c["case_id"],
                "settlement_amount": gross,
                "settlement_date": sdate,
                "attorney_fee": attorney_fee,
                "lien_amount": liens,
                "case_costs": costs,
                "net_to_client": net,
            }
        )
        sid += 1
    return pd.DataFrame(rows)


def build_call_logs(cases: pd.DataFrame) -> pd.DataFrame:
    outcomes = ["Connected", "Voicemail", "No Answer", "Callback Requested", "Wrong Number"]
    rows = []
    cid = 1
    for _, c in cases.iterrows():
        n = int(np.clip(rng.poisson(c["communication_count"] * 0.6), 0, 50))
        for _ in range(n):
            offset = int(rng.integers(0, max(c["case_age_days"], 1) + 1))
            cdate = c["date_opened"] + timedelta(offset)
            if cdate > SNAPSHOT_DATE:
                cdate = SNAPSHOT_DATE
            rows.append(
                {
                    "call_id": f"CALL-{cid:07d}",
                    "case_id": c["case_id"],
                    "client_id": c["client_id"],
                    "case_manager_id": c["assigned_case_manager"],
                    "call_date": cdate,
                    "direction": rng.choice(["Inbound", "Outbound"], p=[0.4, 0.6]),
                    "duration_seconds": int(np.clip(rng.exponential(150), 0, 1800)),
                    "outcome": rng.choice(outcomes, p=[0.45, 0.25, 0.15, 0.10, 0.05]),
                }
            )
            cid += 1
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Intentional data-quality issues (so the DQ layer has work to do)
# --------------------------------------------------------------------------- #
def inject_data_quality_issues(clients: pd.DataFrame,
                               cases: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    clients = clients.copy()
    cases = cases.copy()

    # 1) Duplicate clients: clone ~40 clients under new IDs, same name+DOB.
    dup_src = clients.sample(min(40, len(clients)), random_state=SEED).copy()
    start_id = N_CLIENTS + 1
    dup_src["client_id"] = [f"CL-{start_id + i:05d}" for i in range(len(dup_src))]
    dup_src["email"] = dup_src["email"].str.replace("@", "+dup@", regex=False)
    clients = pd.concat([clients, dup_src], ignore_index=True)

    # 2) Missing emails (~3%) and missing referral sources (~2%).
    miss_email = clients.sample(frac=0.03, random_state=1).index
    clients.loc[miss_email, "email"] = np.nan
    miss_ref = clients.sample(frac=0.02, random_state=2).index
    clients.loc[miss_ref, "referral_source"] = np.nan

    # 3) A handful of logically impossible settlement amounts (negative).
    settled_idx = cases[cases["settlement_amount"].notna()]
    bad = settled_idx.sample(min(8, len(settled_idx)), random_state=3).index
    cases.loc[bad, "settlement_amount"] = cases.loc[bad, "settlement_amount"] * -1

    # 4) A few negative days_in_stage values (sensor/entry error).
    bad2 = cases.sample(min(10, len(cases)), random_state=4).index
    cases.loc[bad2, "days_in_stage"] = -cases.loc[bad2, "days_in_stage"]

    return clients, cases


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Generating synthetic legal case-management data ...")

    attorneys = build_attorneys()
    managers = build_case_managers()
    clients = build_clients()
    cases = build_cases(clients, attorneys, managers)

    activities = build_activities(cases)
    documents = build_documents(cases)
    medical_records = build_medical_records(cases)
    settlements = build_settlements(cases)
    call_logs = build_call_logs(cases)

    clients, cases = inject_data_quality_issues(clients, cases)

    # Drop internal helper columns before export.
    managers_out = managers.drop(columns=["_effectiveness"])
    cases_out = cases.drop(columns=["stage_index", "case_age_days"])

    tables = {
        "clients": clients,
        "attorneys": attorneys,
        "case_managers": managers_out,
        "cases": cases_out,
        "activities": activities,
        "documents": documents,
        "medical_records": medical_records,
        "settlements": settlements,
        "call_logs": call_logs,
    }

    for name, df in tables.items():
        path = os.path.join(DATA_DIR, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  {name:18s} -> {len(df):>7,} rows  ({path})")

    print("\nDone. Snapshot date:", SNAPSHOT_DATE)


if __name__ == "__main__":
    main()
