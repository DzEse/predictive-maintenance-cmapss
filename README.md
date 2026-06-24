# Predictive Maintenance for Aircraft Engines (NASA CMAPSS FD001)

## Project Overview

This project builds an end-to-end **predictive maintenance system** for aircraft engines using the NASA CMAPSS FD001 dataset.  
The goal is to predict the **Remaining Useful Life (RUL)** of engines and convert predictions into actionable maintenance decisions.

The system simulates a real-world industrial workflow used in aerospace engineering for condition-based maintenance and failure prevention.

---

## Problem Statement

Aircraft engines degrade over time due to operational stress.  
The challenge is to accurately estimate how many operational cycles remain before failure occurs, allowing maintenance teams to act proactively rather than reactively.

---

## Workflow

1. Data Loading (NASA CMAPSS FD001)
2. Data Cleaning & Structuring
3. Remaining Useful Life (RUL) Calculation
4. Feature Engineering
   - Rolling mean features
   - Sensor trend features
   - Cycle-based degradation indicators
5. Train-Test Split (no data leakage)
6. Model Training (Random Forest Regressor)
7. Model Evaluation (MAE, RMSE, R²)
8. Feature Importance Analysis
9. Risk-Based Classification System

---

## Machine Learning Model

- Algorithm: Random Forest Regressor  
- Target Variable: Remaining Useful Life (RUL)  
- Input Features: Sensor readings + engineered degradation features  

---

## Model Performance

- **MAE:** 20.40 cycles  
- **RMSE:** 27.68 cycles  
- **R² Score:** 0.8323  

The model explains **83% of variance** in engine degradation behavior.

---

## Fleet Risk Classification

The model classifies engines into operational states:

- **Healthy:** 75.65%  
- **Warning:** 12.02%  
- **Critical:** 12.33%  

This enables proactive maintenance planning.

---

## Key Insights

- Sensor trend features (rolling mean) are the strongest predictors of degradation.
- Engine lifecycle progression plays a significant role in failure prediction.
- The model is most accurate for **critical engines**, which is ideal for safety applications.
- Prediction errors are primarily driven by a small number of high-variance outliers.

---

## Business Impact

- Reduces unexpected engine failures
- Enables condition-based maintenance scheduling
- Improves fleet availability and operational safety
- Optimizes maintenance costs by prioritizing high-risk engines

---

## Tech Stack

- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib

---

## Future Improvements

- Hyperparameter tuning (GridSearchCV)
- XGBoost / LightGBM comparison
- SHAP explainability analysis
- Real-time deployment pipeline
- Time-series deep learning (LSTM models)

---

## Conclusion

This project demonstrates a complete predictive maintenance pipeline from raw sensor data to actionable maintenance decisions.  
It simulates a real-world aerospace monitoring system capable of supporting operational decision-making.

---

