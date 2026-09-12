# Aircraft Fleet Predictive Maintenance Intelligence — Rebuild Entry Point

This branch contains the professional Power BI rebuild of the original NASA C-MAPSS FD001 learning project.

## Current phase

**Phase 0B — Model Integrity Repair**

Power BI development is intentionally blocked until the leakage-safe Python runner passes.

## First run

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python src\phase0b_model_integrity.py
```

Before running, make sure these source files are available in `data/raw/`:

```text
train_FD001.txt
test_FD001.txt
RUL_FD001.txt
```

During migration the runner also accepts `train_FD001.txt`, `test_FD001.txt`, or `RUL_FD001.txt` from the repository root, but `data/raw/` is the target professional structure.

## Expected success gate

A successful run ends with:

```text
PHASE_0B_RUNNER=PASS
```

It also creates:

```text
data/processed/model_validation_comparison.csv

data/powerbi/fact_engine_cycle.csv
data/powerbi/fact_engine_snapshot.csv
data/powerbi/dim_engine.csv
data/powerbi/dim_risk_band.csv
data/powerbi/model_metrics.csv
data/powerbi/feature_importance.csv

models/fd001_selected_random_forest.joblib
models/fd001_selected_features.json
```

Do not begin designing Power BI visuals until these outputs have been reviewed and reconciled.
