"""
AquaWatt Machine Learning Pipeline: Electricity Consumption Forecasting.
Trains and evaluates baseline and ML models for daily household electricity consumption (kWh).
Strict chronological split:
- Train: Dec 16, 2006 to Dec 31, 2008 (complete days with valid lags)
- Validation: Jan 1, 2009 to Dec 31, 2009
- Test: Jan 1, 2010 to Nov 26, 2010
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, median_absolute_error

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "electricity", "electricity_daily_features.csv")
MODELS_DIR = os.path.join(BASE_DIR, "machine_learning", "models")
FIGURES_DIR = os.path.join(BASE_DIR, "machine_learning", "outputs", "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Selected features (past-only)
FEATURE_COLS = [
    "lag_1",
    "lag_7",
    "lag_30",
    "rolling_mean_7",
    "rolling_std_7",
    "rolling_mean_30",
    "day_of_week",
    "is_weekend",
    "month",
    "day_of_year",
]
TARGET_COL = "normalized_daily_kwh"


def calculate_metrics(y_true, y_pred):
    """Compute physical metrics: MAE, RMSE, R2, MedAE."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    medae = median_absolute_error(y_true, y_pred)
    return {
        "MAE_kwh": round(float(mae), 4),
        "RMSE_kwh": round(float(rmse), 4),
        "R2": round(float(r2), 4),
        "MedAE_kwh": round(float(medae), 4),
    }


def load_and_split_data():
    """Load electricity data and perform strict chronological split."""
    print(f"Loading electricity data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    
    # Filter to complete days for clean benchmark evaluation
    complete_df = df[df["is_complete_day"] == True].copy()
    
    # Chronological splits
    train_mask = (complete_df["date"] >= "2006-12-16") & (complete_df["date"] <= "2008-12-31")
    val_mask = (complete_df["date"] >= "2009-01-01") & (complete_df["date"] <= "2009-12-31")
    test_mask = (complete_df["date"] >= "2010-01-01") & (complete_df["date"] <= "2010-11-26")
    
    # Drop rows missing initial lags (cold start in train set)
    train_df = complete_df[train_mask].dropna(subset=FEATURE_COLS + [TARGET_COL]).copy()
    val_df = complete_df[val_mask].dropna(subset=FEATURE_COLS + [TARGET_COL]).copy()
    test_df = complete_df[test_mask].dropna(subset=FEATURE_COLS + [TARGET_COL]).copy()
    
    print(f"Train split: {train_df['date'].min().date()} to {train_df['date'].max().date()} ({len(train_df)} days)")
    print(f"Val split:   {val_df['date'].min().date()} to {val_df['date'].max().date()} ({len(val_df)} days)")
    print(f"Test split:  {test_df['date'].min().date()} to {test_df['date'].max().date()} ({len(test_df)} days)")
    
    X_train, y_train = train_df[FEATURE_COLS], train_df[TARGET_COL].values
    X_val, y_val = val_df[FEATURE_COLS], val_df[TARGET_COL].values
    X_test, y_test = test_df[FEATURE_COLS], test_df[TARGET_COL].values
    
    return (X_train, y_train, train_df), (X_val, y_val, val_df), (X_test, y_test, test_df)


def run_electricity_experiments():
    print("=" * 60)
    print("AQUAWATT PHASE 4: ELECTRICITY MODEL EXPERIMENTS")
    print("=" * 60)
    
    (X_train, y_train, train_df), (X_val, y_val, val_df), (X_test, y_test, test_df) = load_and_split_data()
    
    results = {}
    test_predictions = {}
    
    # -------------------------------------------------------------
    # 1. BASELINE MODELS
    # -------------------------------------------------------------
    print("\n--- Evaluating Baseline Models ---")
    # Persistence baseline: y_hat = lag_1 (yesterday)
    val_pred_persist = X_val["lag_1"].values
    test_pred_persist = X_test["lag_1"].values
    results["Baseline_Persistence"] = {
        "description": "Persistence Baseline: tomorrow = yesterday (lag_1)",
        "val_metrics": calculate_metrics(y_val, val_pred_persist),
        "test_metrics": calculate_metrics(y_test, test_pred_persist),
    }
    test_predictions["Baseline_Persistence"] = test_pred_persist
    print(f"Persistence Baseline -> Val MAE: {results['Baseline_Persistence']['val_metrics']['MAE_kwh']} kWh, Test MAE: {results['Baseline_Persistence']['test_metrics']['MAE_kwh']} kWh")
    
    # 7-day Moving Average baseline: y_hat = rolling_mean_7
    val_pred_ma7 = X_val["rolling_mean_7"].values
    test_pred_ma7 = X_test["rolling_mean_7"].values
    results["Baseline_7Day_MA"] = {
        "description": "7-Day Moving Average Baseline (rolling_mean_7)",
        "val_metrics": calculate_metrics(y_val, val_pred_ma7),
        "test_metrics": calculate_metrics(y_test, test_pred_ma7),
    }
    test_predictions["Baseline_7Day_MA"] = test_pred_ma7
    print(f"7-Day MA Baseline    -> Val MAE: {results['Baseline_7Day_MA']['val_metrics']['MAE_kwh']} kWh, Test MAE: {results['Baseline_7Day_MA']['test_metrics']['MAE_kwh']} kWh")
    
    # -------------------------------------------------------------
    # 2. RIDGE REGRESSION (with tuning on Validation set)
    # -------------------------------------------------------------
    print("\n--- Training Ridge Regression ---")
    best_alpha = 1.0
    best_ridge_val_mae = float("inf")
    best_ridge_pipe = None
    
    for alpha in [0.01, 0.1, 1.0, 10.0, 50.0, 100.0, 500.0]:
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=alpha, random_state=42))
        ])
        pipe.fit(X_train, y_train)
        v_pred = pipe.predict(X_val)
        v_mae = mean_absolute_error(y_val, v_pred)
        if v_mae < best_ridge_val_mae:
            best_ridge_val_mae = v_mae
            best_alpha = alpha
            best_ridge_pipe = pipe
            
    print(f"Tuned Ridge best alpha: {best_alpha} (Val MAE: {best_ridge_val_mae:.4f} kWh)")
    
    ridge_val_pred = best_ridge_pipe.predict(X_val)
    ridge_test_pred = best_ridge_pipe.predict(X_test)
    results["Ridge_Regression"] = {
        "description": f"Ridge Regression (alpha={best_alpha}, StandardScaler)",
        "val_metrics": calculate_metrics(y_val, ridge_val_pred),
        "test_metrics": calculate_metrics(y_test, ridge_test_pred),
        "best_hyperparameters": {"alpha": best_alpha}
    }
    test_predictions["Ridge_Regression"] = ridge_test_pred
    joblib.dump(best_ridge_pipe, os.path.join(MODELS_DIR, "electricity_ridge.joblib"))
    
    # -------------------------------------------------------------
    # 3. RANDOM FOREST REGRESSOR
    # -------------------------------------------------------------
    print("\n--- Training Random Forest Regressor ---")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    rf_val_pred = rf_model.predict(X_val)
    rf_test_pred = rf_model.predict(X_test)
    results["Random_Forest"] = {
        "description": "Random Forest Regressor (n_estimators=100, max_depth=8, min_samples_leaf=3)",
        "val_metrics": calculate_metrics(y_val, rf_val_pred),
        "test_metrics": calculate_metrics(y_test, rf_test_pred),
        "feature_importances": dict(zip(FEATURE_COLS, [round(float(v), 4) for v in rf_model.feature_importances_]))
    }
    test_predictions["Random_Forest"] = rf_test_pred
    joblib.dump(rf_model, os.path.join(MODELS_DIR, "electricity_rf.joblib"))
    print(f"Random Forest        -> Val MAE: {results['Random_Forest']['val_metrics']['MAE_kwh']} kWh, Test MAE: {results['Random_Forest']['test_metrics']['MAE_kwh']} kWh")
    
    # -------------------------------------------------------------
    # 4. GRADIENT BOOSTING REGRESSOR
    # -------------------------------------------------------------
    print("\n--- Training Gradient Boosting Regressor ---")
    gbr_model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        min_samples_leaf=3,
        random_state=42
    )
    gbr_model.fit(X_train, y_train)
    gbr_val_pred = gbr_model.predict(X_val)
    gbr_test_pred = gbr_model.predict(X_test)
    results["Gradient_Boosting"] = {
        "description": "Gradient Boosting Regressor (n_estimators=100, lr=0.05, max_depth=4)",
        "val_metrics": calculate_metrics(y_val, gbr_val_pred),
        "test_metrics": calculate_metrics(y_test, gbr_test_pred),
        "feature_importances": dict(zip(FEATURE_COLS, [round(float(v), 4) for v in gbr_model.feature_importances_]))
    }
    test_predictions["Gradient_Boosting"] = gbr_test_pred
    joblib.dump(gbr_model, os.path.join(MODELS_DIR, "electricity_gbr.joblib"))
    print(f"Gradient Boosting    -> Val MAE: {results['Gradient_Boosting']['val_metrics']['MAE_kwh']} kWh, Test MAE: {results['Gradient_Boosting']['test_metrics']['MAE_kwh']} kWh")
    
    # -------------------------------------------------------------
    # 5. SELECT BEST MODEL BASED ON VALIDATION MAE
    # -------------------------------------------------------------
    ml_candidates = ["Ridge_Regression", "Random_Forest", "Gradient_Boosting"]
    best_model_name = min(ml_candidates, key=lambda m: results[m]["val_metrics"]["MAE_kwh"])
    print(f"\n>>> Selected Best Electricity Model: {best_model_name} (Val MAE: {results[best_model_name]['val_metrics']['MAE_kwh']} kWh, Test MAE: {results[best_model_name]['test_metrics']['MAE_kwh']} kWh)")
    
    # Save best model copy
    if best_model_name == "Ridge_Regression":
        joblib.dump(best_ridge_pipe, os.path.join(MODELS_DIR, "electricity_best_model.joblib"))
    elif best_model_name == "Random_Forest":
        joblib.dump(rf_model, os.path.join(MODELS_DIR, "electricity_best_model.joblib"))
    else:
        joblib.dump(gbr_model, os.path.join(MODELS_DIR, "electricity_best_model.joblib"))
        
    results["selected_best_model"] = best_model_name
    
    # -------------------------------------------------------------
    # 6. PLOT ACTUAL VS PREDICTED & RESIDUALS ON TEST SET
    # -------------------------------------------------------------
    print("\nGenerating electricity actual-vs-predicted charts...")
    test_dates = test_df["date"].values
    
    # Figure 08: Actual vs Predicted Time Series
    plt.figure(figsize=(14, 6))
    plt.plot(test_dates, y_test, label="Actual Consumption", color="#1f77b4", linewidth=1.8, alpha=0.9)
    plt.plot(test_dates, test_predictions[best_model_name], label=f"Best Model ({best_model_name})", color="#2ca02c", linestyle="--", linewidth=1.5)
    plt.plot(test_dates, test_predictions["Baseline_Persistence"], label="Persistence Baseline", color="#d62728", linestyle=":", linewidth=1.2, alpha=0.7)
    plt.title(f"Electricity Forecasting (Test Set 2010): Actual vs {best_model_name}", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Date", fontsize=11)
    plt.ylabel("Daily Consumption (kWh)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    fig8_path = os.path.join(FIGURES_DIR, "08_electricity_actual_vs_predicted.png")
    plt.savefig(fig8_path, dpi=300)
    plt.close()
    print(f"Saved: {fig8_path}")
    
    # Figure 09: Model Residuals Distribution
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    best_residuals = y_test - test_predictions[best_model_name]
    persist_residuals = y_test - test_predictions["Baseline_Persistence"]
    sns.kdeplot(best_residuals, label=f"{best_model_name} (MAE: {results[best_model_name]['test_metrics']['MAE_kwh']})", color="#2ca02c", fill=True, alpha=0.3)
    sns.kdeplot(persist_residuals, label=f"Persistence (MAE: {results['Baseline_Persistence']['test_metrics']['MAE_kwh']})", color="#d62728", fill=True, alpha=0.2)
    plt.axvline(0, color="black", linestyle="--", linewidth=0.8)
    plt.title("Test Residual Error Distribution (y - y_hat)", fontsize=11, fontweight="bold")
    plt.xlabel("Prediction Error (kWh)", fontsize=10)
    plt.ylabel("Density", fontsize=10)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    
    plt.subplot(1, 2, 2)
    plt.scatter(y_test, test_predictions[best_model_name], alpha=0.5, color="#1f77b4", edgecolors="none", s=25)
    min_val = min(y_test.min(), test_predictions[best_model_name].min())
    max_val = max(y_test.max(), test_predictions[best_model_name].max())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=1.5, label="Ideal 1:1 Reference")
    plt.title(f"Predicted vs Actual Scatter ({best_model_name})", fontsize=11, fontweight="bold")
    plt.xlabel("Actual Consumption (kWh)", fontsize=10)
    plt.ylabel("Predicted Consumption (kWh)", fontsize=10)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    
    fig9_path = os.path.join(FIGURES_DIR, "09_electricity_model_residuals.png")
    plt.savefig(fig9_path, dpi=300)
    plt.close()
    print(f"Saved: {fig9_path}")
    
    return results


if __name__ == "__main__":
    res = run_electricity_experiments()
    print("\nElectricity Results Summary:\n", json.dumps(res, indent=2))

