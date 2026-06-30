"""
04_predictive_model.py
================================================================================
Predicts whether a client/matter will COMPLETE CASE WORKUP, so operations can
prioritize at-risk matters early.

Target:   workup_completed (1/0)

Leakage discipline (important)
------------------------------
`workup_completed` is *defined* from the funnel stage, so any field that encodes
progression downstream of workup is a leak and is EXCLUDED from features:
    current_stage, case_status, case_outcome, settlement_amount,
    date_closed, days_to_close, is_open, workup_completed_date
We ALSO exclude `days_in_stage`: in the synthetic generator it is derived from
the stage index, which is itself conditional on the target, so it leaks the
outcome (flagged by methodology review). We train only on attributes knowable
at/near intake & early workup:
    case_type, state, referral_source, marketing_channel,
    communication_count, medical_records_received, missing_documents,
    attorney experience, assigned case manager & team, intake month.

Models:   Logistic Regression (interpretable baseline) and Random Forest.
Eval:     stratified train/test split; Accuracy, Precision, Recall, ROC-AUC,
          confusion matrix; ROC curve + feature importance figures.
Output:   python/outputs/predictions.csv (test-set probabilities),
          model_metrics.txt, roc_curve.png, feature_importance.png

Run (after 01_data_cleaning.py):  python 04_predictive_model.py
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_score,
                             recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = os.path.dirname(__file__)
PROC = os.path.join(HERE, "..", "data", "processed")
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
RANDOM_STATE = 42

# Fields that leak the target - never used as features.
# days_in_stage is excluded too: it is generated from the stage index, which is
# conditional on the target (methodology-review finding C1) -> it leaks.
LEAK_COLS = ["current_stage", "case_status", "case_outcome", "settlement_amount",
             "date_closed", "days_to_close", "is_open", "workup_completed",
             "workup_completed_date", "days_in_stage",
             # case_age_days embeds date_closed -> would leak if ever promoted.
             "case_age_days"]

NUMERIC = ["communication_count", "medical_records_received", "missing_documents",
           "attorney_years_experience"]
CATEGORICAL = ["case_type", "state", "referral_source", "marketing_channel",
               "team", "intake_month_num"]

_report: list[str] = []


def log(m: str) -> None:
    print(m); _report.append(m)


def build_features() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    cases = pd.read_csv(os.path.join(PROC, "cases_clean.csv"),
                        parse_dates=["intake_date", "date_opened"])
    clients = pd.read_csv(os.path.join(PROC, "clients_clean.csv"))
    attorneys = pd.read_csv(os.path.join(HERE, "..", "data", "attorneys.csv"))
    managers = pd.read_csv(os.path.join(HERE, "..", "data", "case_managers.csv"))

    df = (cases
          .merge(clients[["client_id", "referral_source", "marketing_channel"]],
                 on="client_id", how="left")
          .merge(attorneys[["attorney_id", "years_experience"]]
                 .rename(columns={"years_experience": "attorney_years_experience"}),
                 on="attorney_id", how="left")
          .merge(managers[["case_manager_id", "team"]]
                 .rename(columns={"case_manager_id": "assigned_case_manager"}),
                 on="assigned_case_manager", how="left"))

    df["intake_month_num"] = df["intake_date"].dt.month.astype(str)
    df["referral_source"] = df["referral_source"].fillna("Unknown")

    y = df["workup_completed"].astype(int)
    X = df[NUMERIC + CATEGORICAL].copy()
    # NOTE: imputation is NOT done here. It lives inside the pipeline so it is
    # fit on training folds only (no train/test contamination) - review fix M1.
    return X, y, df["case_id"]


def make_pipeline(estimator) -> Pipeline:
    # Imputers are inside the ColumnTransformer so every preprocessing step is
    # fit on the training fold only (no leakage from the test set).
    num_pipe = Pipeline([("impute", SimpleImputer(strategy="median")),
                         ("scale", StandardScaler())])
    cat_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                         ("ohe", OneHotEncoder(handle_unknown="ignore"))])
    pre = ColumnTransformer([
        ("num", num_pipe, NUMERIC),
        ("cat", cat_pipe, CATEGORICAL),
    ])
    return Pipeline([("pre", pre), ("model", estimator)])


def evaluate(name, pipe, Xte, yte) -> tuple[dict, np.ndarray]:
    proba = pipe.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    m = {
        "model": name,
        "accuracy": accuracy_score(yte, pred),
        "precision": precision_score(yte, pred),
        "recall": recall_score(yte, pred),
        "roc_auc": roc_auc_score(yte, proba),
    }
    log(f"\n{name}")
    log(f"  Accuracy : {m['accuracy']:.3f}")
    log(f"  Precision: {m['precision']:.3f}")
    log(f"  Recall   : {m['recall']:.3f}")
    log(f"  ROC-AUC  : {m['roc_auc']:.3f}")
    cm = confusion_matrix(yte, pred)
    log(f"  Confusion matrix [ [TN FP] [FN TP] ]: {cm.tolist()}")
    return m, proba


def main() -> None:
    log("=" * 70)
    log("PREDICTIVE MODEL - Will the matter complete workup?")
    log("=" * 70)

    X, y, case_ids = build_features()
    log(f"\nSamples: {len(X):,} | Positive rate (completed): {y.mean():.3f}")
    log(f"Features: {len(NUMERIC)} numeric + {len(CATEGORICAL)} categorical")
    log(f"Excluded leakage columns: {', '.join(LEAK_COLS)}")

    Xtr, Xte, ytr, yte, _, ids_te = train_test_split(
        X, y, case_ids, test_size=0.25, stratify=y, random_state=RANDOM_STATE)
    log(f"Train: {len(Xtr):,} | Test: {len(Xte):,} (stratified 75/25)")

    # ---- 5-fold stratified CV on the TRAIN set (review fix M2) ---- #
    # Reports mean +/- std ROC-AUC so the single-split number has context.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    log("\n5-fold stratified CV ROC-AUC (train set):")
    for name, est in [
        ("Logistic Regression", LogisticRegression(max_iter=1000, C=1.0)),
        ("Random Forest", RandomForestClassifier(
            n_estimators=300, max_depth=12, min_samples_leaf=5,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)),
    ]:
        scores = cross_val_score(make_pipeline(est), Xtr, ytr,
                                 cv=cv, scoring="roc_auc", n_jobs=-1)
        log(f"  {name:22s} AUC = {scores.mean():.3f} +/- {scores.std():.3f}")

    # ---- Model 1: Logistic Regression ---- #
    logit = make_pipeline(LogisticRegression(max_iter=1000, C=1.0))
    logit.fit(Xtr, ytr)
    m_logit, p_logit = evaluate("Logistic Regression", logit, Xte, yte)

    # ---- Model 2: Random Forest ---- #
    rf = make_pipeline(RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=5,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1))
    rf.fit(Xtr, ytr)
    m_rf, p_rf = evaluate("Random Forest", rf, Xte, yte)

    # ---- Pick the better model by ROC-AUC for export ---- #
    best_name, best_pipe, best_proba = max(
        [("Logistic Regression", logit, p_logit),
         ("Random Forest", rf, p_rf)],
        key=lambda x: roc_auc_score(yte, x[2]))
    log(f"\nSelected model (by ROC-AUC): {best_name}")

    # ---- ROC curve figure ---- #
    fig, ax = plt.subplots(figsize=(6, 6))
    for name, proba in [("Logistic Regression", p_logit), ("Random Forest", p_rf)]:
        fpr, tpr, _ = roc_curve(yte, proba)
        ax.plot(fpr, tpr, lw=2, label=f"{name} (AUC={roc_auc_score(yte, proba):.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC - Workup Completion Classifier"); ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.savefig(os.path.join(OUT, "roc_curve.png"), bbox_inches="tight", dpi=110)
    plt.close(fig)

    # ---- Feature importance (from Random Forest) ---- #
    pre = rf.named_steps["pre"]
    ohe = pre.named_transformers_["cat"]
    feat_names = NUMERIC + list(ohe.get_feature_names_out(CATEGORICAL))
    importances = rf.named_steps["model"].feature_importances_
    fi = (pd.Series(importances, index=feat_names)
          .sort_values(ascending=False).head(15))
    log("\nTop feature importances (Random Forest):")
    for f, v in fi.items():
        log(f"  {f:38s} {v:.4f}")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(fi.index[::-1], fi.values[::-1], color="#2a9d8f")
    ax.set_title("Top 15 Feature Importances - Workup Completion")
    ax.set_xlabel("Importance")
    fig.savefig(os.path.join(OUT, "feature_importance.png"),
                bbox_inches="tight", dpi=110)
    plt.close(fig)

    # ---- Export predictions ---- #
    preds = pd.DataFrame({
        "case_id": ids_te.values,
        "actual_workup_completed": yte.values,
        "predicted_proba": best_proba.round(4),
        "predicted_label": (best_proba >= 0.5).astype(int),
        "risk_flag": np.where(best_proba < 0.5, "AT RISK", "on track"),
    }).sort_values("predicted_proba")
    preds.to_csv(os.path.join(OUT, "predictions.csv"), index=False)
    log(f"\nExported {len(preds):,} test-set predictions -> {OUT}/predictions.csv")
    log(f"  At-risk matters flagged: {(preds['risk_flag']=='AT RISK').sum():,}")

    # ---- Metrics summary table ---- #
    pd.DataFrame([m_logit, m_rf]).round(3).to_csv(
        os.path.join(OUT, "model_metrics.csv"), index=False)
    with open(os.path.join(OUT, "model_metrics.txt"), "w") as f:
        f.write("\n".join(_report))
    log(f"Saved metrics + figures to {OUT}/")


if __name__ == "__main__":
    main()
