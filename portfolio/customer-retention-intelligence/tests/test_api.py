from fastapi.testclient import TestClient
from app import app

client=TestClient(app)

def test_health():
    r=client.get("/health")
    assert r.status_code==200 and r.json()["status"]=="ok"

def test_score():
    r=client.post("/api/score",json={})
    assert r.status_code==200
    body=r.json()
    assert 0<=body["churn_probability"]<=1
    assert "annual_revenue_at_risk" in body
    assert "estimated_uplift" in body

def test_model_card():
    r=client.get("/api/model-card")
    assert r.status_code==200 and r.json()["data"]["synthetic"] is True
