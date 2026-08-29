# Model governance

## Intended use
Rank B2B SaaS customer accounts for retention review. The score is a 60-day churn probability, not an automated eligibility or pricing decision.

## Leakage controls
- Predictors are snapshot-time observables.
- Train / validation / test are split by calendar time.
- Outcome is future churn in the next 60 days.

## Calibration
The XGBoost probability is Platt-calibrated on a later validation window so finance and success teams can interpret the score as a risk estimate, not only a ranking.

## Explainability
Model contributions explain which inputs pushed a prediction up or down. They describe model associations and are not causal effects.

## Uplift
The demo uses randomized synthetic treatment history and a T-learner. In real deployments, uplift should only be enabled when treatment assignment is randomized or otherwise causally credible.

## Monitoring
Production monitoring should cover feature drift, schema/missingness, calibration drift, PR-AUC/recall after labels mature, and incremental retained revenue by treatment policy.
