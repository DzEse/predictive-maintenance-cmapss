# Power BI Semantic Model — Phase 1

## Purpose

This document defines the semantic model for the **Aircraft Fleet Predictive Maintenance Intelligence** Power BI report. It uses only the repaired Phase 0B outputs and preserves the difference between engine-level snapshots and engine-cycle history.

The model supports the report sequence:

**OVERVIEW → PRIORITIZE → DIAGNOSE → VALIDATE → ACT**

The report is a portfolio decision-support simulation using NASA C-MAPSS FD001 research data. It is not an operational or certified aviation-maintenance system.

---

## 1. Import these six Power BI tables

From `data/powerbi/` import:

1. `fact_engine_snapshot.csv`
2. `fact_engine_cycle.csv`
3. `dim_engine.csv`
4. `dim_risk_band.csv`
5. `model_metrics.csv`
6. `feature_importance.csv`

Do not import `model_validation_comparison.csv` into the production report model unless it is deliberately added later for a methodology appendix. It is development evidence rather than a core reporting table.

---

## 2. Table roles and grain

### `fact_engine_snapshot`
**Grain:** one row per official FD001 test engine at its latest observed cycle.

Use for:
- executive fleet counts;
- latest predicted RUL;
- latest analytical risk band;
- prioritization;
- final-snapshot model error analysis;
- actual-vs-predicted scatter.

Expected row count: **100**.

### `fact_engine_cycle`
**Grain:** one row per engine per observed operating cycle.

Use for:
- RUL trajectories;
- degradation analysis;
- sensor trends;
- cycle-level diagnostic exploration.

Do not use this table for executive engine-count KPIs.

### `dim_engine`
**Grain:** one row per engine.

Use as the shared engine dimension and engine slicer source.

Expected row count: **100**.

### `dim_risk_band`
**Grain:** one row per illustrative analytical band.

Use for:
- consistent band labels;
- sort order;
- explanatory definitions;
- shared risk-band filtering.

The bands are portfolio-created analytical categories, not certified maintenance limits.

### `model_metrics`
**Grain:** one row per official-test metric for the selected model.

Keep disconnected from the engine fact tables.

### `feature_importance`
**Grain:** one row per selected model feature.

Keep disconnected from the engine fact tables.

---

## 3. Power Query data types

### `dim_engine`
| Column | Type |
|---|---|
| `unit` | Whole Number |
| `engine_label` | Text |

### `dim_risk_band`
| Column | Type |
|---|---|
| `risk_band_key` | Whole Number |
| `risk_band` | Text |
| `min_predicted_rul` | Decimal Number |
| `max_predicted_rul` | Decimal Number |
| `sort_order` | Whole Number |
| `meaning` | Text |

### `fact_engine_snapshot`
| Column | Type |
|---|---|
| `unit` | Whole Number |
| `cycle` | Whole Number |
| `actual_rul` | Decimal Number |
| `predicted_rul` | Decimal Number |
| `prediction_error` | Decimal Number |
| `absolute_error` | Decimal Number |
| `risk_band_key` | Whole Number |
| `risk_band` | Text |

### `fact_engine_cycle`
Use:
- `unit`, `cycle`, `last_observed_cycle`, `risk_band_key` → **Whole Number**;
- `risk_band` → **Text**;
- all RUL, error, operating-setting, sensor, rolling, lag and difference fields → **Decimal Number**.

### `model_metrics`
| Column | Type |
|---|---|
| `model_name` | Text |
| `evaluation_scope` | Text |
| `metric` | Text |
| `value` | Decimal Number |
| `unit` | Text |

### `feature_importance`
| Column | Type |
|---|---|
| `importance_rank` | Whole Number |
| `feature` | Text |
| `importance` | Decimal Number |

---

## 4. Relationships

Create these four active relationships:

```text
dim_engine[unit]        1 ───── * fact_engine_snapshot[unit]
dim_engine[unit]        1 ───── * fact_engine_cycle[unit]

dim_risk_band[risk_band_key] 1 ───── * fact_engine_snapshot[risk_band_key]
dim_risk_band[risk_band_key] 1 ───── * fact_engine_cycle[risk_band_key]
```

For every relationship:
- cardinality: **One-to-many (1:*)**;
- cross-filter direction: **Single**;
- relationship: **Active**;
- filter direction should run from the dimension table to the fact table.

Do not create relationships from `model_metrics` or `feature_importance` to the fact tables.

---

## 5. Model-view layout

Arrange the model visually as:

```text
                 dim_engine
                /          \
               v            v
 fact_engine_snapshot    fact_engine_cycle
               ^            ^
                \          /
               dim_risk_band

 model_metrics          feature_importance
   [disconnected]         [disconnected]
```

This makes the grain distinction obvious during an interview.

---

## 6. Field hygiene

After relationships are validated:

- hide `fact_engine_snapshot[unit]` and use `dim_engine[unit]` / `dim_engine[engine_label]` in visuals;
- hide `fact_engine_cycle[unit]` for the same reason;
- hide duplicated fact-table `risk_band` fields and use `dim_risk_band[risk_band]` in slicers and categories;
- keep `risk_band_key` hidden from report users;
- keep technical fields available in the model where they support diagnostics, but do not expose every sensor on executive pages.

Sort `dim_risk_band[risk_band]` by `dim_risk_band[sort_order]`.

---

## 7. Core DAX measures

Create a dedicated measure table named `Measures` and place report measures there.

### Fleet measures

```DAX
Engines Monitored =
DISTINCTCOUNT ( fact_engine_snapshot[unit] )
```

```DAX
Priority Review Engines =
CALCULATE (
    [Engines Monitored],
    dim_risk_band[risk_band] = "PRIORITY REVIEW"
)
```

```DAX
Monitor Engines =
CALCULATE (
    [Engines Monitored],
    dim_risk_band[risk_band] = "MONITOR"
)
```

```DAX
Lower Priority Engines =
CALCULATE (
    [Engines Monitored],
    dim_risk_band[risk_band] = "LOWER PRIORITY"
)
```

```DAX
Fleet At Risk % =
DIVIDE (
    [Priority Review Engines] + [Monitor Engines],
    [Engines Monitored]
)
```

`Fleet At Risk %` is an analytical portfolio measure, not a probability of certified maintenance risk.

```DAX
Average Predicted RUL =
AVERAGE ( fact_engine_snapshot[predicted_rul] )
```

```DAX
Median Predicted RUL =
MEDIAN ( fact_engine_snapshot[predicted_rul] )
```

```DAX
Average Actual RUL =
AVERAGE ( fact_engine_snapshot[actual_rul] )
```

```DAX
Average Absolute Error =
AVERAGE ( fact_engine_snapshot[absolute_error] )
```

```DAX
Snapshot Mean Error Bias =
AVERAGE ( fact_engine_snapshot[prediction_error] )
```

Because `prediction_error = actual_rul - predicted_rul`, a negative value indicates average optimism: the prediction exceeds actual RUL.

### Official model-metric measures

```DAX
Model MAE =
CALCULATE (
    MAX ( model_metrics[value] ),
    model_metrics[metric] = "MAE"
)
```

```DAX
Model RMSE =
CALCULATE (
    MAX ( model_metrics[value] ),
    model_metrics[metric] = "RMSE"
)
```

```DAX
Model R2 =
CALCULATE (
    MAX ( model_metrics[value] ),
    model_metrics[metric] = "R2"
)
```

```DAX
Model Mean Error Bias =
CALCULATE (
    MAX ( model_metrics[value] ),
    model_metrics[metric] = "Mean Error Bias"
)
```

```DAX
Within 10 Cycles % =
CALCULATE (
    MAX ( model_metrics[value] ),
    model_metrics[metric] = "Within ±10 Cycles"
) / 100
```

```DAX
Within 20 Cycles % =
CALCULATE (
    MAX ( model_metrics[value] ),
    model_metrics[metric] = "Within ±20 Cycles"
) / 100
```

```DAX
Within 30 Cycles % =
CALCULATE (
    MAX ( model_metrics[value] ),
    model_metrics[metric] = "Within ±30 Cycles"
) / 100
```

---

## 8. Measure formatting

Recommended formats:

- engine counts → whole number;
- RUL and error measures → one decimal place;
- `Fleet At Risk %`, within-cycle measures → percentage, one decimal place;
- MAE / RMSE / bias → one or two decimals;
- R² → three decimals;
- feature importance → percentage or decimal consistently across the visual.

---

## 9. Model QA gates

Before building report pages, verify all of the following:

1. `fact_engine_snapshot` contains **100 rows**.
2. `dim_engine` contains **100 rows**.
3. `[Engines Monitored]` returns **100** with no slicers applied.
4. `[Model MAE]` returns approximately **19.8483**.
5. `[Model RMSE]` returns approximately **26.4641**.
6. `[Model R2]` returns approximately **0.5944**.
7. `[Model Mean Error Bias]` returns approximately **-9.7227**.
8. `[Within 10 Cycles %]` returns **37%**.
9. `[Within 20 Cycles %]` returns **60%**.
10. `[Within 30 Cycles %]` returns **74%**.
11. `Priority Review Engines + Monitor Engines + Lower Priority Engines = Engines Monitored`.
12. Selecting one engine in `dim_engine` filters both fact tables.
13. Selecting one risk band filters both fact tables.
14. `model_metrics` and `feature_importance` remain unaffected by engine slicers unless a deliberate visual interaction is configured.

Do not move to page design if the row counts, relationships, or official metrics do not reconcile.

---

## 10. Interview explanation

A concise explanation of the model:

> I separated the reporting layer into two fact grains. The snapshot fact has exactly one latest record per engine and drives fleet KPIs and prioritization, while the cycle fact contains the complete observed trajectory and drives degradation analysis. Shared engine and risk-band dimensions filter both facts using one-to-many, single-direction relationships. Model metrics and feature importance remain disconnected because they describe the analytical model rather than individual engines. This prevents cycle rows from inflating fleet counts and keeps the semantic model aligned with the business questions.
