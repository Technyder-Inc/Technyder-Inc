from __future__ import annotations

import base64
import gzip
import json
import math
import struct
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from employee_attrition import router as employee_router

ROOT = Path(__file__).resolve().parent


@lru_cache
def runtime():
    raw = base64.b64decode((ROOT / "artifacts" / "runtime_model.b64").read_text().strip())
    return json.loads(gzip.decompress(raw).decode("utf-8"))


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def logistic(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def preprocess(row: dict, rt: dict) -> list[float]:
    out = []
    for col, categories in zip(rt["categorical"], rt["categories"]):
        value = str(row[col])
        out.extend(1.0 if value == category else 0.0 for category in categories)

    for col, mean, scale in zip(rt["numeric"], rt["mean"], rt["scale"]):
        out.append((float(row[col]) - float(mean)) / float(scale))
    return out


def booster_probability(model, vector: list[float]) -> float:
    base_score, trees = model
    margin = math.log(base_score / (1.0 - base_score))

    for left, right, feature, split, weight in trees:
        node = 0
        while left[node] != -1:
            value = f32(vector[feature[node]])
            threshold = f32(split[node])
            node = left[node] if value < threshold else right[node]
        margin += weight[node]

    return logistic(margin)


def churn_probability(row: dict, rt: dict) -> float:
    x = preprocess(row, rt)
    raw = booster_probability(rt["churn"], x)
    clipped = min(max(raw, 1e-6), 1 - 1e-6)
    margin = math.log(clipped / (1 - clipped))
    coef, intercept = rt["calibration"]
    return logistic(coef * margin + intercept)


def local_drivers(row: dict, rt: dict, full_probability: float, limit: int = 5):
    drivers = []

    for feature in rt["categorical"] + rt["numeric"]:
        baseline_value = rt["baseline"][feature]

        if str(row[feature]) == str(baseline_value):
            delta = 0.0
        else:
            counterfactual = dict(row)
            counterfactual[feature] = baseline_value
            baseline_probability = churn_probability(counterfactual, rt)
            delta = full_probability - baseline_probability

        drivers.append(
            {
                "feature": feature,
                "direction": (
                    "raises risk"
                    if delta > 0
                    else "reduces risk"
                    if delta < 0
                    else "neutral"
                ),
                "impact": delta,
            }
        )

    return sorted(drivers, key=lambda item: abs(item["impact"]), reverse=True)[:limit]


def score_row(row: dict, explain: bool = True) -> dict:
    rt = runtime()
    x = preprocess(row, rt)

    raw = booster_probability(rt["churn"], x)
    clipped = min(max(raw, 1e-6), 1 - 1e-6)
    coef, intercept = rt["calibration"]
    risk = logistic(coef * math.log(clipped / (1 - clipped)) + intercept)

    control = booster_probability(rt["uplift_control"], x)
    treated = booster_probability(rt["uplift_treated"], x)
    uplift = max(-0.5, min(0.5, control - treated))

    annual_revenue = float(row["monthly_revenue"]) * 12.0
    revenue_at_risk = risk * annual_revenue
    expected_value = uplift * annual_revenue * 0.72 - 45.0

    threshold = float(rt["threshold"])
    risk_band = (
        "Critical"
        if risk >= 0.65
        else "High"
        if risk >= threshold
        else "Medium"
        if risk >= 0.25
        else "Low"
    )

    result = {
        "churn_probability": risk,
        "risk_band": risk_band,
        "decision_threshold": threshold,
        "annual_revenue_at_risk": revenue_at_risk,
        "estimated_uplift": uplift,
        "expected_retention_value": expected_value,
        "recommended_action": bool(expected_value > 0 and uplift > 0),
        "model_version": rt["version"],
    }

    if explain:
        result["top_drivers"] = local_drivers(row, rt, risk)

    return result


class CustomerSnapshot(BaseModel):
    plan_tier: Literal["Starter", "Growth", "Scale", "Enterprise"] = "Growth"
    region: Literal["North America", "Europe", "APAC", "LATAM"] = "North America"
    acquisition_channel: Literal[
        "Organic", "Partner", "Paid", "Outbound", "Referral"
    ] = "Organic"

    tenure_months: int = Field(18, ge=1, le=120)
    seats: int = Field(22, ge=1, le=1000)
    monthly_revenue: float = Field(1800, ge=0)
    usage_30d: float = Field(48, ge=0, le=100)
    usage_change_90d: float = Field(-22, ge=-100, le=100)
    support_tickets_90d: int = Field(4, ge=0)
    nps: int = Field(5, ge=-100, le=100)
    payment_failures_90d: int = Field(1, ge=0)
    days_since_login: int = Field(17, ge=0)
    feature_adoption: float = Field(0.42, ge=0, le=1)
    integrations_count: int = Field(2, ge=0)
    admin_logins_30d: int = Field(4, ge=0)
    renewal_due_60d: int = Field(1, ge=0, le=1)
    contract_months_left: int = Field(1, ge=0)
    price_increase_90d: int = Field(1, ge=0, le=1)


app = FastAPI(
    title="Technyder Retention Intelligence API",
    version="1.1.0",
    description=(
        "Portable churn, revenue-at-risk and uplift scoring demo "
        "using synthetic B2B SaaS data."
    ),
)

app.include_router(employee_router)


DASHBOARD = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Retention Intelligence — Technyder</title>
<style>
body{margin:0;background:#f6f7f9;color:#111827;font-family:Inter,Arial,sans-serif}
.w{max-width:1100px;margin:auto;padding:42px 20px}
.k{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:#667085;font-weight:700}
h1{font-size:42px;max-width:760px;margin:8px 0}
.sub{color:#667085;max-width:800px;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}
.card{background:white;border:1px solid #e5e7eb;border-radius:16px;padding:18px}
.m{font-size:28px;font-weight:800}
.lab{font-size:12px;color:#667085}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.arch{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
.arch div{padding:12px;border:1px solid #e5e7eb;border-radius:10px;text-align:center;font-size:12px;background:#fafafa}
a{color:#111827;font-weight:700}
@media(max-width:850px){.grid{grid-template-columns:1fr 1fr}.two{grid-template-columns:1fr}.arch{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="w">
<div class="k">Technyder / ML Portfolio</div>
<h1>Customer Retention Intelligence</h1><p><a href="/employees">Employee Attrition Analyzer →</a></p>
<div class="sub">
Predict 60-day churn, explain account risk, quantify recurring revenue exposure,
and prioritize retention actions by expected financial value.
</div>

<div class="grid">
<div class="card"><div class="lab">ROC-AUC</div><div class="m" id="a">—</div></div>
<div class="card"><div class="lab">PR-AUC</div><div class="m" id="p">—</div></div>
<div class="card"><div class="lab">Revenue at risk</div><div class="m" id="r">—</div></div>
<div class="card"><div class="lab">Actionable accounts</div><div class="m" id="x">—</div></div>
</div>

<div class="card">
<div class="lab">Decision architecture</div>
<h2>Prediction is separated from action.</h2>
<div class="arch">
<div>Customer signals</div>
<div>Calibrated XGBoost</div>
<div>Local drivers</div>
<div>T-learner uplift</div>
<div>Economic priority</div>
</div>
</div>

<div class="two" style="margin-top:16px">
<div class="card">
<h2>Business output</h2>
<p>Who is likely to churn? Why? How much ARR is exposed? Which accounts are worth targeting?</p>
<p><a href="/docs">Open interactive API docs →</a></p>
</div>
<div class="card">
<h2>Deployment profile</h2>
<p>
The full training stack stays in GitHub. Production inference uses a portable
pure-Python tree evaluator, keeping the serverless bundle small while preserving
XGBoost predictions.
</p>
</div>
</div>

<p style="font-size:11px;color:#98a2b3">
All data is synthetic. Explanations are model-based associations; uplift requires
causally credible treatment history in production.
</p>
</div>

<script>
const money=n=>new Intl.NumberFormat('en-US',{
style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:1
}).format(n);

fetch('/api/model-card')
.then(r=>r.json())
.then(c=>{
a.textContent=c.test_metrics.roc_auc.toFixed(3);
p.textContent=c.test_metrics.pr_auc.toFixed(3);
r.textContent=money(c.portfolio.test_revenue_at_risk);
x.textContent=c.portfolio.high_value_actionable_accounts.toLocaleString();
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return DASHBOARD


@app.get("/health")
def health():
    rt = runtime()
    return {
        "status": "ok",
        "model": "retention-intelligence",
        "version": rt["version"],
        "runtime": "portable-pure-python",
    }


@app.get("/api/model-card")
def model_card():
    return runtime()["model_card"]


@app.get("/api/feature-importance")
def feature_importance():
    return runtime()["feature_importance"]


@app.get("/api/drift")
def drift():
    return runtime()["drift"]


@app.get("/api/portfolio")
def portfolio(limit: int = 20):
    rows = runtime()["portfolio_rows"][: max(1, min(limit, 25))]
    result = []

    for row in rows:
        score = score_row(row, explain=False)
        result.append(
            {
                "customer_id": row["customer_id"],
                "plan_tier": row["plan_tier"],
                "monthly_revenue": row["monthly_revenue"],
                **score,
            }
        )

    return result


@app.post("/api/score")
def score_one(snapshot: CustomerSnapshot):
    return score_row(snapshot.model_dump())


@app.post("/api/batch-score")
def batch_score(snapshots: list[CustomerSnapshot]):
    if len(snapshots) > 250:
        return {"error": "Demo endpoint is limited to 250 rows."}

    return {
        "count": len(snapshots),
        "predictions": [
            score_row(snapshot.model_dump(), explain=False)
            for snapshot in snapshots
        ],
    }
