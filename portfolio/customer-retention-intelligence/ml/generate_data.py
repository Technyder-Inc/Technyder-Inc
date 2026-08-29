from __future__ import annotations
import numpy as np
import pandas as pd

def sigmoid(x):
    return 1/(1+np.exp(-x))

def generate_saas_churn_data(n_rows=24000,seed=42):
    rng=np.random.default_rng(seed)
    months=pd.date_range("2025-01-01","2026-06-01",freq="MS")
    snapshot_month=rng.choice(months,size=n_rows)
    plan=rng.choice(["Starter","Growth","Scale","Enterprise"],p=[.28,.36,.24,.12],size=n_rows)
    region=rng.choice(["North America","Europe","APAC","LATAM"],p=[.46,.27,.19,.08],size=n_rows)
    channel=rng.choice(["Organic","Partner","Paid","Outbound","Referral"],p=[.25,.18,.19,.22,.16],size=n_rows)
    tenure=np.clip(rng.gamma(2.4,10,n_rows).astype(int)+1,1,84)
    seats=np.clip(rng.lognormal(2.3,.85,n_rows).astype(int),2,450)
    mult=pd.Series(plan).map({"Starter":1,"Growth":1.8,"Scale":3.4,"Enterprise":7.5}).to_numpy()
    mrr=np.round(np.clip(38*seats*mult+rng.normal(0,180,n_rows),79,48000),2)
    usage=np.clip(rng.normal(63,22,n_rows),0,100)
    usage_delta=np.clip(rng.normal(-2,24,n_rows),-90,80)
    tickets=np.clip(rng.poisson(2.2,n_rows),0,20)
    nps=np.clip(np.round(rng.normal(34,31,n_rows)),-100,100).astype(int)
    payment=np.clip(rng.poisson(.28,n_rows),0,5)
    days=np.clip(np.round(rng.exponential(7.5,n_rows)),0,90).astype(int)
    adoption=np.clip(rng.beta(3.1,2.2,n_rows),.03,.99)
    integrations=np.clip(rng.poisson(3.4,n_rows),0,18)
    admin=np.clip(rng.poisson(7,n_rows),0,50)
    renewal=rng.binomial(1,.31,n_rows)
    months_left=np.where(renewal==1,rng.integers(0,3,n_rows),rng.integers(3,25,n_rows))
    price=rng.binomial(1,.16,n_rows)
    treatment=rng.binomial(1,.35,n_rows)
    risk=(-.95+.03*days-.017*usage-.018*usage_delta+.18*tickets-.010*nps+.58*payment
          -1.05*adoption-.035*np.minimum(tenure,36)-.10*integrations-.025*admin+.82*renewal
          -.045*months_left+.52*price+.22*(plan=="Starter")-.20*(plan=="Enterprise")
          +.18*(channel=="Paid")+.10*(channel=="Outbound")+.95*(usage_delta<-30)
          +.65*(days>20)+.85*((renewal==1)&(price==1))+.65*((tickets>=5)&(nps<0))
          -.75*((tenure>24)&(integrations>=4)&(adoption>.65)))
    effect=(-.95-.30*(nps>10)-.28*(usage>45)-.22*(renewal==1)+.45*(days>35)+.30*(payment>=2))
    month_index=pd.Series(snapshot_month).map({m:i for i,m in enumerate(months)}).to_numpy()
    p=np.clip(sigmoid(risk+treatment*effect+.018*month_index),.01,.92)
    churn=rng.binomial(1,p)
    return pd.DataFrame({
      "customer_id":[f"CUS-{i:06d}" for i in range(1,n_rows+1)],"snapshot_month":pd.to_datetime(snapshot_month),
      "plan_tier":plan,"region":region,"acquisition_channel":channel,"tenure_months":tenure,"seats":seats,
      "monthly_revenue":mrr,"usage_30d":np.round(usage,1),"usage_change_90d":np.round(usage_delta,1),
      "support_tickets_90d":tickets,"nps":nps,"payment_failures_90d":payment,"days_since_login":days,
      "feature_adoption":np.round(adoption,3),"integrations_count":integrations,"admin_logins_30d":admin,
      "renewal_due_60d":renewal,"contract_months_left":months_left,"price_increase_90d":price,
      "treatment":treatment,"churned":churn}).sort_values(["snapshot_month","customer_id"]).reset_index(drop=True)
