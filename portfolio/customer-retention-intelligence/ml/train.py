from __future__ import annotations
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,brier_score_loss,confusion_matrix,f1_score,precision_score,recall_score,roc_auc_score
from sklearn.preprocessing import OneHotEncoder,StandardScaler

CATEGORICAL=["plan_tier","region","acquisition_channel"]
NUMERIC=["tenure_months","seats","monthly_revenue","usage_30d","usage_change_90d","support_tickets_90d","nps","payment_failures_90d","days_since_login","feature_adoption","integrations_count","admin_logins_30d","renewal_due_60d","contract_months_left","price_increase_90d"]
FEATURES=CATEGORICAL+NUMERIC

def _logit(p):
    p=np.clip(p,1e-6,1-1e-6)
    return np.log(p/(1-p)).reshape(-1,1)

def _metrics(y,p,t):
    pred=(p>=t).astype(int);tn,fp,fn,tp=confusion_matrix(y,pred).ravel()
    return {"roc_auc":float(roc_auc_score(y,p)),"pr_auc":float(average_precision_score(y,p)),"brier":float(brier_score_loss(y,p)),"precision":float(precision_score(y,pred,zero_division=0)),"recall":float(recall_score(y,pred,zero_division=0)),"f1":float(f1_score(y,pred,zero_division=0)),"tp":int(tp),"fp":int(fp),"tn":int(tn),"fn":int(fn)}

def _threshold(y,p,mrr):
    best=(.5,-1e18)
    for t in np.arange(.10,.81,.01):
        targeted=p>=t
        net=float((targeted*y.to_numpy()*mrr.to_numpy()*9*.72*.28).sum()-targeted.sum()*45)
        if net>best[1]: best=(round(float(t),2),net)
    return best

def _psi(ref,cur,bins=10):
    a=ref.astype(float).to_numpy();b=cur.astype(float).to_numpy()
    edges=np.unique(np.quantile(a,np.linspace(0,1,bins+1)))
    if len(edges)<3:return 0.0
    edges[0],edges[-1]=-np.inf,np.inf
    ah=np.clip(np.histogram(a,bins=edges)[0]/len(a),1e-6,None);bh=np.clip(np.histogram(b,bins=edges)[0]/len(b),1e-6,None)
    return float(np.sum((bh-ah)*np.log(bh/ah)))

def train_and_export(data_path:Path,artifact_dir:Path):
    artifact_dir.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(data_path,parse_dates=["snapshot_month"])
    tr=df[df.snapshot_month<"2026-01-01"].copy()
    va=df[(df.snapshot_month>="2026-01-01")&(df.snapshot_month<"2026-04-01")].copy()
    te=df[df.snapshot_month>="2026-04-01"].copy()
    prep=ColumnTransformer([("cat",OneHotEncoder(handle_unknown="ignore",sparse_output=False),CATEGORICAL),("num",StandardScaler(),NUMERIC)],verbose_feature_names_out=False)
    prep.fit(tr[FEATURES])
    xtr,xv,xte=prep.transform(tr[FEATURES]),prep.transform(va[FEATURES]),prep.transform(te[FEATURES])
    model=xgb.XGBClassifier(n_estimators=320,max_depth=4,learning_rate=.045,subsample=.85,colsample_bytree=.82,min_child_weight=4,reg_lambda=2,reg_alpha=.08,objective="binary:logistic",eval_metric="logloss",random_state=42,n_jobs=4)
    model.fit(xtr,tr.churned)
    raw=model.predict_proba(xv)[:,1];cal=LogisticRegression(C=1000).fit(_logit(raw),va.churned)
    pv=cal.predict_proba(_logit(raw))[:,1];threshold,val_value=_threshold(va.churned,pv,va.monthly_revenue)
    pt=cal.predict_proba(_logit(model.predict_proba(xte)[:,1]))[:,1]
    uplift={}
    for arm in (0,1):
        a=tr[tr.treatment==arm]
        m=xgb.XGBClassifier(n_estimators=240,max_depth=3,learning_rate=.05,subsample=.85,colsample_bytree=.85,min_child_weight=4,reg_lambda=2,objective="binary:logistic",eval_metric="logloss",random_state=100+arm,n_jobs=4)
        m.fit(prep.transform(a[FEATURES]),a.churned);uplift[arm]=m
    pc=uplift[0].predict_proba(xte)[:,1];pa=uplift[1].predict_proba(xte)[:,1];up=np.clip(pc-pa,-.5,.5)
    arr=te.monthly_revenue.to_numpy()*12;rar=pt*arr;ev=up*arr*.72-45
    scored=te[["customer_id","snapshot_month","plan_tier","monthly_revenue","nps","days_since_login","usage_change_90d"]].copy()
    scored["churn_probability"]=pt;scored["uplift"]=up;scored["annual_revenue_at_risk"]=rar;scored["expected_retention_value"]=ev;scored["priority_score"]=np.maximum(ev,0)*pt
    scored=scored.sort_values("priority_score",ascending=False)
    names=prep.get_feature_names_out().tolist();contrib=model.get_booster().predict(xgb.DMatrix(xte[:min(2000,len(xte))]),pred_contribs=True)
    imp=sorted([{"feature":f,"mean_abs_shap":float(v)} for f,v in zip(names,np.abs(contrib[:,:-1]).mean(axis=0))],key=lambda x:x["mean_abs_shap"],reverse=True)[:15]
    card={"model_name":"Technyder Retention Intelligence v1","problem":"Predict 60-day B2B SaaS churn and prioritize economically useful retention interventions.","data":{"synthetic":True,"rows":int(len(df)),"train_rows":int(len(tr)),"validation_rows":int(len(va)),"test_rows":int(len(te)),"test_period":"2026-04 through 2026-06","overall_churn_rate":float(df.churned.mean())},"champion":"XGBoost + Platt calibration","decision_threshold":threshold,"validation_expected_net_value":float(val_value),"test_metrics":_metrics(te.churned,pt,threshold),"portfolio":{"test_revenue_at_risk":float(rar.sum()),"accounts_above_threshold":int((pt>=threshold).sum()),"positive_uplift_accounts":int((up>0).sum()),"high_value_actionable_accounts":int((ev>500).sum()),"mean_positive_uplift":float(up[up>0].mean())}}
    drift=sorted([{"feature":c,"psi":_psi(tr[c],te[c])} for c in NUMERIC],key=lambda x:x["psi"],reverse=True)
    bundle={"preprocessor":prep,"model":model,"calibrator":cal,"uplift_control":uplift[0],"uplift_treated":uplift[1],"features":FEATURES,"feature_names":names,"threshold":threshold,"model_version":"1.0.0"}
    joblib.dump(bundle,artifact_dir/"retention_model.joblib",compress=3)
    (artifact_dir/"model_card.json").write_text(json.dumps(card,indent=2))
    (artifact_dir/"feature_importance.json").write_text(json.dumps(imp,indent=2))
    (artifact_dir/"drift_report.json").write_text(json.dumps({"status":"stable" if max(x["psi"] for x in drift)<.2 else "review","method":"Population Stability Index (PSI)","features":drift},indent=2))
    (artifact_dir/"portfolio_sample.json").write_text(scored.head(40).assign(snapshot_month=lambda x:x.snapshot_month.astype(str)).to_json(orient="records",indent=2))
