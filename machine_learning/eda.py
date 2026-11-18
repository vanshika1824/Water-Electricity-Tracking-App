"""
AquaWatt Exploratory Data Analysis (EDA) Script.
Generates comprehensive statistical summaries and publication-quality figures
for UCI Electricity and HSB Living Lab Water datasets.
Outputs are saved in machine_learning/outputs/figures/
"""

import os
import json
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Directory setup
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_ELE_DIR = os.path.join(BASE_DIR, "data", "processed", "electricity")
PROCESSED_WAT_DIR = os.path.join(BASE_DIR, "data", "processed", "water")
FIGURES_DIR = os.path.join(BASE_DIR, "machine_learning", "outputs", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# Styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
COLOR_TEAL = "#064E5A"
COLOR_AQUA = "#39D5D0"
COLOR_CORAL = "#E06D53"
COLOR_GOLD = "#F4A261"
COLOR_NAVY = "#083D4A"


def run_electricity_eda() -> dict:
    print("\n" + "=" * 60)
    print("RUNNING ELECTRICITY EXPLORATORY DATA ANALYSIS")
    print("=" * 60)
    daily_path = os.path.join(PROCESSED_ELE_DIR, "electricity_daily.csv")
    monthly_path = os.path.join(PROCESSED_ELE_DIR, "electricity_monthly.csv")
    
    df_daily = pd.read_csv(daily_path)
    df_daily["date"] = pd.to_datetime(df_daily["date"])
    df_monthly = pd.read_csv(monthly_path)
    
    # Statistical analysis on complete days
    complete = df_daily[df_daily["is_complete_day"] == True].copy()
    val = complete["normalized_daily_kwh"]
    
    stats_ele = {
        "dataset": "UCI Individual Household Electric Power Consumption",
        "total_days": len(df_daily),
        "complete_days": len(complete),
        "mean_daily_kwh": round(float(val.mean()), 3),
        "std_daily_kwh": round(float(val.std()), 3),
        "median_daily_kwh": round(float(val.median()), 3),
        "min_daily_kwh": round(float(val.min()), 3),
        "max_daily_kwh": round(float(val.max()), 3),
        "q25_daily_kwh": round(float(val.quantile(0.25)), 3),
        "q75_daily_kwh": round(float(val.quantile(0.75)), 3),
        "total_period_kwh": round(float(complete["total_active_kwh"].sum()), 2),
        "submetering_shares": {
            "sub1_kitchen_pct": round(float(complete["sub1_kitchen_kwh"].sum() / complete["total_active_kwh"].sum()) * 100, 2),
            "sub2_laundry_pct": round(float(complete["sub2_laundry_kwh"].sum() / complete["total_active_kwh"].sum()) * 100, 2),
            "sub3_ac_geyser_pct": round(float(complete["sub3_ac_geyser_kwh"].sum() / complete["total_active_kwh"].sum()) * 100, 2),
            "other_unmetered_pct": round(float(complete["other_kwh"].sum() / complete["total_active_kwh"].sum()) * 100, 2)
        }
    }
    print(f"Electricity Daily Mean: {stats_ele['mean_daily_kwh']} kWh (Median: {stats_ele['median_daily_kwh']} kWh)")
    print(f"Sub-metering shares: {stats_ele['submetering_shares']}")

    # FIGURE 1: Daily Consumption Trend over Time
    fig, ax = plt.subplots(figsize=(13, 5), dpi=300)
    ax.plot(complete["date"], complete["normalized_daily_kwh"], color=COLOR_TEAL, alpha=0.6, linewidth=1, label="Daily Total (kWh)")
    # 30-day moving average
    complete["ma30"] = complete["normalized_daily_kwh"].rolling(30, center=True).mean()
    ax.plot(complete["date"], complete["ma30"], color=COLOR_CORAL, linewidth=2.2, label="30-Day Moving Average")
    ax.set_title("UCI Individual Household Electricity Consumption (Dec 2006 – Nov 2010)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Daily Electricity Consumption (kWh)", fontsize=11)
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    f1_path = os.path.join(FIGURES_DIR, "01_electricity_daily_trend.png")
    fig.savefig(f1_path)
    plt.close(fig)
    print(f"Saved: {f1_path}")

    # FIGURE 2: Day-of-Week and Monthly Seasonality Profiles
    complete["day_name"] = complete["date"].dt.day_name()
    complete["month"] = complete["date"].dt.month
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    # Day of Week
    sns.barplot(data=complete, x="day_name", y="normalized_daily_kwh", order=dow_order, ax=ax1, color=COLOR_TEAL, errorbar="se")
    ax1.set_title("Average Electricity Consumption by Day of Week", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Day of Week", fontsize=10)
    ax1.set_ylabel("Mean Daily kWh", fontsize=10)
    ax1.tick_params(axis="x", rotation=30)
    
    # Month of Year
    monthly_mean = complete.groupby("month")["normalized_daily_kwh"].mean().reset_index()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    sns.barplot(data=monthly_mean, x="month", y="normalized_daily_kwh", ax=ax2, color=COLOR_CORAL)
    ax2.set_xticks(range(12))
    ax2.set_xticklabels(month_names)
    ax2.set_title("Monthly Seasonality (Winter Heating vs Summer)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Calendar Month", fontsize=10)
    ax2.set_ylabel("Mean Daily kWh", fontsize=10)
    plt.tight_layout()
    f2_path = os.path.join(FIGURES_DIR, "02_electricity_weekly_monthly_profile.png")
    fig.savefig(f2_path)
    plt.close(fig)
    print(f"Saved: {f2_path}")

    # FIGURE 3: Sub-Metering Contributions Breakdown
    fig, (ax_pie, ax_box) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    shares = stats_ele["submetering_shares"]
    labels = [
        f"Sub 3: AC / Water Heater\n({shares['sub3_ac_geyser_pct']}%)",
        f"Sub 2: Laundry & Fridge\n({shares['sub2_laundry_pct']}%)",
        f"Sub 1: Kitchen\n({shares['sub1_kitchen_pct']}%)",
        f"Other / Outlets / Lights\n({shares['other_unmetered_pct']}%)"
    ]
    sizes = [
        shares["sub3_ac_geyser_pct"],
        shares["sub2_laundry_pct"],
        shares["sub1_kitchen_pct"],
        shares["other_unmetered_pct"]
    ]
    colors = [COLOR_CORAL, COLOR_AQUA, COLOR_GOLD, COLOR_NAVY]
    ax_pie.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140, explode=(0.04, 0.04, 0.04, 0.04))
    ax_pie.set_title("Sub-Metering Breakdown of Total Household Energy", fontsize=12, fontweight="bold")
    
    # Distribution of daily total kWh
    sns.histplot(complete["normalized_daily_kwh"], kde=True, ax=ax_box, color=COLOR_TEAL, bins=40)
    ax_box.axvline(stats_ele["median_daily_kwh"], color=COLOR_CORAL, linestyle="--", linewidth=2, label=f"Median ({stats_ele['median_daily_kwh']} kWh)")
    ax_box.axvline(stats_ele["mean_daily_kwh"], color=COLOR_GOLD, linestyle="-.", linewidth=2, label=f"Mean ({stats_ele['mean_daily_kwh']} kWh)")
    ax_box.set_title("Distribution of Daily Electricity Consumption", fontsize=12, fontweight="bold")
    ax_box.set_xlabel("Daily Energy (kWh)", fontsize=10)
    ax_box.set_ylabel("Frequency (Days)", fontsize=10)
    ax_box.legend()
    plt.tight_layout()
    f3_path = os.path.join(FIGURES_DIR, "03_electricity_submetering_distribution.png")
    fig.savefig(f3_path)
    plt.close(fig)
    print(f"Saved: {f3_path}")
    
    return stats_ele


def run_water_eda() -> dict:
    print("\n" + "=" * 60)
    print("RUNNING WATER EXPLORATORY DATA ANALYSIS")
    print("=" * 60)
    daily_apt_path = os.path.join(PROCESSED_WAT_DIR, "water_daily_by_apartment.csv")
    daily_bldg_path = os.path.join(PROCESSED_WAT_DIR, "water_daily_building.csv")
    
    df_apt = pd.read_csv(daily_apt_path)
    df_apt["date"] = pd.to_datetime(df_apt["date"])
    df_bldg = pd.read_csv(daily_bldg_path)
    df_bldg["date"] = pd.to_datetime(df_bldg["date"])
    
    val_apt = df_apt["total_litres"]
    val_bldg = df_bldg["total_litres"]
    
    # Sum fixture totals across all apartment-days
    tot_water = df_apt["total_litres"].sum()
    shower_tot = df_apt["shower_litres"].sum()
    tap_tot = df_apt["kitchen_litres"].sum()
    basin_tot = df_apt["washbasin_litres"].sum()
    toilet_tot = df_apt["toilet_litres"].sum()
    laundry_tot = df_apt["laundry_and_dish_litres"].sum()
    other_tot = tot_water - (shower_tot + tap_tot + basin_tot + toilet_tot + laundry_tot)
    
    stats_wat = {
        "dataset": "HSB Living Lab Fixture-Level Household Water Dataset",
        "total_monitored_days": len(df_bldg),
        "total_apartment_days": len(df_apt),
        "monitored_apartments": int(df_apt["apartment"].nunique()),
        "apartment_daily_mean_litres": round(float(val_apt.mean()), 2),
        "apartment_daily_median_litres": round(float(val_apt.median()), 2),
        "apartment_daily_min_litres": round(float(val_apt.min()), 2),
        "apartment_daily_max_litres": round(float(val_apt.max()), 2),
        "building_daily_mean_litres": round(float(val_bldg.mean()), 2),
        "building_daily_median_litres": round(float(val_bldg.median()), 2),
        "building_total_period_m3": round(float(df_bldg["total_m3"].sum()), 3),
        "fixture_shares": {
            "shower_pct": round(float(shower_tot / tot_water) * 100, 2),
            "washbasin_pct": round(float(basin_tot / tot_water) * 100, 2),
            "kitchen_tap_pct": round(float(tap_tot / tot_water) * 100, 2),
            "toilet_pct": round(float(toilet_tot / tot_water) * 100, 2),
            "laundry_dish_pct": round(float(laundry_tot / tot_water) * 100, 2),
            "other_pct": round(float(max(0, other_tot) / tot_water) * 100, 2)
        }
    }
    print(f"Water Apartment Daily Mean: {stats_wat['apartment_daily_mean_litres']} L (Median: {stats_wat['apartment_daily_median_litres']} L)")
    print(f"Building Daily Mean: {stats_wat['building_daily_mean_litres']} L (~{stats_wat['building_total_period_m3']} m3 total)")
    print(f"Fixture Shares: {stats_wat['fixture_shares']}")

    # FIGURE 4: Building-Wide Water Consumption Trend
    fig, ax = plt.subplots(figsize=(13, 5), dpi=300)
    ax.plot(df_bldg["date"], df_bldg["total_litres"], color="#088395", alpha=0.55, linewidth=1, label="Daily Building Total (Litres)")
    df_bldg["ma30"] = df_bldg["total_litres"].rolling(30, center=True).mean()
    ax.plot(df_bldg["date"], df_bldg["ma30"], color=COLOR_CORAL, linewidth=2.2, label="30-Day Moving Average")
    ax.set_title("HSB Living Lab Total Building Water Consumption (Dec 2019 – Jan 2023)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Daily Consumption (Litres/day)", fontsize=11)
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    f4_path = os.path.join(FIGURES_DIR, "04_water_daily_trend_building.png")
    fig.savefig(f4_path)
    plt.close(fig)
    print(f"Saved: {f4_path}")

    # FIGURE 5: Fixture-Wise Water Consumption Distribution
    fig, (ax_pie, ax_bar) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    f_shares = stats_wat["fixture_shares"]
    labels = [
        f"Showers ({f_shares['shower_pct']}%)",
        f"Washbasins ({f_shares['washbasin_pct']}%)",
        f"Kitchen Taps ({f_shares['kitchen_tap_pct']}%)",
        f"Toilets ({f_shares['toilet_pct']}%)",
        f"Laundry/Dish ({f_shares['laundry_dish_pct']}%)",
        f"Other ({f_shares['other_pct']}%)"
    ]
    sizes = [
        f_shares["shower_pct"],
        f_shares["washbasin_pct"],
        f_shares["kitchen_tap_pct"],
        f_shares["toilet_pct"],
        f_shares["laundry_dish_pct"],
        f_shares["other_pct"]
    ]
    colors = ["#0077B6", "#0096C7", "#00B4D8", "#48CAE4", "#90E0EF", "#ADE8F4"]
    ax_pie.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=120, explode=(0.04, 0.04, 0.04, 0.04, 0.04, 0.04))
    ax_pie.set_title("Domestic End-Use Water Consumption by Fixture Type", fontsize=12, fontweight="bold")
    
    # Average daily volume by fixture
    fixture_means = pd.Series({
        "Showers": shower_tot / len(df_apt),
        "Washbasins": basin_tot / len(df_apt),
        "Kitchen Taps": tap_tot / len(df_apt),
        "Toilets": toilet_tot / len(df_apt),
        "Laundry/Dish": laundry_tot / len(df_apt)
    }).sort_values(ascending=True)
    fixture_means.plot(kind="barh", ax=ax_bar, color=COLOR_TEAL)
    ax_bar.set_title("Mean Daily Consumption per Monitored Apartment (Litres)", fontsize=12, fontweight="bold")
    ax_bar.set_xlabel("Mean Litres per Day", fontsize=10)
    for i, v in enumerate(fixture_means):
        ax_bar.text(v + 1, i, f"{v:.1f} L", va="center", fontsize=10, fontweight="bold", color=COLOR_NAVY)
    plt.tight_layout()
    f5_path = os.path.join(FIGURES_DIR, "05_water_fixture_distribution.png")
    fig.savefig(f5_path)
    plt.close(fig)
    print(f"Saved: {f5_path}")

    # FIGURE 6: Cross-Apartment Variation (28 Units)
    fig, ax = plt.subplots(figsize=(14, 5.5), dpi=300)
    apt_means = df_apt.groupby("apartment")["total_litres"].mean().sort_values(ascending=False)
    # Color communal clusters vs conventional
    sns.barplot(x=apt_means.index, y=apt_means.values, ax=ax, color=COLOR_TEAL)
    ax.axhline(val_apt.mean(), color=COLOR_CORAL, linestyle="--", linewidth=2, label=f"Cohort Average ({val_apt.mean():.1f} L/day)")
    ax.set_title("Mean Daily Water Consumption Across 28 Anonymized Apartments", fontsize=13, fontweight="bold")
    ax.set_xlabel("Apartment Identifier (Randomized)", fontsize=10)
    ax.set_ylabel("Mean Daily Consumption (Litres)", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    plt.tight_layout()
    f6_path = os.path.join(FIGURES_DIR, "06_water_apartment_comparison.png")
    fig.savefig(f6_path)
    plt.close(fig)
    print(f"Saved: {f6_path}")

    # FIGURE 7: Day of Week Water Profiles
    df_apt["day_name"] = df_apt["date"].dt.day_name()
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    sns.barplot(data=df_apt, x="day_name", y="total_litres", order=dow_order, ax=ax, color="#0096C7", errorbar="se")
    ax.set_title("Apartment Water Consumption by Day of Week", fontsize=12, fontweight="bold")
    ax.set_xlabel("Day of Week", fontsize=10)
    ax.set_ylabel("Mean Daily Litres per Apartment", fontsize=10)
    plt.tight_layout()
    f7_path = os.path.join(FIGURES_DIR, "07_water_weekly_profile.png")
    fig.savefig(f7_path)
    plt.close(fig)
    print(f"Saved: {f7_path}")

    return stats_wat


def main():
    print("=" * 60)
    print("AQUAWATT PHASE 3: EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 60)
    ele_stats = run_electricity_eda()
    wat_stats = run_water_eda()
    
    summary_path = os.path.join(BASE_DIR, "machine_learning", "outputs", "eda_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"electricity": ele_stats, "water": wat_stats}, f, indent=2)
    print(f"\nSaved complete EDA summary to: {summary_path}")


if __name__ == "__main__":
    main()

