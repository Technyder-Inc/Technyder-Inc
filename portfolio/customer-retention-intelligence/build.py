from pathlib import Path

from ml.export_runtime import export_portable_runtime
from ml.generate_data import generate_saas_churn_data
from ml.train import train_and_export

ROOT = Path(__file__).resolve().parent
data_path = ROOT / "data" / "synthetic_saas_churn.csv"
artifact_dir = ROOT / "artifacts"

data_path.parent.mkdir(parents=True, exist_ok=True)
artifact_dir.mkdir(parents=True, exist_ok=True)

if not data_path.exists():
    generate_saas_churn_data(24000, 42).to_csv(data_path, index=False)

train_and_export(data_path, artifact_dir)
runtime_path = export_portable_runtime(data_path, artifact_dir)

print(f"Portable runtime: {runtime_path} ({runtime_path.stat().st_size / 1024:.1f} KB)")
