from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

CSV = """employee_id,snapshot_date,department,role_level,tenure_months,monthly_salary,overtime_hours_30d,avg_weekly_hours,absent_days_90d,late_days_90d,performance_score,engagement_score,manager_changes_12m,months_since_promotion,training_hours_90d,remote_days_week,commute_minutes,pay_raise_months_ago,left_company
EMP-001,2026-08-01,Engineering,Mid,18,5200,8,41,1,1,4.1,78,0,14,18,3,22,10,0
EMP-002,2026-08-01,Sales,Senior,29,7600,24,49,4,3,3.7,44,1,31,6,2,55,22,0
EMP-003,2026-08-01,Operations,Junior,5,3400,21,51,6,5,3.2,42,1,18,2,0,61,17,1
"""

def test_employee_page():
    r = client.get("/employees")
    assert r.status_code == 200
    assert "Employee Attrition Analyzer" in r.text

def test_csv_template():
    r = client.get("/api/employee-attrition/template.csv")
    assert r.status_code == 200
    assert "employee_id" in r.text
    assert "left_company" in r.text

def test_employee_upload():
    r = client.post(
        "/api/employee-attrition/upload",
        files={"file": ("employees.csv", CSV.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kpis"]["unique_employees"] == 3
    assert body["kpis"]["historical_exits"] == 1
    assert body["kpis"]["observed_churn_rate"] == 0.3333
    assert body["kpis"]["active_employees"] == 2
    assert 0 <= body["kpis"]["predicted_attrition_rate"] <= 1
