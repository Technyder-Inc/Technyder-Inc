from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_score():
    response = client.post("/api/score", json={})
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["churn_probability"] <= 1
    assert "annual_revenue_at_risk" in body
    assert "estimated_uplift" in body


def test_model_card():
    response = client.get("/api/model-card")
    assert response.status_code == 200
    assert response.json()["data"]["synthetic"] is True


def test_employee_page_has_top_right_sample_and_reasoning_ui():
    response = client.get("/employees")
    assert response.status_code == 200
    assert "Sample data" in response.text
    assert "Why this risk?" in response.text
    assert "preAnalysis" in response.text
    assert "runAnalysis()" in response.text


def test_employee_sample_upload_returns_conceptual_explanations():
    template = client.get("/api/employee-attrition/template.csv")
    assert template.status_code == 200

    response = client.post(
        "/api/employee-attrition/upload",
        files={
            "file": (
                "employee_attrition_template.csv",
                template.content,
                "text/csv",
            )
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert "methodology" in body
    assert body["methodology"]["model_type"] == "Attrition risk scoring model"
    assert "employees" in body and body["employees"]

    employee = body["employees"][0]
    assert "model_context" in employee
    assert "summary" in employee["model_context"]
    assert "top_signals" in employee

    if employee["top_signals"]:
        signal = employee["top_signals"][0]
        assert "display_value" in signal
        assert "benchmark" in signal
        assert "model_effect_pp" in signal
        assert "why" in signal
        assert "caution" in signal


def test_vercel_employee_entrypoint():
    from api.index import app as vercel_app

    vercel_client = TestClient(vercel_app)

    health = vercel_client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    page = vercel_client.get("/api/employees")
    assert page.status_code == 200
    assert "Employee Attrition Analyzer" in page.text


def test_employee_page_has_pagination_controls():
    response = client.get("/employees")
    assert response.status_code == 200
    assert 'id="employeePageSize"' in response.text
    assert 'id="employeePrev"' in response.text
    assert 'id="employeeNext"' in response.text
    assert "renderEmployeePage()" in response.text
    assert "changeEmployeePageSize" in response.text
