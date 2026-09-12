# Phase 0B — Model Integrity Repair

## Objective

Repair the predictive-maintenance foundation before any Power BI report is built. The goal is not to maximize a headline score; it is to create a defensible evaluation design that can be explained in an interview.

## Defects identified in the original learning notebook

### 1. Future-information leakage through `max_cycle`

The training target is correctly defined as:

```text
RUL = max_cycle - cycle
```

However, the original feature matrix removed `unit`, `cycle`, and `RUL` while leaving `max_cycle` available to the Random Forest. Because `max_cycle` is the future failure cycle, it is unavailable at prediction time and must not be an input feature.

**Repair:** `max_cycle` is used only to construct training labels and is excluded from every model feature list.

### 2. Row-level random train/test split

The original notebook randomly split individual engine-cycle rows. This allows observations from the same engine trajectory to appear in both training and testing subsets.

**Repair:** model-development validation is split by engine ID using a group-aware split. Entire engine trajectories belong to one side of the split.

### 3. Test observations described as engines

The original test split contained 4,127 cycle-level rows, but downstream reporting described them as 4,127 engines.

**Repair:** the rebuilt workflow distinguishes:

- **cycle observations** — one row per engine per cycle;
- **engine snapshots** — one latest observed row per unique test engine.

Executive Power BI KPIs must use the engine snapshot table when reporting engine counts.

### 4. Risk thresholds overstated as maintenance rules

The original `<30`, `<60`, `>=60` RUL bands were portfolio-created thresholds, not certified maintenance limits.

**Repair:** retain thresholds only as clearly labelled **illustrative analytical risk bands**. They support portfolio prioritization and do not prescribe real aircraft maintenance.

### 5. Feature-engineering improvement not benchmarked

The original notebook stated that engineered features significantly improved performance without a direct baseline comparison.

**Repair:** compare a baseline Random Forest using available raw/current-state features with an enhanced Random Forest that adds historical Sensor 2 rolling, lag, and difference features. Select the model using group-held-out validation only.

## Professional evaluation architecture

```text
NASA train_FD001
      |
      +--> construct training RUL labels
      |
      +--> group-aware train/validation split by engine
      |        |
      |        +--> baseline model
      |        +--> enhanced model
      |        +--> select using validation MAE
      |
      +--> refit selected specification on all training engines
                     |
NASA test_FD001 -----+----> predictions
NASA RUL_FD001 ------+----> official test evaluation
                     |
                     +--> Power BI analytical exports
```

## Reportable metrics

The professional rebuild records:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- R-squared (R²)
- mean signed error / bias
- percentage of final-engine predictions within ±10, ±20, and ±30 cycles

The final README and Power BI report must use the newly generated metrics, not the scores from the original leakage-prone notebook.

## Power BI output grains

### `fact_engine_cycle.csv`
One row per FD001 test engine per observed operating cycle. Supports degradation and diagnostic analysis.

### `fact_engine_snapshot.csv`
One row per FD001 test engine at its latest observed cycle. Supports executive fleet counts and prioritization.

### `dim_engine.csv`
One row per unique test engine.

### `dim_risk_band.csv`
Lookup for illustrative analytical bands and explanatory text.

### `model_metrics.csv`
One row per official-test metric for the selected model.

### `feature_importance.csv`
One row per model feature, ranked by Random Forest importance.

## Completion gate

Phase 0B is complete only when:

- the runner executes without error;
- 100 training engines and 100 test engines are detected for FD001;
- `max_cycle` is absent from model inputs;
- validation engines do not overlap training engines;
- official test predictions exist for 100 unique engines;
- exported engine counts reconcile to source data;
- model metrics are regenerated from the repaired methodology;
- Power BI files have not yet been built from stale original metrics.
