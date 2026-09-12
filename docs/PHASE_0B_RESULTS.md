# Phase 0B — Validated Results

## Status

**PASS**

The leakage-safe FD001 runner completed successfully on the professional rebuild branch.

## Source reconciliation

The repository-root `train_FD001.txt` and the newly downloaded NASA source copy produced different raw SHA-256 hashes because the Windows checkout used different line endings. After normalizing CRLF/LF line endings, the files matched exactly.

## Source population

| Dataset | Rows | Engines |
|---|---:|---:|
| Training (`train_FD001`) | 20,631 | 100 |
| Official test (`test_FD001`) | 13,096 | 100 |

## Development validation

Validation was performed with whole engine trajectories held out. Eighty engines were used for development and twenty engines for validation.

| Specification | Features | MAE | RMSE | R² | Mean error bias | Within 10 | Within 20 | Within 30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_raw_available` | 18 | 23.8255 | 31.3805 | 0.7715 | -5.1406 | 36.19% | 52.75% | 64.59% |
| `enhanced_sensor2_temporal` | 21 | 23.9891 | 31.4902 | 0.7699 | -4.8720 | 35.72% | 52.24% | 64.23% |

### Selection decision

`baseline_raw_available` was selected because it produced the lower held-out validation MAE and RMSE. The experiment therefore does **not** support a claim that the Sensor 2 rolling/lag/difference features improve predictive performance in this configuration.

This negative result is retained because it is analytically useful: engineered features should be justified by measured performance rather than assumed to be beneficial.

## Official NASA test results

The selected specification was refit on all 100 training engines and evaluated on the final observed snapshot of each of the 100 separate NASA FD001 test engines.

| Metric | Result |
|---|---:|
| MAE | 19.8483 cycles |
| RMSE | 26.4641 cycles |
| R² | 0.5944 |
| Mean signed error (`actual - predicted`) | -9.7227 cycles |
| Predictions within 10 cycles | 37.00% |
| Predictions within 20 cycles | 60.00% |
| Predictions within 30 cycles | 74.00% |

## Interpretation

The repaired evaluation is intentionally more conservative than the original notebook. The previous headline score must not be used in the final portfolio because it came from a methodology with future-information leakage and row-level train/test mixing.

The mean signed error is negative because the metric is calculated as `actual_rul - predicted_rul`. A negative value therefore means the model **over-predicts remaining useful life on average**. On the official final-engine snapshots, the average optimistic bias is approximately 9.7 cycles. This should be visible in the model-performance page because it is operationally more meaningful than reporting R² alone.

The model is suitable as a defensible portfolio baseline for decision-support visualization. It is not presented as a certified maintenance model, a deployed airline system, or a safety-critical decision engine.

## Power BI analytical outputs

The validated run produced:

- `fact_engine_cycle.csv` — 13,096 engine-cycle observations for degradation analysis;
- `fact_engine_snapshot.csv` — exactly one latest-state row for each of the 100 official test engines;
- `dim_engine.csv` — engine lookup;
- `dim_risk_band.csv` — illustrative analytical risk-band definitions;
- `model_metrics.csv` — official-test metrics;
- `feature_importance.csv` — selected Random Forest feature importance;
- `model_validation_comparison.csv` — development/validation benchmark results.

## Phase gate

Phase 0B is closed as **PASS**. Power BI design may proceed using only the repaired outputs and the newly generated metrics.
