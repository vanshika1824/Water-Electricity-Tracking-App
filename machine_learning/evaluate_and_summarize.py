"""
AquaWatt Phase 4: Model Performance Evaluator & Visualizer.
Aggregates electricity and water model metrics into a unified JSON and produces
Figure 12: Comprehensive Benchmark Performance Summary.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUTS_DIR = os.path.join(BASE_DIR, "machine_learning", "outputs")
FIGURES_DIR = os.path.join(OUTPUTS_DIR, "figures")

from train_electricity import run_electricity_experiments
from train_water import run_water_experiments


def main():
    print("=" * 60)
    print("RUNNING COMPLETE PHASE 4 EVALUATION & METRIC CONSOLIDATION")
    print("=" * 60)
    
    ele_res = run_electricity_experiments()
    wat_res, per_apt_df = run_water_experiments()
    
    full_metrics = {
        "metadata": {
            "date": "2026-11-15",
            "phase": "Phase 4 - Machine Learning Model Development",
            "electricity_task": "Daily household active energy consumption forecasting (kWh)",
            "water_task": "Daily apartment-level water consumption forecasting (Litres)",
            "leakage_protection": "Strict chronological out-of-time splits with verified past-only calendar-day lags"
        },
        "electricity": ele_res,
        "water": wat_res
    }
    
    metrics_json_path = os.path.join(OUTPUTS_DIR, "model_metrics.json")
    with open(metrics_json_path, "w") as f:
        json.dump(full_metrics, f, indent=2)
    print(f"\nSaved consolidated metrics JSON to: {metrics_json_path}")
    
    # ------------------------------------------------------------------
    # GENERATE FIGURE 12: MODEL PERFORMANCE SUMMARY BAR CHARTS
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    
    # Left: Electricity MAE on Test Set (2010)
    ele_models = ["Baseline_Persistence", "Baseline_7Day_MA", "Ridge_Regression", "Random_Forest", "Gradient_Boosting"]
    ele_labels = ["Persistence", "7-Day MA", "Ridge", "Random Forest", "Gradient Boost"]
    ele_maes = [ele_res[m]["test_metrics"]["MAE_kwh"] for m in ele_models]
    ele_colors = ["#d62728", "#ff7f0e", "#1f77b4", "#2ca02c", "#9467bd"]
    
    bars1 = axes[0].bar(ele_labels, ele_maes, color=ele_colors, width=0.55, edgecolor="black", linewidth=0.8)
    axes[0].set_title("Electricity Forecasting: Test Set MAE (kWh/day)", fontsize=12, fontweight="bold", pad=10)
    axes[0].set_ylabel("Mean Absolute Error (kWh)", fontsize=11)
    axes[0].grid(True, axis="y", linestyle="--", alpha=0.5)
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    axes[0].set_ylim(0, max(ele_maes) * 1.2)
    
    # Right: Water MAE on Test Set (Jul 2022 - Jan 2023)
    wat_models = ["Baseline_Persistence", "Baseline_7Day_MA", "Ridge_Regression", "HistGradientBoosting", "Random_Forest"]
    wat_labels = ["Persistence", "7-Day MA", "Ridge", "HistGBR", "Random Forest"]
    wat_maes = [wat_res[m]["test_metrics"]["MAE_litres"] for m in wat_models]
    wat_colors = ["#d62728", "#ff7f0e", "#1f77b4", "#9467bd", "#2ca02c"]
    
    bars2 = axes[1].bar(wat_labels, wat_maes, color=wat_colors, width=0.55, edgecolor="black", linewidth=0.8)
    axes[1].set_title("Water Forecasting: Test Set MAE (Litres/day)", fontsize=12, fontweight="bold", pad=10)
    axes[1].set_ylabel("Mean Absolute Error (Litres)", fontsize=11)
    axes[1].grid(True, axis="y", linestyle="--", alpha=0.5)
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2.0, yval + 0.6, f"{yval:.1f} L", ha="center", va="bottom", fontsize=10, fontweight="bold")
    axes[1].set_ylim(0, max(wat_maes) * 1.2)
    
    plt.suptitle("AquaWatt Phase 4: Model Performance vs Heuristic Baselines (Out-of-Time Test Sets)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    
    fig12_path = os.path.join(FIGURES_DIR, "12_model_performance_summary.png")
    plt.savefig(fig12_path, dpi=300)
    plt.close()
    print(f"Saved Figure 12 to: {fig12_path}")


if __name__ == "__main__":
    main()

