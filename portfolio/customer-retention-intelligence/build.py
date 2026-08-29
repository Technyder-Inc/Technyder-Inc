from pathlib import Path
from ml.generate_data import generate_saas_churn_data
from ml.train import train_and_export

ROOT=Path(__file__).resolve().parent
data_path=ROOT/"data"/"synthetic_saas_churn.csv"
data_path.parent.mkdir(parents=True,exist_ok=True)
if not data_path.exists():
    generate_saas_churn_data(24000,42).to_csv(data_path,index=False)
train_and_export(data_path,ROOT/"artifacts")
