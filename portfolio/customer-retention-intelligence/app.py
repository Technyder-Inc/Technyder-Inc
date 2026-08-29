from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Literal
import joblib,numpy as np,pandas as pd,xgboost as xgb
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field

ROOT=Path(__file__).resolve().parent;ART=ROOT/"artifacts"
app=FastAPI(title="Technyder Retention Intelligence API",version="1.0.0",description="Churn, revenue-at-risk and uplift scoring demo using synthetic B2B SaaS data.")

class CustomerSnapshot(BaseModel):
    plan_tier:Literal["Starter","Growth","Scale","Enterprise"]="Growth"
    region:Literal["North America","Europe","APAC","LATAM"]="North America"
    acquisition_channel:Literal["Organic","Partner","Paid","Outbound","Referral"]="Organic"
    tenure_months:int=Field(18,ge=1,le=120);seats:int=Field(22,ge=1,le=1000);monthly_revenue:float=Field(1800,ge=0)
    usage_30d:float=Field(48,ge=0,le=100);usage_change_90d:float=Field(-22,ge=-100,le=100);support_tickets_90d:int=Field(4,ge=0)
    nps:int=Field(5,ge=-100,le=100);payment_failures_90d:int=Field(1,ge=0);days_since_login:int=Field(17,ge=0)
    feature_adoption:float=Field(.42,ge=0,le=1);integrations_count:int=Field(2,ge=0);admin_logins_30d:int=Field(4,ge=0)
    renewal_due_60d:int=Field(1,ge=0,le=1);contract_months_left:int=Field(1,ge=0);price_increase_90d:int=Field(1,ge=0,le=1)

@lru_cache
def bundle(): return joblib.load(ART/"retention_model.joblib")
@lru_cache
def load(name): return json.loads((ART/name).read_text())
def logit(p):
    p=np.clip(p,1e-6,1-1e-6);return np.log(p/(1-p)).reshape(-1,1)
def score(frame):
    b=bundle();x=b["preprocessor"].transform(frame[b["features"]]);raw=b["model"].predict_proba(x)[:,1];p=b["calibrator"].predict_proba(logit(raw))[:,1]
    up=np.clip(b["uplift_control"].predict_proba(x)[:,1]-b["uplift_treated"].predict_proba(x)[:,1],-.5,.5)
    contrib=b["model"].get_booster().predict(xgb.DMatrix(x),pred_contribs=True)[:,:-1];out=[]
    for i,row in frame.reset_index(drop=True).iterrows():
        risk=float(p[i]);arr=float(row.monthly_revenue*12);rar=risk*arr;ev=float(up[i]*arr*.72-45)
        idx=np.argsort(np.abs(contrib[i]))[::-1][:5];drivers=[{"feature":b["feature_names"][j],"direction":"raises risk" if contrib[i,j]>0 else "reduces risk","impact":float(contrib[i,j])} for j in idx]
        band="Critical" if risk>=.65 else "High" if risk>=b["threshold"] else "Medium" if risk>=.25 else "Low"
        out.append({"churn_probability":risk,"risk_band":band,"decision_threshold":b["threshold"],"annual_revenue_at_risk":rar,"estimated_uplift":float(up[i]),"expected_retention_value":ev,"recommended_action":bool(ev>0 and up[i]>0),"top_drivers":drivers,"model_version":b["model_version"]})
    return out

@app.get("/")
def home(): return FileResponse(ROOT/"public"/"index.html")
@app.get("/health")
def health(): bundle();return {"status":"ok","model":"retention-intelligence","version":"1.0.0"}
@app.get("/api/model-card")
def card(): return load("model_card.json")
@app.get("/api/feature-importance")
def importance(): return load("feature_importance.json")
@app.get("/api/drift")
def drift(): return load("drift_report.json")
@app.get("/api/portfolio")
def portfolio(limit:int=20): return load("portfolio_sample.json")[:max(1,min(limit,40))]
@app.post("/api/score")
def score_one(snapshot:CustomerSnapshot): return score(pd.DataFrame([snapshot.model_dump()]))[0]
@app.post("/api/batch-score")
def batch(snapshots:list[CustomerSnapshot]):
    if len(snapshots)>500:return {"error":"Demo endpoint is limited to 500 rows."}
    return {"count":len(snapshots),"predictions":score(pd.DataFrame([s.model_dump() for s in snapshots]))}
