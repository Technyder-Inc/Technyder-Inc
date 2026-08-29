from __future__ import annotations

import base64
import gzip
import json
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def _compact_xgb(model):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = Path(tmp.name)

    try:
        model.save_model(path)
        payload = json.loads(path.read_text())
    finally:
        path.unlink(missing_ok=True)

    learner = payload["learner"]
    base_score = learner["learner_model_param"]["base_score"]
    if isinstance(base_score, str) and base_score.startswith("["):
        base_score = float(base_score.strip("[]"))
    else:
        base_score = float(base_score)

    trees = []
    for tree in learner["gradient_booster"]["model"]["trees"]:
        trees.append(
            [
                tree["left_children"],
                tree["right_children"],
                tree["split_indices"],
                tree["split_conditions"],
                tree["base_weights"],
            ]
        )

    return [base_score, trees]


def _calibrated_probability(bundle, matrix):
    raw = bundle["model"].predict_proba(matrix)[:, 1]
    raw = np.clip(raw, 1e-6, 1 - 1e-6)
    margin = np.log(raw / (1 - raw)).reshape(-1, 1)
    return bundle["calibrator"].predict_proba(margin)[:, 1]


def export_portable_runtime(data_path: Path, artifact_dir: Path) -> Path:
    bundle = joblib.load(artifact_dir / "retention_model.joblib")
    df = pd.read_csv(data_path, parse_dates=["snapshot_month"])

    preprocessor = bundle["preprocessor"]
    categorical = list(preprocessor.transformers_[0][2])
    numeric = list(preprocessor.transformers_[1][2])
    features = categorical + numeric

    encoder = preprocessor.named_transformers_["cat"]
    scaler = preprocessor.named_transformers_["num"]

    train = df[df.snapshot_month < "2026-01-01"].copy()
    test = df[df.snapshot_month >= "2026-04-01"].copy()

    baseline = {}
    for column in categorical:
        baseline[column] = str(train[column].mode().iloc[0])
    for column in numeric:
        baseline[column] = float(train[column].mean())

    x_test = preprocessor.transform(test[features])
    churn_probability = _calibrated_probability(bundle, x_test)
    control = bundle["uplift_control"].predict_proba(x_test)[:, 1]
    treated = bundle["uplift_treated"].predict_proba(x_test)[:, 1]
    uplift = np.clip(control - treated, -0.5, 0.5)

    annual_revenue = test["monthly_revenue"].to_numpy() * 12
    expected_value = uplift * annual_revenue * 0.72 - 45
    priority = np.maximum(expected_value, 0) * churn_probability

    selected = test.assign(_priority=priority).sort_values(
        "_priority", ascending=False
    ).head(25)

    portfolio_rows = []
    for _, row in selected.iterrows():
        item = {"customer_id": str(row["customer_id"])}
        for column in features:
            value = row[column]
            if isinstance(value, (np.integer,)):
                value = int(value)
            elif isinstance(value, (np.floating,)):
                value = float(value)
            else:
                value = str(value)
            item[column] = value
        portfolio_rows.append(item)

    model_card = json.loads((artifact_dir / "model_card.json").read_text())
    model_card["deployment_runtime"] = "Portable pure-Python XGBoost tree evaluator"

    payload = {
        "categorical": categorical,
        "categories": [[str(v) for v in values] for values in encoder.categories_],
        "numeric": numeric,
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "feature_names": bundle["feature_names"],
        "churn": _compact_xgb(bundle["model"]),
        "calibration": [
            float(bundle["calibrator"].coef_[0][0]),
            float(bundle["calibrator"].intercept_[0]),
        ],
        "uplift_control": _compact_xgb(bundle["uplift_control"]),
        "uplift_treated": _compact_xgb(bundle["uplift_treated"]),
        "threshold": float(bundle["threshold"]),
        "version": bundle["model_version"],
        "baseline": baseline,
        "model_card": model_card,
        "feature_importance": json.loads(
            (artifact_dir / "feature_importance.json").read_text()
        ),
        "drift": json.loads((artifact_dir / "drift_report.json").read_text()),
        "portfolio_rows": portfolio_rows,
    }

    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded = base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii")

    target = artifact_dir / "runtime_model.b64"
    target.write_text(encoded)
    return target
