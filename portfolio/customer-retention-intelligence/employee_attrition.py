from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from datetime import date
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from openpyxl import Workbook, load_workbook

router = APIRouter()

REQUIRED_COLUMNS = [
    "employee_id",
    "snapshot_date",
    "department",
    "role_level",
    "tenure_months",
    "monthly_salary",
    "overtime_hours_30d",
    "avg_weekly_hours",
    "absent_days_90d",
    "late_days_90d",
    "performance_score",
    "engagement_score",
    "manager_changes_12m",
    "months_since_promotion",
    "training_hours_90d",
    "remote_days_week",
    "commute_minutes",
    "pay_raise_months_ago",
]

OPTIONAL_COLUMNS = ["left_company"]

TEMPLATE_ROWS = [
    ["EMP-0001","2026-08-01","Engineering","Mid",18,5200,8,41,1,1,4.1,78,0,14,18,3,22,10,0],
    ["EMP-0002","2026-08-01","Sales","Senior",29,7600,24,49,4,3,3.7,44,1,31,6,2,55,22,0],
    ["EMP-0003","2026-08-01","Customer Success","Mid",11,5000,17,46,5,4,3.9,39,2,28,4,4,48,19,0],
    ["EMP-0004","2026-08-01","Finance","Lead",46,9100,5,40,0,0,4.4,83,0,8,22,2,18,6,0],
    ["EMP-0005","2026-08-01","Operations","Junior",5,3400,21,51,6,5,3.2,42,1,18,2,0,61,17,0],
    ["EMP-0006","2026-08-01","Engineering","Senior",37,7900,7,42,1,0,4.5,88,0,10,25,5,12,8,0],
    ["EMP-0007","2026-08-01","Sales","Mid",7,4800,29,54,3,4,3.5,36,2,40,3,1,52,26,1],
    ["EMP-0008","2026-08-01","Customer Success","Lead",33,8600,10,43,2,1,4.0,72,0,19,14,3,27,12,0],
]

def _float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be numeric")

def _int01(value: Any) -> int:
    if value in (None, ""):
        return 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "left", "exited"}:
        return 1
    if text in {"0", "false", "no", "n", "active", "stayed"}:
        return 0
    try:
        return 1 if float(text) >= 1 else 0
    except ValueError:
        raise ValueError("left_company must be 0/1, true/false, active/left")

def employee_attrition_score(row: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
    engagement = _float(row, "engagement_score")
    overtime = _float(row, "overtime_hours_30d")
    weekly = _float(row, "avg_weekly_hours")
    absent = _float(row, "absent_days_90d")
    late = _float(row, "late_days_90d")
    manager_changes = _float(row, "manager_changes_12m")
    months_promotion = _float(row, "months_since_promotion")
    training = _float(row, "training_hours_90d")
    commute = _float(row, "commute_minutes")
    raise_months = _float(row, "pay_raise_months_ago")
    tenure = _float(row, "tenure_months")

    contributions = []
    z = -3.2

    def add(label: str, amount: float):
        nonlocal z
        z += amount
        if abs(amount) >= 0.05:
            contributions.append(
                {
                    "signal": label,
                    "direction": "raises risk" if amount > 0 else "reduces risk",
                    "impact": round(amount, 3),
                }
            )

    add("Low engagement", max(0.0, 60.0 - engagement) * 0.035)
    add("High overtime", max(0.0, overtime - 12.0) * 0.045)
    add("Long weekly hours", max(0.0, weekly - 45.0) * 0.06)
    add("Absence frequency", absent * 0.12)
    add("Late arrivals", late * 0.06)
    add("Manager changes", manager_changes * 0.35)
    add("Time since promotion", max(0.0, months_promotion - 24.0) * 0.025)
    add("Time since pay raise", max(0.0, raise_months - 18.0) * 0.025)
    add("Long commute", max(0.0, commute - 40.0) * 0.012)
    add("Very short tenure", 0.45 if tenure < 6 else 0.0)
    add("Recent training", -min(training, 30.0) * 0.012)

    probability = 1.0 / (1.0 + math.exp(-z))
    contributions = sorted(contributions, key=lambda x: abs(x["impact"]), reverse=True)[:4]
    return probability, contributions

def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise HTTPException(status_code=400, detail="The uploaded file contains no employee rows.")

    headers = {str(k).strip() for k in rows[0].keys() if k is not None}
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing required columns", "missing_columns": missing},
        )

    latest: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows, start=2):
        row = {str(k).strip(): v for k, v in raw.items() if k is not None}
        employee_id = str(row.get("employee_id", "")).strip()
        if not employee_id:
            raise HTTPException(status_code=400, detail=f"Row {index}: employee_id is required")

        snapshot = str(row.get("snapshot_date", "")).strip()
        current = latest.get(employee_id)
        if current is None or snapshot >= str(current.get("snapshot_date", "")):
            latest[employee_id] = row

    return list(latest.values())

def _parse_csv(content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))

def _parse_xlsx(content: bytes) -> list[dict[str, Any]]:
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb["Employee_Data"] if "Employee_Data" in wb.sheetnames else wb[wb.sheetnames[0]]
    iterator = ws.iter_rows(values_only=True)
    try:
        header_row = next(iterator)
    except StopIteration:
        return []
    headers = [str(v).strip() if v is not None else "" for v in header_row]
    rows = []
    for values in iterator:
        if not any(v not in (None, "") for v in values):
            continue
        rows.append({headers[i]: values[i] for i in range(min(len(headers), len(values))) if headers[i]})
    return rows

def analyze_employee_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = _normalize_rows(rows)
    scored = []
    exits = 0
    active = 0
    risk_sum = 0.0
    high_risk = 0
    engagement_values = []
    by_department: dict[str, list[float]] = defaultdict(list)

    has_exit_column = any("left_company" in r for r in normalized)

    for row in normalized:
        exited = _int01(row.get("left_company", 0)) if has_exit_column else 0
        exits += exited

        try:
            engagement_values.append(_float(row, "engagement_score"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{row.get('employee_id')}: {exc}")

        if exited:
            continue

        active += 1
        try:
            risk, drivers = employee_attrition_score(row)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{row.get('employee_id')}: {exc}")

        risk_sum += risk
        if risk >= 0.25:
            band = "High"
            high_risk += 1
        elif risk >= 0.12:
            band = "Medium"
        else:
            band = "Low"

        department = str(row.get("department", "Unknown"))
        by_department[department].append(risk)

        scored.append(
            {
                "employee_id": str(row["employee_id"]),
                "department": department,
                "role_level": str(row.get("role_level", "")),
                "attrition_probability": round(risk, 4),
                "risk_band": band,
                "engagement_score": _float(row, "engagement_score"),
                "overtime_hours_30d": _float(row, "overtime_hours_30d"),
                "top_signals": drivers,
            }
        )

    scored.sort(key=lambda item: item["attrition_probability"], reverse=True)
    total = len(normalized)

    department_summary = [
        {
            "department": department,
            "active_employees": len(values),
            "predicted_attrition_rate": round(sum(values) / len(values), 4),
        }
        for department, values in by_department.items()
    ]
    department_summary.sort(key=lambda x: x["predicted_attrition_rate"], reverse=True)

    return {
        "kpis": {
            "unique_employees": total,
            "active_employees": active,
            "historical_exits": exits if has_exit_column else None,
            "observed_churn_rate": round(exits / total, 4) if has_exit_column and total else None,
            "predicted_attrition_rate": round(risk_sum / active, 4) if active else 0.0,
            "high_risk_active_employees": high_risk,
            "average_engagement_score": round(sum(engagement_values) / len(engagement_values), 1)
            if engagement_values
            else None,
        },
        "department_summary": department_summary,
        "employees": scored[:200],
        "model_note": (
            "Synthetic transparent attrition-risk demo using operational work signals only. "
            "Use for aggregate retention/workforce planning, not termination, hiring, pay, promotion, "
            "or other employment decisions."
        ),
    }

def _csv_template() -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
    writer.writerows(TEMPLATE_ROWS)
    return output.getvalue().encode("utf-8")

def _xlsx_template() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Employee_Data"
    ws.append(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
    for row in TEMPLATE_ROWS:
        ws.append(row)
    ws.freeze_panes = "A2"

    widths = {
        "A": 14, "B": 14, "C": 20, "D": 12, "E": 14, "F": 15, "G": 19, "H": 17,
        "I": 18, "J": 16, "K": 18, "L": 18, "M": 20, "N": 22, "O": 20, "P": 18,
        "Q": 16, "R": 20, "S": 14,
    }
    for column, width in widths.items():
        ws.column_dimensions[column].width = width

    dd = wb.create_sheet("Data_Dictionary")
    dd.append(["Column", "Required", "Description"])
    descriptions = {
        "employee_id": "Unique employee identifier; avoid names/emails in demo uploads.",
        "snapshot_date": "Snapshot date in YYYY-MM-DD format.",
        "department": "Department or business function.",
        "role_level": "Role level such as Junior, Mid, Senior, Lead, Manager.",
        "tenure_months": "Months employed at snapshot date.",
        "monthly_salary": "Monthly base salary; not used by the demo risk score.",
        "overtime_hours_30d": "Overtime hours in the last 30 days.",
        "avg_weekly_hours": "Average weekly working hours.",
        "absent_days_90d": "Absent days in the last 90 days.",
        "late_days_90d": "Late arrivals in the last 90 days.",
        "performance_score": "1-5 performance score; not used by the demo risk score.",
        "engagement_score": "0-100 engagement score.",
        "manager_changes_12m": "Number of manager changes in the last 12 months.",
        "months_since_promotion": "Months since last promotion.",
        "training_hours_90d": "Training hours in the last 90 days.",
        "remote_days_week": "Average remote days per week; not used by the demo risk score.",
        "commute_minutes": "One-way commute minutes.",
        "pay_raise_months_ago": "Months since last pay raise.",
        "left_company": "Optional historical outcome: 1 exited, 0 stayed. Used for observed churn only.",
    }
    for col in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        dd.append([col, "Optional" if col in OPTIONAL_COLUMNS else "Yes", descriptions[col]])

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

@router.get("/employees", response_class=HTMLResponse)
def employee_page():
    return EMPLOYEE_PAGE

@router.get("/api/employee-attrition/template.csv")
def download_csv_template():
    return Response(
        content=_csv_template(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="employee_attrition_template.csv"'},
    )

@router.get("/api/employee-attrition/template.xlsx")
def download_xlsx_template():
    return Response(
        content=_xlsx_template(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="employee_attrition_template.xlsx"'},
    )

@router.post("/api/employee-attrition/upload")
async def upload_employee_file(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Upload a .csv or .xlsx file.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Demo upload limit is 5 MB.")

    try:
        rows = _parse_csv(content) if filename.endswith(".csv") else _parse_xlsx(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}") from exc

    if len(rows) > 5000:
        raise HTTPException(status_code=413, detail="Demo upload limit is 5,000 rows.")

    return analyze_employee_rows(rows)


EMPLOYEE_PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Employee Attrition Analyzer — Technyder</title>
<style>
body{margin:0;background:#f6f7f9;color:#111827;font-family:Inter,Arial,sans-serif}
.w{max-width:1120px;margin:auto;padding:38px 20px 60px}
.k{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:#667085;font-weight:700}
h1{font-size:40px;margin:8px 0 10px}.sub{color:#667085;line-height:1.55;max-width:850px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:18px}
.upload{margin:24px 0;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
input[type=file]{background:white;border:1px solid #d0d5dd;padding:12px;border-radius:10px;min-width:300px}
button,.btn{background:#111827;color:white;border:0;padding:12px 16px;border-radius:10px;font-weight:700;cursor:pointer;text-decoration:none;font-size:14px}
.btn.alt{background:white;color:#111827;border:1px solid #d0d5dd}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0}.metric{font-size:28px;font-weight:800}.label{font-size:12px;color:#667085}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px;border-bottom:1px solid #eaecf0;text-align:left}th{color:#667085;font-size:11px;text-transform:uppercase}
.badge{padding:4px 8px;border-radius:999px;font-size:11px;font-weight:700}.High{background:#fee4e2;color:#b42318}.Medium{background:#fef0c7;color:#b54708}.Low{background:#dcfae6;color:#067647}
.note{font-size:12px;color:#667085;margin-top:18px}.error{color:#b42318;font-weight:700}.hidden{display:none}
@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}.upload{align-items:stretch}input[type=file]{min-width:0;width:100%}}
</style>
</head>
<body>
<div class="w">
<div class="k">Technyder / Workforce Analytics Demo</div>
<h1>Employee Attrition Analyzer</h1>
<div class="sub">
Upload a CSV or Excel file to calculate historical employee churn (when an exit flag exists),
estimate current workforce attrition risk, and summarize retention pressure by department.
</div>

<div class="upload">
<input id="file" type="file" accept=".csv,.xlsx">
<button onclick="runAnalysis()">Run attrition analysis</button>
<a class="btn alt" href="/api/employee-attrition/template.csv">Download CSV template</a>
<a class="btn alt" href="/api/employee-attrition/template.xlsx">Download Excel template</a>
</div>
<div id="error" class="error"></div>

<div id="result" class="hidden">
<div class="grid">
<div class="card"><div class="label">Employees</div><div class="metric" id="employees">—</div></div>
<div class="card"><div class="label">Observed churn</div><div class="metric" id="observed">—</div></div>
<div class="card"><div class="label">Predicted attrition</div><div class="metric" id="predicted">—</div></div>
<div class="card"><div class="label">High-risk active</div><div class="metric" id="highrisk">—</div></div>
<div class="card"><div class="label">Avg engagement</div><div class="metric" id="engagement">—</div></div>
</div>

<div class="card" style="margin-bottom:16px">
<h2>Retention review queue</h2>
<table>
<thead><tr><th>Employee ID</th><th>Department</th><th>Role</th><th>Risk</th><th>Probability</th><th>Primary signals</th></tr></thead>
<tbody id="rows"></tbody>
</table>
</div>

<div class="card">
<h2>Department attrition pressure</h2>
<table>
<thead><tr><th>Department</th><th>Active employees</th><th>Predicted attrition rate</th></tr></thead>
<tbody id="departments"></tbody>
</table>
</div>

<div class="note" id="note"></div>
</div>
</div>

<script>
const pct=v=>v===null||v===undefined?'N/A':(v*100).toFixed(1)+'%';

async function runAnalysis(){
  const file=document.getElementById('file').files[0];
  const error=document.getElementById('error');
  error.textContent='';
  if(!file){error.textContent='Choose a CSV or Excel file first.';return;}

  const form=new FormData();
  form.append('file',file);

  try{
    const response=await fetch('/api/employee-attrition/upload',{method:'POST',body:form});
    const data=await response.json();
    if(!response.ok){throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));}

    const k=data.kpis;
    document.getElementById('employees').textContent=k.unique_employees.toLocaleString();
    document.getElementById('observed').textContent=pct(k.observed_churn_rate);
    document.getElementById('predicted').textContent=pct(k.predicted_attrition_rate);
    document.getElementById('highrisk').textContent=k.high_risk_active_employees.toLocaleString();
    document.getElementById('engagement').textContent=k.average_engagement_score ?? 'N/A';

    document.getElementById('rows').innerHTML=data.employees.slice(0,50).map(e=>{
      const signals=e.top_signals.map(s=>s.signal).join(', ');
      return '<tr><td>'+e.employee_id+'</td><td>'+e.department+'</td><td>'+e.role_level+
      '</td><td><span class="badge '+e.risk_band+'">'+e.risk_band+'</span></td><td>'+
      pct(e.attrition_probability)+'</td><td>'+signals+'</td></tr>';
    }).join('');

    document.getElementById('departments').innerHTML=data.department_summary.map(d=>
      '<tr><td>'+d.department+'</td><td>'+d.active_employees+'</td><td>'+
      pct(d.predicted_attrition_rate)+'</td></tr>'
    ).join('');

    document.getElementById('note').textContent=data.model_note;
    document.getElementById('result').classList.remove('hidden');
  }catch(err){
    error.textContent=err.message;
  }
}
</script>
</body>
</html>"""
