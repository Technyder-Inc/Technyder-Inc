from pathlib import Path
import sys

from fastapi import FastAPI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from employee_attrition import router as employee_router

app = FastAPI(
    title="Technyder Employee Attrition Analytics",
    version="1.0.0",
)

app.include_router(employee_router)

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "employee-attrition-analytics",
        "version": "1.0.0",
    }
