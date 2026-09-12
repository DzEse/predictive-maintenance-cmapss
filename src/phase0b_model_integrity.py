"""Phase 0B model-integrity runner for NASA C-MAPSS FD001.

This script repairs the original portfolio methodology by:
- excluding future-information fields such as max_cycle from model inputs;
- validating by engine trajectory rather than random cycle rows;
- evaluating the selected model on NASA's separate FD001 test engines;
- exporting clearly grained datasets for later Power BI development.

Run from the repository root:
    python src/phase0b_model_integrity.py
"""

from __future__ import annotations

from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
POWERBI_DIR = ROOT / "data" / "powerbi"
MODEL_DIR = ROOT / "models"

COLUMNS = (
    ["unit", "cycle"]
    + [f"op_setting_{i}" for i in range(1, 4)]
    + [f"sensor_{i}" for i in range(1, 22)]
)

RISK_ROWS = [
    {
        "risk_band_key": 1,
        "risk_band": "PRIORITY REVIEW",
        "min_predicted_rul": 0,
        "max_predicted_rul": 29.999999,
        "sort_order": 1,
        "meaning": "Illustrative portfolio band for the lowest predicted RUL values; not a certified maintenance limit.",
    },
    {
        "risk_band_key": 2,
        "risk_band": "MONITOR",
        "min_predicted_rul": 30,
        "max_predicted_rul": 59.999999,
        "sort_order": 2,
        "meaning": "Illustrative portfolio band for intermediate predicted RUL values; not a certified maintenance limit.",
    },
    {
        "risk_band_key": 3,
        "risk_band": "LOWER PRIORITY",
        "min_predicted_rul": 60,
        "max_predicted_rul": np.nan,
        "sort_order": 3,
        "meaning": "Illustrative portfolio band for higher predicted RUL values; not a certified maintenance limit.",
    },
]


def ensure_directories() -> None:
    for directory in (RAW_DIR, PROCESSED_DIR, POWERBI_DIR, MODEL_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def resolve_source_file(filename: str) -> Path:
    """Prefer data/raw, but allow the repository root during migration."""
    candidates = [RAW_DIR / filename, ROOT / filename]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Missing {filename}. Place it in {RAW_DIR}. "
        "FD001 requires train_FD001.txt, test_FD001.txt and RUL_FD001.txt."
    )


def load_cmapss(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=r"\s+", header=None)
    if frame.shape[1] != 26:
        raise ValueError(f"{path.name}: expected 26 columns, found {frame.shape[1]}")
    frame.columns = COLUMNS
    frame["unit"] = frame["unit"].astype(int)
    frame["cycle"] = frame["cycle"].astype(int)
    return frame


def load_rul_truth(path: Path, expected_units: int) -> pd.DataFrame:
    rul = pd.read_csv(path, sep=r"\s+", header=None)
    rul = rul.iloc[:, [0]].rename(columns={0: "final_actual_rul"})
    rul["unit"] = np.arange(1, len(rul) + 1, dtype=int)
    rul["final_actual_rul"] = rul["final_actual_rul"].astype(float)
    if len(rul) != expected_units:
        raise ValueError(
            f"{path.name}: expected {expected_units} RUL values, found {len(rul)}"
        )
    return rul[["unit", "final_actual_rul"]]


def validate_source(frame: pd.DataFrame, name: str, expected_units: int) -> None:
    duplicate_count = frame.duplicated(["unit", "cycle"]).sum()
    if duplicate_count:
        raise ValueError(f"{name}: found {duplicate_count} duplicate unit-cycle rows")
    if frame.isna().any().any():
        raise ValueError(f"{name}: unexpected missing values in raw source")
    unit_count = frame["unit"].nunique()
    if unit_count != expected_units:
        raise ValueError(f"{name}: expected {expected_units} engines, found {unit_count}")


def add_training_rul(train: pd.DataFrame) -> pd.DataFrame:
    out = train.copy()
    max_cycles = out.groupby("unit", as_index=False)["cycle"].max()
    max_cycles = max_cycles.rename(columns={"cycle": "max_cycle"})
    out = out.merge(max_cycles, on="unit", how="left", validate="many_to_one")
    out["actual_rul"] = out["max_cycle"] - out["cycle"]
    return out


def add_test_rul(test: pd.DataFrame, truth: pd.DataFrame) -> pd.DataFrame:
    """Derive actual RUL for every observed test cycle from NASA's final-cycle truth."""
    out = test.copy()
    last_cycles = out.groupby("unit", as_index=False)["cycle"].max()
    last_cycles = last_cycles.rename(columns={"cycle": "last_observed_cycle"})
    out = out.merge(last_cycles, on="unit", how="left", validate="many_to_one")
    out = out.merge(truth, on="unit", how="left", validate="many_to_one")
    out["actual_rul"] = (
        out["final_actual_rul"] + out["last_observed_cycle"] - out["cycle"]
    )
    return out


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.sort_values(["unit", "cycle"]).copy()
    grouped = out.groupby("unit", sort=False)["sensor_2"]
    out["sensor_2_rolling_mean_5"] = grouped.transform(
        lambda series: series.rolling(window=5, min_periods=1).mean()
    )
    out["sensor_2_lag_1"] = grouped.shift(1)
    out["sensor_2_lag_1"] = out["sensor_2_lag_1"].fillna(out["sensor_2"])
    out["sensor_2_diff_1"] = out["sensor_2"] - out["sensor_2_lag_1"]
    return out


def available_raw_features(train: pd.DataFrame) -> list[str]:
    candidates = ["cycle"] + [f"op_setting_{i}" for i in range(1, 4)] + [
        f"sensor_{i}" for i in range(1, 22)
    ]
    return [column for column in candidates if train[column].nunique(dropna=False) > 1]


def regression_metrics(actual: pd.Series | np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual_array = np.asarray(actual, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    residual = actual_array - predicted_array
    abs_error = np.abs(residual)
    return {
        "mae": float(mean_absolute_error(actual_array, predicted_array)),
        "rmse": float(mean_squared_error(actual_array, predicted_array) ** 0.5),
        "r2": float(r2_score(actual_array, predicted_array)),
        "mean_error_bias": float(residual.mean()),
        "within_10_pct": float((abs_error <= 10).mean() * 100),
        "within_20_pct": float((abs_error <= 20).mean() * 100),
        "within_30_pct": float((abs_error <= 30).mean() * 100),
    }


def new_model() -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )


def fit_and_validate(
    train: pd.DataFrame,
    feature_sets: dict[str, list[str]],
) -> tuple[str, pd.DataFrame]:
    groups = train["unit"]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, validation_idx = next(splitter.split(train, groups=groups))

    development = train.iloc[train_idx]
    validation = train.iloc[validation_idx]

    development_units = set(development["unit"].unique())
    validation_units = set(validation["unit"].unique())
    overlap = development_units.intersection(validation_units)
    if overlap:
        raise AssertionError(f"Engine leakage detected across validation split: {sorted(overlap)}")

    records: list[dict[str, float | str | int]] = []
    for model_name, features in feature_sets.items():
        model = new_model()
        model.fit(development[features], development["actual_rul"])
        prediction = model.predict(validation[features])
        metrics = regression_metrics(validation["actual_rul"], prediction)
        records.append(
            {
                "model_name": model_name,
                "development_engines": len(development_units),
                "validation_engines": len(validation_units),
                "feature_count": len(features),
                **metrics,
            }
        )

    comparison = pd.DataFrame(records).sort_values(["mae", "rmse"]).reset_index(drop=True)
    selected_name = str(comparison.loc[0, "model_name"])
    return selected_name, comparison


def risk_band(predicted_rul: float) -> tuple[int, str]:
    if predicted_rul < 30:
        return 1, "PRIORITY REVIEW"
    if predicted_rul < 60:
        return 2, "MONITOR"
    return 3, "LOWER PRIORITY"


def main() -> None:
    ensure_directories()

    train_path = resolve_source_file("train_FD001.txt")
    test_path = resolve_source_file("test_FD001.txt")
    rul_path = resolve_source_file("RUL_FD001.txt")

    train_raw = load_cmapss(train_path)
    test_raw = load_cmapss(test_path)
    validate_source(train_raw, "train_FD001", expected_units=100)
    validate_source(test_raw, "test_FD001", expected_units=100)

    truth = load_rul_truth(rul_path, expected_units=100)
    train = add_engineered_features(add_training_rul(train_raw))
    test = add_engineered_features(add_test_rul(test_raw, truth))

    baseline_features = available_raw_features(train)
    engineered_features = [
        "sensor_2_rolling_mean_5",
        "sensor_2_lag_1",
        "sensor_2_diff_1",
    ]
    enhanced_features = baseline_features + engineered_features

    forbidden = {"unit", "max_cycle", "actual_rul", "final_actual_rul", "last_observed_cycle"}
    if forbidden.intersection(baseline_features) or forbidden.intersection(enhanced_features):
        raise AssertionError("Forbidden leakage/identifier field entered a feature list")

    feature_sets = {
        "baseline_raw_available": baseline_features,
        "enhanced_sensor2_temporal": enhanced_features,
    }

    selected_name, validation_comparison = fit_and_validate(train, feature_sets)
    selected_features = feature_sets[selected_name]

    model = new_model()
    model.fit(train[selected_features], train["actual_rul"])

    test["predicted_rul"] = model.predict(test[selected_features])
    test["prediction_error"] = test["actual_rul"] - test["predicted_rul"]
    test["absolute_error"] = test["prediction_error"].abs()

    bands = test["predicted_rul"].apply(risk_band)
    test["risk_band_key"] = [item[0] for item in bands]
    test["risk_band"] = [item[1] for item in bands]

    snapshot = (
        test.sort_values(["unit", "cycle"])
        .groupby("unit", as_index=False)
        .tail(1)
        .sort_values("unit")
        .reset_index(drop=True)
    )
    if snapshot["unit"].nunique() != 100 or len(snapshot) != 100:
        raise AssertionError("Official test snapshot must contain exactly one row for each of 100 engines")

    official_metrics = regression_metrics(snapshot["actual_rul"], snapshot["predicted_rul" ])

    metric_rows = [
        {"metric": "MAE", "value": official_metrics["mae"], "unit": "cycles"},
        {"metric": "RMSE", "value": official_metrics["rmse"], "unit": "cycles"},
        {"metric": "R2", "value": official_metrics["r2"], "unit": "score"},
        {"metric": "Mean Error Bias", "value": official_metrics["mean_error_bias"], "unit": "cycles"},
        {"metric": "Within ±10 Cycles", "value": official_metrics["within_10_pct"], "unit": "percent"},
        {"metric": "Within ±20 Cycles", "value": official_metrics["within_20_pct"], "unit": "percent"},
        {"metric": "Within ±30 Cycles", "value": official_metrics["within_30_pct"], "unit": "percent"},
    ]
    model_metrics = pd.DataFrame(metric_rows)
    model_metrics.insert(0, "model_name", selected_name)
    model_metrics.insert(1, "evaluation_scope", "NASA FD001 official test final engine snapshots")

    importance = pd.DataFrame(
        {"feature": selected_features, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False).reset_index(drop=True)
    importance.insert(0, "importance_rank", np.arange(1, len(importance) + 1))

    dim_engine = pd.DataFrame({"unit": sorted(test["unit"].unique())})
    dim_engine["engine_label"] = dim_engine["unit"].map(lambda value: f"Engine {value:03d}")
    dim_risk_band = pd.DataFrame(RISK_ROWS)

    cycle_columns = [
        "unit", "cycle", "last_observed_cycle", "actual_rul", "predicted_rul",
        "prediction_error", "absolute_error", "risk_band_key", "risk_band",
    ] + [f"op_setting_{i}" for i in range(1, 4)] + [f"sensor_{i}" for i in range(1, 22)] + engineered_features
    cycle_export = test[cycle_columns].copy()

    snapshot_columns = [
        "unit", "cycle", "actual_rul", "predicted_rul", "prediction_error",
        "absolute_error", "risk_band_key", "risk_band",
    ]
    snapshot_export = snapshot[snapshot_columns].copy()

    cycle_export.to_csv(POWERBI_DIR / "fact_engine_cycle.csv", index=False)
    snapshot_export.to_csv(POWERBI_DIR / "fact_engine_snapshot.csv", index=False)
    dim_engine.to_csv(POWERBI_DIR / "dim_engine.csv", index=False)
    dim_risk_band.to_csv(POWERBI_DIR / "dim_risk_band.csv", index=False)
    model_metrics.to_csv(POWERBI_DIR / "model_metrics.csv", index=False)
    importance.to_csv(POWERBI_DIR / "feature_importance.csv", index=False)
    validation_comparison.to_csv(PROCESSED_DIR / "model_validation_comparison.csv", index=False)

    joblib.dump(model, MODEL_DIR / "fd001_selected_random_forest.joblib")
    (MODEL_DIR / "fd001_selected_features.json").write_text(
        json.dumps({"model_name": selected_name, "features": selected_features}, indent=2),
        encoding="utf-8",
    )

    print("\nPHASE 0B — MODEL INTEGRITY REPAIR")
    print("=" * 52)
    print(f"Training rows                : {len(train):,}")
    print(f"Training engines             : {train['unit'].nunique()}")
    print(f"Official test rows           : {len(test):,}")
    print(f"Official test engines        : {test['unit'].nunique()}")
    print(f"Selected specification       : {selected_name}")
    print(f"Selected feature count       : {len(selected_features)}")
    print("\nValidation model comparison")
    print(validation_comparison.to_string(index=False))
    print("\nOfficial NASA test — final snapshot metrics")
    print(f"MAE                           : {official_metrics['mae']:.4f} cycles")
    print(f"RMSE                          : {official_metrics['rmse']:.4f} cycles")
    print(f"R²                            : {official_metrics['r2']:.4f}")
    print(f"Mean error bias               : {official_metrics['mean_error_bias']:.4f} cycles")
    print(f"Within ±10 cycles             : {official_metrics['within_10_pct']:.2f}%")
    print(f"Within ±20 cycles             : {official_metrics['within_20_pct']:.2f}%")
    print(f"Within ±30 cycles             : {official_metrics['within_30_pct']:.2f}%")
    print("\nPower BI export directory")
    print(POWERBI_DIR)
    print("\nPHASE_0B_RUNNER=PASS")


if __name__ == "__main__":
    main()
