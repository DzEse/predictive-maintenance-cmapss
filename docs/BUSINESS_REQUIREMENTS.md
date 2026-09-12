# Aircraft Fleet Predictive Maintenance Intelligence — Business Requirements

## 1. Project purpose

Translate a technically valid NASA C-MAPSS FD001 Remaining Useful Life workflow into a Power BI decision-support experience that demonstrates how analytics can help an operations or maintenance-planning audience move from fleet status to prioritization, diagnosis, model validation, and analytical follow-up.

This is a portfolio simulation using NASA research data. It is **not** a deployed airline maintenance system, and its analytical risk bands are not certified maintenance limits.

## 2. Business narrative

The report follows this decision sequence:

**OVERVIEW → PRIORITIZE → DIAGNOSE → VALIDATE → ACT**

Every major page or visual should answer four questions:

**QUESTION → EVIDENCE → INSIGHT → DECISION**

The intended portfolio story is:

> During experience in aerospace electronics and technical manufacturing environments, I became interested in how operational data could support earlier identification of equipment deterioration. This project explores that question using NASA's simulated C-MAPSS turbofan-engine degradation dataset. The analytical workflow estimates Remaining Useful Life for previously unseen simulated engine trajectories, then translates those outputs into a Power BI decision-support report for fleet monitoring, engine prioritization, degradation analysis, and model-performance assessment.

## 3. Intended audiences

### Executive / operations manager
Needs a rapid fleet-level view: how many engines are monitored, how many fall into each analytical priority band, and whether attention is concentrated in a small subset of assets.

### Maintenance planner
Needs a ranked worklist of engines that deserve analytical review first, supported by predicted RUL, latest observed cycle, and risk-band context.

### Reliability / technical analyst
Needs trajectory-level evidence: how RUL and selected sensor signals change over operating cycles and how an individual engine reached its current analytical state.

### Data / analytics recruiter or hiring manager
Needs evidence that the project is not only a model notebook: the candidate can define business questions, control data grain, build a semantic model, calculate KPIs correctly, communicate limitations, and translate model output into decisions.

## 4. Data scope

The Power BI report will use only outputs created by the repaired Phase 0B pipeline.

Primary tables:

- `fact_engine_snapshot` — one row per official FD001 test engine at its latest observed cycle;
- `fact_engine_cycle` — one row per engine per observed cycle;
- `dim_engine` — one row per engine;
- `dim_risk_band` — analytical risk-band metadata;
- `model_metrics` — official NASA test metrics for the selected model;
- `feature_importance` — Random Forest feature-importance ranking.

The report must not use the original leakage-prone notebook metrics.

## 5. Core business questions

1. What is the latest analytical condition of the monitored fleet?
2. Which engines deserve analytical review first?
3. How much predicted useful life remains for each engine?
4. How concentrated is the fleet in lower-RUL analytical bands?
5. What degradation pattern led an individual engine to its latest condition?
6. Which sensor or operating variables are most influential in the selected model?
7. How accurate is the model on the separate NASA test fleet?
8. Does the model show systematic optimism or pessimism?
9. How much uncertainty should decision-makers keep in mind when using the predictions?
10. What should an analyst or planner investigate next, without presenting the dashboard as an automated maintenance authority?

## 6. KPI definitions

### Engines Monitored
Distinct engine count from `fact_engine_snapshot`. Expected portfolio value: 100.

### Priority Review Engines
Distinct engine count whose latest snapshot is in the illustrative `PRIORITY REVIEW` band.

### Monitor Engines
Distinct engine count whose latest snapshot is in the illustrative `MONITOR` band.

### Lower Priority Engines
Distinct engine count whose latest snapshot is in the illustrative `LOWER PRIORITY` band.

### Fleet At Risk %
Percentage of monitored engines in `PRIORITY REVIEW` or `MONITOR`. This is a portfolio analytical measure, not a certified maintenance-risk probability.

### Average Predicted RUL
Average latest-snapshot predicted RUL across the selected engine population.

### Median Predicted RUL
Median latest-snapshot predicted RUL. Included because RUL distributions can be skewed and a mean alone can be misleading.

### Model MAE
Official test final-snapshot MAE from `model_metrics`.

### Model RMSE
Official test final-snapshot RMSE from `model_metrics`.

### Model R²
Official test final-snapshot R² from `model_metrics`.

### Mean Error Bias
Average `actual_rul - predicted_rul`. Negative values indicate the model is optimistic on average because predicted RUL exceeds actual RUL.

## 7. Report pages

### Page 1 — Fleet Executive Overview
**Question:** What is the latest condition of the monitored fleet?

Required content:
- Engines Monitored
- Priority Review Engines
- Monitor Engines
- Lower Priority Engines
- Average Predicted RUL
- Fleet At Risk %
- latest-state risk-band distribution
- predicted-RUL distribution
- concise explanatory text describing the simulated-data and analytical-band limitations

Decision outcome: identify whether the fleet has a concentrated lower-RUL group requiring deeper review.

### Page 2 — Maintenance Priority
**Question:** Which engines deserve analytical review first?

Required content:
- ranked engine table
- Engine ID
- latest observed cycle
- predicted RUL
- analytical risk band
- actual RUL available for evaluation transparency
- absolute error available as a model-quality field, not as a real-world operational input
- filters for risk band and RUL range

Decision outcome: create a transparent analytical review queue rather than a prescriptive maintenance schedule.

### Page 3 — Engine Degradation Analysis
**Question:** What patterns led an engine toward its latest state?

Required content:
- single-engine selector
- predicted RUL by cycle
- actual RUL by cycle for evaluation context
- selected sensor trends by cycle
- Sensor 2 rolling/lag context where useful for explanation
- current/latest-state summary card

Decision outcome: move from fleet-level prioritization into asset-level diagnostic exploration.

### Page 4 — Model Performance & Explainability
**Question:** How reliable are the predictions and what influences them?

Required content:
- MAE
- RMSE
- R²
- Mean Error Bias
- within-10/20/30-cycle performance
- Actual vs Predicted scatter
- error distribution
- feature-importance ranking
- explicit note that the Sensor 2 temporal feature experiment did not outperform the baseline specification

Decision outcome: help the audience understand model quality, uncertainty, bias, and limitations before relying on prediction outputs.

### Page 5 — Decision Support
**Question:** What should the analytical audience investigate next?

Required content:
- prioritized analytical findings
- count/share of engines in review bands
- engines with the lowest predicted RUL
- engines with the largest model error
- model-bias statement
- limitations and next-step guidance

Decision outcome: convert analysis into a short, defensible follow-up agenda without presenting the report as an autonomous maintenance authority.

## 8. Semantic-model requirements

- `dim_engine[unit]` must have a one-to-many relationship to both fact tables.
- `dim_risk_band[risk_band_key]` must relate to the fact tables where appropriate.
- Cross-filter direction should remain single-direction unless a clear business need justifies otherwise.
- Executive engine-count measures must use `fact_engine_snapshot`, not `fact_engine_cycle`.
- Historical cycle analysis must use `fact_engine_cycle`.
- Model metrics and feature importance are analytical support tables and should not create ambiguous relationships to the engine facts.

## 9. Visual-design requirements

- Keep the report professional and restrained; avoid decorative visuals that do not answer a business question.
- Use consistent page titles, navigation, spacing, typography, and analytical-band labels.
- Every chart title should communicate the question or insight, not merely the chart type.
- Tooltips should expose useful context without overwhelming the main canvas.
- Avoid gauges unless they add information unavailable from a clearer KPI/card/bar visual.
- Do not use 3D charts.
- Avoid red/amber/green language that implies certified aviation severity unless explanatory context makes the illustrative nature explicit.

## 10. Governance and limitation statements

The final report must make the following clear:

- C-MAPSS FD001 is simulated research data, not live airline telemetry.
- The project is a portfolio decision-support simulation, not an operational aviation-maintenance system.
- Predictions contain error and uncertainty.
- The selected model shows an optimistic mean bias on the official test snapshots and this must not be hidden.
- Analytical risk bands are portfolio-created thresholds and not OEM, airline, regulator, or certified engineering limits.
- Real maintenance decisions require engineering judgment, approved procedures, safety controls, and regulatory/organizational authority.

## 11. Acceptance criteria

Phase 1 business definition is complete when:

- every report page has a named audience question and decision outcome;
- engine-level KPIs use the one-row-per-engine snapshot grain;
- cycle-level visuals use the engine-cycle grain;
- all model-performance claims use the repaired Phase 0B results;
- the negative Sensor 2 feature-engineering result is represented accurately;
- risk bands are clearly labelled illustrative;
- no visual, text box, or KPI claims real-world deployment, certified maintenance authority, or unsupported ROI;
- the semantic model can be explained clearly in an interview.
