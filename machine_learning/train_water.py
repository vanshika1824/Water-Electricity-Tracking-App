"""
AquaWatt Machine Learning Pipeline: Water Consumption Forecasting.
Trains and evaluates baseline and ML models for daily apartment-level water consumption (Litres).
Group-Aware Temporal Panel Split:
- Train: Jan 1, 2020 to Dec 31, 2021 (across all 28 apartments)
- Validation: Jan 1, 2022 to Jun 30, 2022 (across all 28 apartments)
- Test: Jul 1, 2022 to Jan 31, 2023 (across all 28 apartments)
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

from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, median_absolute_error

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "water", "water_daily_apartment_features.csv")
MODELS_DIR = os.path.join(BASE_DIR, "machine_learning", "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "machine_learning", "outputs")
FIGURES_DIR = os.path.join(OUTPUTS_DIR, "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

NUM_FEATURES = [
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
CAT_FEATURES = ["apartment", "cluster_name"]
ALL_FEATURES = NUM_FEATURES + CAT_FEATURES
TARGET_COL = "total_litres"


def calculate_metrics(y_true, y_pred):
    """Compute physical metrics: MAE, RMSE, R2, MedAE."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    medae = median_absolute_error(y_true, y_pred)
    return {
        "MAE_litres": round(float(mae), 4),
        "RMSE_litres": round(float(rmse), 4),
        "R2": round(float(r2), 4),
        "MedAE_litres": round(float(medae), 4),
    }


def load_and_split_data():
    """Load water features and perform group-aware temporal panel split."""
    print(f"Loading water dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    
    # Filter to monitored days with valid lags and target
    valid_df = df[df["is_monitored_building_day"] & df[TARGET_COL].notna()].dropna(subset=NUM_FEATURES).copy()
    
    # Temporal panel splits
    train_mask = (valid_df["date"] >= "2020-01-01") & (valid_df["date"] <= "2021-12-31")
    val_mask = (valid_df["date"] >= "2022-01-01") & (valid_df["date"] <= "2022-06-30")
    test_mask = (valid_df["date"] >= "2022-07-01") & (valid_df["date"] <= "2023-01-31")
    
    train_df = valid_df[train_mask].copy()
    val_df = valid_df[val_mask].copy()
    test_df = valid_df[test_mask].copy()
    
    print(f"Train split: {train_df['date'].min().date()} to {train_df['date'].max().date()} ({len(train_df):,} rows across {train_df['apartment'].nunique()} apts)")
    print(f"Val split:   {val_df['date'].min().date()} to {val_df['date'].max().date()} ({len(val_df):,} rows across {val_df['apartment'].nunique()} apts)")
    print(f"Test split:  {test_df['date'].min().date()} to {test_df['date'].max().date()} ({len(test_df):,} rows across {test_df['apartment'].nunique()} apts)")
    
    return train_df, val_df, test_df


def run_water_experiments():
    print("=" * 60)
    print("AQUAWATT PHASE 4: WATER MODEL EXPERIMENTS")
    print("=" * 60)
    
    train_df, val_df, test_df = load_and_split_data()
    
    X_train, y_train = train_df[ALL_FEATURES], train_df[TARGET_COL].values
    X_val, y_val = val_df[ALL_FEATURES], val_df[TARGET_COL].values
    X_test, y_test = test_df[ALL_FEATURES], test_df[TARGET_COL].values
    
    results = {}
    test_predictions = {}
    
    # -------------------------------------------------------------
    # 1. BASELINE MODELS
    # -------------------------------------------------------------
    print("\n--- Evaluating Baseline Models ---")
    # Persistence: tomorrow = yesterday (lag_1)
    val_pred_persist = X_val["lag_1"].values
    test_pred_persist = X_test["lag_1"].values
    results["Baseline_Persistence"] = {
        "description": "Persistence Baseline: tomorrow = yesterday (lag_1)",
        "val_metrics": calculate_metrics(y_val, val_pred_persist),
        "test_metrics": calculate_metrics(y_test, test_pred_persist),
    }
    test_predictions["Baseline_Persistence"] = test_pred_persist
    print(f"Persistence Baseline -> Val MAE: {results['Baseline_Persistence']['val_metrics']['MAE_litres']} L, Test MAE: {results['Baseline_Persistence']['test_metrics']['MAE_litres']} L")
    
    # 7-Day Moving Average
    val_pred_ma7 = X_val["rolling_mean_7"].values
    test_pred_ma7 = X_test["rolling_mean_7"].values
    results["Baseline_7Day_MA"] = {
        "description": "7-Day Moving Average Baseline (rolling_mean_7)",
        "val_metrics": calculate_metrics(y_val, val_pred_ma7),
        "test_metrics": calculate_metrics(y_test, test_pred_ma7),
    }
    test_predictions["Baseline_7Day_MA"] = test_pred_ma7
    print(f"7-Day MA Baseline    -> Val MAE: {results['Baseline_7Day_MA']['val_metrics']['MAE_litres']} L, Test MAE: {results['Baseline_7Day_MA']['test_metrics']['MAE_litres']} L")
    
    # -------------------------------------------------------------
    # 2. RIDGE REGRESSION
    # -------------------------------------------------------------
    print("\n--- Training Ridge Regression ---")
    preprocessor_ridge = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUM_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CAT_FEATURES),
        ]
    )
    
    best_alpha = 100.0
    best_ridge_val_mae = float("inf")
    best_ridge_pipe = None
    
    for alpha in [1.0, 10.0, 50.0, 100.0, 250.0, 500.0, 1000.0]:
        pipe = Pipeline([
            ("preprocessor", preprocessor_ridge),
            ("ridge", Ridge(alpha=alpha, random_state=42))
        ])
        pipe.fit(X_train, y_train)
        v_pred = pipe.predict(X_val)
        v_mae = mean_absolute_error(y_val, v_pred)
        if v_mae < best_ridge_val_mae:
            best_ridge_val_mae = v_mae
            best_alpha = alpha
            best_ridge_pipe = pipe
            
    print(f"Tuned Ridge best alpha: {best_alpha} (Val MAE: {best_ridge_val_mae:.4f} L)")
    
    ridge_val_pred = best_ridge_pipe.predict(X_val)
    ridge_test_pred = best_ridge_pipe.predict(X_test)
    results["Ridge_Regression"] = {
        "description": f"Ridge Regression (alpha={best_alpha}, StandardScaler, OneHotEncoder)",
        "val_metrics": calculate_metrics(y_val, ridge_val_pred),
        "test_metrics": calculate_metrics(y_test, ridge_test_pred),
        "best_hyperparameters": {"alpha": best_alpha}
    }
    test_predictions["Ridge_Regression"] = ridge_test_pred
    joblib.dump(best_ridge_pipe, os.path.join(MODELS_DIR, "water_ridge.joblib"))
    
    # -------------------------------------------------------------
    # 3. RANDOM FOREST REGRESSOR
    # -------------------------------------------------------------
    print("\n--- Training Random Forest Regressor ---")
    preprocessor_rf = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUM_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
        ]
    )
    rf_pipe = Pipeline([
        ("preprocessor", preprocessor_rf),
        ("rf", RandomForestRegressor(n_estimators=100, max_depth=12, min_samples_leaf=5, n_jobs=-1, random_state=42))
    ])
    rf_pipe.fit(X_train, y_train)
    rf_val_pred = rf_pipe.predict(X_val)
    rf_test_pred = rf_pipe.predict(X_test)
    results["Random_Forest"] = {
        "description": "Random Forest Regressor (n_estimators=100, max_depth=12, min_samples_leaf=5)",
        "val_metrics": calculate_metrics(y_val, rf_val_pred),
        "test_metrics": calculate_metrics(y_test, rf_test_pred),
    }
    test_predictions["Random_Forest"] = rf_test_pred
    joblib.dump(rf_pipe, os.path.join(MODELS_DIR, "water_rf.joblib"))
    print(f"Random Forest        -> Val MAE: {results['Random_Forest']['val_metrics']['MAE_litres']} L, Test MAE: {results['Random_Forest']['test_metrics']['MAE_litres']} L")
    
    # -------------------------------------------------------------
    # 4. HIST GRADIENT BOOSTING REGRESSOR
    # -------------------------------------------------------------
    print("\n--- Training HistGradientBoosting Regressor ---")
    # HistGradientBoosting handles categoricals natively with OrdinalEncoder
    preprocessor_hgb = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUM_FEATURES),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CAT_FEATURES),
        ]
    )
    cat_indices = [len(NUM_FEATURES), len(NUM_FEATURES) + 1]
    
    hgb_pipe = Pipeline([
        ("preprocessor", preprocessor_hgb),
        ("hgb", HistGradientBoostingRegressor(
            categorical_features=cat_indices,
            max_iter=100,
            learning_rate=0.05,
            max_depth=8,
            min_samples_leaf=15,
            random_state=42
        ))
    ])
    hgb_pipe.fit(X_train, y_train)
    hgb_val_pred = hgb_pipe.predict(X_val)
    hgb_test_pred = hgb_pipe.predict(X_test)
    results["HistGradientBoosting"] = {
        "description": "HistGradientBoosting Regressor (max_iter=100, lr=0.05, max_depth=8, min_samples_leaf=15)",
        "val_metrics": calculate_metrics(y_val, hgb_val_pred),
        "test_metrics": calculate_metrics(y_test, hgb_test_pred),
    }
    test_predictions["HistGradientBoosting"] = hgb_test_pred
    joblib.dump(hgb_pipe, os.path.join(MODELS_DIR, "water_hist_gbr.joblib"))
    print(f"HistGradientBoosting -> Val MAE: {results['HistGradientBoosting']['val_metrics']['MAE_litres']} L, Test MAE: {results['HistGradientBoosting']['test_metrics']['MAE_litres']} L")
    
    # -------------------------------------------------------------
    # 5. SELECT BEST MODEL BASED ON VALIDATION MAE
    # -------------------------------------------------------------
    ml_candidates = ["Ridge_Regression", "Random_Forest", "HistGradientBoosting"]
    best_model_name = min(ml_candidates, key=lambda m: results[m]["val_metrics"]["MAE_litres"])
    print(f"\n>>> Selected Best Water Model: {best_model_name} (Val MAE: {results[best_model_name]['val_metrics']['MAE_litres']} L, Test MAE: {results[best_model_name]['test_metrics']['MAE_litres']} L)")
    
    if best_model_name == "Ridge_Regression":
        joblib.dump(best_ridge_pipe, os.path.join(MODELS_DIR, "water_best_model.joblib"))
    elif best_model_name == "Random_Forest":
        joblib.dump(rf_pipe, os.path.join(MODELS_DIR, "water_best_model.joblib"))
    else:
        joblib.dump(hgb_pipe, os.path.join(MODELS_DIR, "water_best_model.joblib"))
        
    results["selected_best_model"] = best_model_name
    
    # -------------------------------------------------------------
    # 6. PER-APARTMENT EVALUATION ON TEST SET
    # -------------------------------------------------------------
    print("\nComputing per-apartment evaluation across all 28 apartments on Test set...")
    test_eval_df = test_df.copy()
    test_eval_df["y_true"] = y_test
    test_eval_df["pred_persist"] = test_predictions["Baseline_Persistence"]
    test_eval_df["pred_ma7"] = test_predictions["Baseline_7Day_MA"]
    test_eval_df["pred_ridge"] = test_predictions["Ridge_Regression"]
    test_eval_df["pred_rf"] = test_predictions["Random_Forest"]
    test_eval_df["pred_hgb"] = test_predictions["HistGradientBoosting"]
    test_eval_df["pred_best"] = test_predictions[best_model_name]
    
    apt_rows = []
    for apt, grp in test_eval_df.groupby("apartment"):
        mae_persist = mean_absolute_error(grp["y_true"], grp["pred_persist"])
        mae_ma7 = mean_absolute_error(grp["y_true"], grp["pred_ma7"])
        mae_ridge = mean_absolute_error(grp["y_true"], grp["pred_ridge"])
        mae_rf = mean_absolute_error(grp["y_true"], grp["pred_rf"])
        mae_hgb = mean_absolute_error(grp["y_true"], grp["pred_hgb"])
        mae_best = mean_absolute_error(grp["y_true"], grp["pred_best"])
        
        # Improvement relative to persistence (%)
        pct_imp = ((mae_persist - mae_best) / mae_persist) * 100.0 if mae_persist > 0 else 0.0
        
        apt_rows.append({
            "apartment": apt,
            "cluster_name": grp["cluster_name"].iloc[0],
            "test_days": len(grp),
            "mean_actual_litres": round(float(grp["y_true"].mean()), 2),
            "mae_persistence": round(float(mae_persist), 2),
            "mae_7day_ma": round(float(mae_ma7), 2),
            "mae_ridge": round(float(mae_ridge), 2),
            "mae_rf": round(float(mae_rf), 2),
            "mae_hist_gbr": round(float(mae_hgb), 2),
            "mae_best_model": round(float(mae_best), 2),
            "improvement_pct_over_persistence": round(float(pct_imp), 2)
        })
        
    per_apt_metrics_df = pd.DataFrame(apt_rows).sort_values("apartment").reset_index(drop=True)
    per_apt_csv_path = os.path.join(OUTPUTS_DIR, "water_per_apartment_metrics.csv")
    per_apt_metrics_df.to_csv(per_apt_csv_path, index=False)
    print(f"Saved per-apartment evaluation metrics to: {per_apt_csv_path}")
    
    # -------------------------------------------------------------
    # 7. VISUALIZATIONS
    # -------------------------------------------------------------
    print("\nGenerating water actual-vs-predicted and per-apartment charts...")
    # Figure 10: Pooled Actual vs Predicted Scatter and Residuals
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.scatter(y_test, test_predictions[best_model_name], alpha=0.3, color="#1f77b4", edgecolors="none", s=20)
    plt.plot([0, 1000], [0, 1000], "r--", linewidth=1.5, label="Ideal 1:1 Line")
    plt.xlim(-10, 1000)
    plt.ylim(-10, 1000)
    plt.title(f"Water Test Set: Predicted vs Actual ({best_model_name})", fontsize=11, fontweight="bold")
    plt.xlabel("Actual Consumption (Litres)", fontsize=10)
    plt.ylabel("Predicted Consumption (Litres)", fontsize=10)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    
    plt.subplot(1, 2, 2)
    residuals = y_test - test_predictions[best_model_name]
    persist_res = y_test - test_predictions["Baseline_Persistence"]
    sns.kdeplot(residuals, label=f"{best_model_name} (MAE: {results[best_model_name]['test_metrics']['MAE_litres']} L)", color="#2ca02c", fill=True, alpha=0.3)
    sns.kdeplot(persist_res, label=f"Persistence (MAE: {results['Baseline_Persistence']['test_metrics']['MAE_litres']} L)", color="#d62728", fill=True, alpha=0.2)
    plt.xlim(-250, 250)
    plt.axvline(0, color="black", linestyle="--", linewidth=0.8)
    plt.title("Test Residual Error Distribution (y - y_hat)", fontsize=11, fontweight="bold")
    plt.xlabel("Prediction Error (Litres)", fontsize=10)
    plt.ylabel("Density", fontsize=10)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    
    fig10_path = os.path.join(FIGURES_DIR, "10_water_actual_vs_predicted_pooled.png")
    plt.savefig(fig10_path, dpi=300)
    plt.close()
    print(f"Saved: {fig10_path}")
    
    # Figure 11: Per-Apartment MAE Bar Chart Comparison
    plt.figure(figsize=(15, 6))
    x_indices = np.arange(len(per_apt_metrics_df))
    width = 0.38
    
    plt.bar(x_indices - width/2, per_apt_metrics_df["mae_persistence"], width=width, label="Persistence Baseline", color="#d62728", alpha=0.85)
    plt.bar(x_indices + width/2, per_apt_metrics_df["mae_best_model"], width=width, label=f"Best Model ({best_model_name})", color="#2ca02c", alpha=0.85)
    
    plt.xticks(x_indices, per_apt_metrics_df["apartment"], rotation=45, ha="right", fontsize=9)
    plt.ylabel("Mean Absolute Error (Litres)", fontsize=11)
    plt.title("Per-Apartment Water Forecast Performance: Best Model vs Persistence Baseline (Test Set)", fontsize=13, fontweight="bold", pad=12)
    plt.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    
    fig11_path = os.path.join(FIGURES_DIR, "11_water_per_apartment_mae_comparison.png")
    plt.savefig(fig11_path, dpi=300)
    plt.close()
    print(f"Saved: {fig11_path}")
    
    return results, per_apt_metrics_df


if __name__ == "__main__":
    res, per_apt_df = run_water_experiments()
    print("\nWater Results Summary:\n", json.dumps(res, indent=2))

