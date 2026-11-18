"""
AquaWatt Machine Learning Preprocessing Pipeline.
Processes UCI Electricity and HSB Living Lab Water benchmark datasets:
- Cleans and transparently handles missing values
- Resamples to verified daily and monthly consumption figures (kWh and Litres)
- Computes leak-free temporal, lag, and rolling features for future ML
- Prepares auditable outputs in data/processed/ without modifying data/raw/
"""

import os
import sys
import time
import numpy as np
import pandas as pd

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_ELE_FILE = os.path.join(BASE_DIR, "data", "extracted", "electricity", "household_power_consumption.txt")
RAW_WAT_FILE = os.path.join(BASE_DIR, "data", "extracted", "water", "HSB_Living_Lab_Water_Consumption_Anonymized.csv")

PROCESSED_ELE_DIR = os.path.join(BASE_DIR, "data", "processed", "electricity")
PROCESSED_WAT_DIR = os.path.join(BASE_DIR, "data", "processed", "water")


def ensure_dirs():
    os.makedirs(PROCESSED_ELE_DIR, exist_ok=True)
    os.makedirs(PROCESSED_WAT_DIR, exist_ok=True)


def safe_save(df: pd.DataFrame, csv_path: str, parquet_path: str = None):
    """Save dataframe to CSV reliably, and optionally Parquet if engine is supported."""
    df.to_csv(csv_path, index=False)
    if parquet_path:
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception as e:
            # Silently fallback to CSV if DLL policy blocks pyarrow C-extension
            pass


# ==============================================================================
# FEATURE ENGINEERING HELPER FUNCTIONS
# ==============================================================================

def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add calendar features without any target leakage."""
    out = df.copy()
    dt = pd.to_datetime(out[date_col])
    out["day_of_week"] = dt.dt.day_of_week
    out["day_name"] = dt.dt.day_name()
    out["month"] = dt.dt.month
    out["day_of_year"] = dt.dt.day_of_year
    out["is_weekend"] = dt.dt.day_of_week.isin([5, 6]).astype(int)
    
    # Astronomical/meteorological northern hemisphere seasons
    def get_season(m):
        if m in [12, 1, 2]:
            return "Winter"
        elif m in [3, 4, 5]:
            return "Spring"
        elif m in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"
    out["season"] = dt.dt.month.apply(get_season)
    return out


def add_lag_and_rolling_features(
    df: pd.DataFrame,
    target_col: str,
    date_col: str = "date",
    group_col: str = None
) -> pd.DataFrame:
    """
    Construct shifted lag features and rolling averages.
    CRITICAL: Uses shift(1) so current time t is strictly excluded from rolling windows.
    If group_col is given, features are computed independently within each entity.
    """
    out = df.copy()
    if group_col:
        out = out.sort_values([group_col, date_col]).reset_index(drop=True)
        g = out.groupby(group_col)[target_col]
        out["lag_1"] = g.shift(1)
        out["lag_7"] = g.shift(7)
        out["lag_30"] = g.shift(30)
        out["rolling_mean_7"] = g.transform(lambda s: s.shift(1).rolling(7, min_periods=3).mean())
        out["rolling_std_7"] = g.transform(lambda s: s.shift(1).rolling(7, min_periods=3).std())
        out["rolling_mean_30"] = g.transform(lambda s: s.shift(1).rolling(30, min_periods=10).mean())
    else:
        out = out.sort_values(date_col).reset_index(drop=True)
        s = out[target_col]
        out["lag_1"] = s.shift(1)
        out["lag_7"] = s.shift(7)
        out["lag_30"] = s.shift(30)
        out["rolling_mean_7"] = s.shift(1).rolling(7, min_periods=3).mean()
        out["rolling_std_7"] = s.shift(1).rolling(7, min_periods=3).std()
        out["rolling_mean_30"] = s.shift(1).rolling(30, min_periods=10).mean()
    return out


# ==============================================================================
# ELECTRICITY PREPROCESSING
# ==============================================================================

def preprocess_electricity():
    """
    Preprocess UCI Individual Household Electric Power Consumption:
    1. Parse 2,075,259 minute-level records.
    2. Transparently track missing values (marked as '?').
    3. Calculate Energy (kWh) = Global_active_power (kW) * (1/60).
    4. Convert sub-metering Watt-hours to kWh.
    5. Aggregate to daily and monthly series with coverage tracking.
    6. Generate future ML features with zero leakage.
    """
    print("\n" + "=" * 60)
    print("STARTING ELECTRICITY PREPROCESSING (UCI Benchmark)")
    print("=" * 60)
    t0 = time.time()
    
    print(f"Reading raw electricity file: {RAW_ELE_FILE}")
    df = pd.read_csv(
        RAW_ELE_FILE,
        sep=";",
        na_values=["?", ""],
        dtype={
            "Date": str,
            "Time": str,
            "Global_active_power": float,
            "Global_reactive_power": float,
            "Voltage": float,
            "Global_intensity": float,
            "Sub_metering_1": float,
            "Sub_metering_2": float,
            "Sub_metering_3": float,
        }
    )
    total_raw_rows = len(df)
    print(f"Total raw records loaded: {total_raw_rows:,}")
    
    # 1. Parse Datetime
    print("Parsing date and time into datetime index...")
    df["datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S")
    df["date"] = df["datetime"].dt.date
    
    # 2. Check duplicates
    dup_count = df["datetime"].duplicated().sum()
    print(f"Duplicate timestamps found: {dup_count}")
    if dup_count > 0:
        df = df.drop_duplicates(subset=["datetime"], keep="first")
        print(f"Removed duplicates, remaining: {len(df):,}")
    
    # 3. Missing values analysis
    missing_active = df["Global_active_power"].isna().sum()
    pct_missing = (missing_active / total_raw_rows) * 100
    print(f"Missing Global_active_power values: {missing_active:,} ({pct_missing:.2f}%)")
    
    # 4. Energy Conversion (Minute kW to kWh)
    # Energy in 1 minute = kW * (1/60 hour)
    df["active_energy_kwh"] = df["Global_active_power"] / 60.0
    # Sub-metering is in Wh. To convert to kWh: Wh / 1000
    df["sub1_kwh"] = df["Sub_metering_1"] / 1000.0
    df["sub2_kwh"] = df["Sub_metering_2"] / 1000.0
    df["sub3_kwh"] = df["Sub_metering_3"] / 1000.0
    
    # Unmetered remainder (lights, wall electronics)
    sub_sum = df["sub1_kwh"].fillna(0) + df["sub2_kwh"].fillna(0) + df["sub3_kwh"].fillna(0)
    df["other_kwh"] = np.maximum(0.0, df["active_energy_kwh"].fillna(0) - sub_sum)
    
    # 5. Daily Aggregation
    print("Aggregating minute data to daily consumption...")
    daily_stats = df.groupby("date").agg(
        valid_minutes=("Global_active_power", "count"),
        total_active_kwh=("active_energy_kwh", "sum"),
        sub1_kitchen_kwh=("sub1_kwh", "sum"),
        sub2_laundry_kwh=("sub2_kwh", "sum"),
        sub3_ac_geyser_kwh=("sub3_kwh", "sum"),
        other_kwh=("other_kwh", "sum"),
        avg_voltage=("Voltage", "mean"),
        avg_active_power_kw=("Global_active_power", "mean"),
        max_active_power_kw=("Global_active_power", "max")
    ).reset_index()
    
    daily_stats["expected_minutes"] = 1440
    daily_stats["coverage_ratio"] = daily_stats["valid_minutes"] / 1440.0
    
    # Completeness flag: at least 95% valid minutes in the day (1,368+ minutes)
    daily_stats["is_complete_day"] = daily_stats["coverage_ratio"] >= 0.95
    
    # Scaled consumption for complete days: proportionally scale minor missing intervals
    daily_stats["normalized_daily_kwh"] = np.where(
        daily_stats["is_complete_day"],
        daily_stats["total_active_kwh"] / daily_stats["coverage_ratio"],
        daily_stats["total_active_kwh"]
    )
    
    total_days = len(daily_stats)
    complete_days = int(daily_stats["is_complete_day"].sum())
    print(f"Total days processed: {total_days:,}")
    print(f"Complete days (>= 95% coverage): {complete_days:,} ({(complete_days / total_days)*100:.1f}%)")
    print(f"Incomplete/partial days: {total_days - complete_days}")
    
    # 6. Monthly Aggregation
    print("Aggregating to monthly consumption...")
    daily_stats["date_dt"] = pd.to_datetime(daily_stats["date"])
    daily_stats["year_month"] = daily_stats["date_dt"].dt.to_period("M").astype(str)
    
    monthly_stats = daily_stats.groupby("year_month").agg(
        total_days=("date", "count"),
        complete_days=("is_complete_day", "sum"),
        total_kwh=("total_active_kwh", "sum"),
        sub1_kitchen_kwh=("sub1_kitchen_kwh", "sum"),
        sub2_laundry_kwh=("sub2_laundry_kwh", "sum"),
        sub3_ac_geyser_kwh=("sub3_ac_geyser_kwh", "sum"),
        other_kwh=("other_kwh", "sum"),
        avg_daily_kwh=("total_active_kwh", "mean")
    ).reset_index()
    monthly_stats["coverage_pct"] = (monthly_stats["complete_days"] / monthly_stats["total_days"]) * 100.0
    print(f"Total calendar months processed: {len(monthly_stats)}")
    
    # 7. Add ML Features to Daily Data
    print("Generating zero-leakage ML features for daily electricity...")
    daily_with_cal = add_calendar_features(daily_stats, date_col="date")
    daily_ml = add_lag_and_rolling_features(
        daily_with_cal,
        target_col="normalized_daily_kwh",
        date_col="date"
    )
    
    # Drop intermediate date_dt
    if "date_dt" in daily_ml.columns:
        daily_ml = daily_ml.drop(columns=["date_dt"])
    if "date_dt" in daily_stats.columns:
        daily_stats = daily_stats.drop(columns=["date_dt"])
        
    # 8. Save Processed Outputs
    p_daily_csv = os.path.join(PROCESSED_ELE_DIR, "electricity_daily.csv")
    p_daily_parquet = os.path.join(PROCESSED_ELE_DIR, "electricity_daily.parquet")
    p_monthly_csv = os.path.join(PROCESSED_ELE_DIR, "electricity_monthly.csv")
    p_monthly_parquet = os.path.join(PROCESSED_ELE_DIR, "electricity_monthly.parquet")
    p_features_csv = os.path.join(PROCESSED_ELE_DIR, "electricity_daily_features.csv")
    p_features_parquet = os.path.join(PROCESSED_ELE_DIR, "electricity_daily_features.parquet")
    
    safe_save(daily_stats, p_daily_csv, p_daily_parquet)
    safe_save(monthly_stats, p_monthly_csv, p_monthly_parquet)
    safe_save(daily_ml, p_features_csv, p_features_parquet)
    
    elapsed = time.time() - t0
    print(f"Electricity preprocessing completed in {elapsed:.2f}s.")
    print(f"Saved: {p_daily_csv} ({os.path.getsize(p_daily_csv) / 1024:.1f} KB)")
    print(f"Saved: {p_monthly_csv} ({os.path.getsize(p_monthly_csv) / 1024:.1f} KB)")
    print(f"Saved: {p_features_csv} ({os.path.getsize(p_features_csv) / 1024:.1f} KB)")
    
    return {
        "raw_records": total_raw_rows,
        "missing_active": int(missing_active),
        "total_days": total_days,
        "complete_days": complete_days,
        "total_months": len(monthly_stats),
        "daily_features_shape": list(daily_ml.shape)
    }


# ==============================================================================
# WATER PREPROCESSING
# ==============================================================================

def preprocess_water():
    """
    Preprocess HSB Living Lab Water Consumption:
    1. Parse 652,315 10-minute records across 28 apartments.
    2. Confirm correct consumption column is 'value' (m3).
    3. Exclude 'aggregated_value' from summing to prevent double-counting.
    4. Filter sensor outliers (value > 0.3 m3) and zero-value records.
    5. Convert m3 to Litres: Litres = value * 1000.
    6. Aggregate daily consumption by apartment and fixture type.
    7. Aggregate building-wide daily and monthly statistics.
    8. Construct group-aware lag and rolling features per apartment.
    """
    print("\n" + "=" * 60)
    print("STARTING WATER PREPROCESSING (HSB Living Lab Benchmark)")
    print("=" * 60)
    t0 = time.time()
    
    print(f"Reading raw water file: {RAW_WAT_FILE}")
    df = pd.read_csv(
        RAW_WAT_FILE,
        sep=";",
        dtype={
            "timestamp": str,
            "date": str,
            "hour": int,
            "day_of_week": int,
            "day_name": str,
            "month": int,
            "year": int,
            "sensor_id": str,
            "apartment": str,
            "cluster_name": str,
            "room_number": str,
            "room_type": str,
            "type": str,
            "attached_to": str,
            "value": float,
            "aggregated_value": float
        }
    )
    total_raw_rows = len(df)
    print(f"Total raw water records: {total_raw_rows:,}")
    
    # 1. Clean Non-Physical Readings (following author's protocol in verify_R5.py)
    zero_mask = df["value"] <= 0
    zero_count = int(zero_mask.sum())
    outlier_mask = df["value"] > 0.3  # > 300 Litres in 10 minutes
    outlier_count = int(outlier_mask.sum())
    
    print(f"Zero or negative value records: {zero_count:,}")
    print(f"Outlier records (> 0.3 m3): {outlier_count:,}")
    
    valid_df = df[(df["value"] > 0) & (df["value"] <= 0.3)].copy()
    print(f"Valid consumption events retained: {len(valid_df):,} ({(len(valid_df)/total_raw_rows)*100:.2f}%)")
    
    # 2. Conversion: m3 to Litres
    valid_df["litres"] = valid_df["value"] * 1000.0
    
    # Standardize fixture names
    valid_df["fixture"] = valid_df["attached_to"].fillna("Other")
    
    # Separate hot and cold water flags
    valid_df["is_hot_water"] = valid_df["type"].str.lower().str.contains("hot").astype(int)
    
    # 3. Apartment-Level Daily Aggregation
    print("Aggregating daily consumption by apartment and fixture...")
    fixture_pivot = valid_df.pivot_table(
        index=["date", "apartment", "cluster_name"],
        columns="fixture",
        values="litres",
        aggfunc="sum",
        fill_value=0.0
    ).reset_index()
    
    daily_apt_totals = valid_df.groupby(["date", "apartment", "cluster_name"]).agg(
        total_litres=("litres", "sum"),
        total_m3=("value", "sum"),
        events_count=("value", "count"),
        hot_water_litres=("litres", lambda s: s[valid_df.loc[s.index, "is_hot_water"] == 1].sum())
    ).reset_index()
    
    daily_apt = pd.merge(daily_apt_totals, fixture_pivot, on=["date", "apartment", "cluster_name"], how="left")
    
    # Ensure standard fixture columns exist
    for fix in ["Shower", "Kitchen tap", "Washbasin", "Toilet", "Washing machine", "Dishwasher", "Other"]:
        if fix not in daily_apt.columns:
            daily_apt[fix] = 0.0
            
    daily_apt["laundry_and_dish_litres"] = daily_apt["Washing machine"] + daily_apt["Dishwasher"]
    
    # Rename for clarity
    daily_apt = daily_apt.rename(columns={
        "Shower": "shower_litres",
        "Kitchen tap": "kitchen_litres",
        "Washbasin": "washbasin_litres",
        "Toilet": "toilet_litres"
    })
    
    # Sort chronologically
    daily_apt = daily_apt.sort_values(["apartment", "date"]).reset_index(drop=True)
    print(f"Apartment-daily aggregated observations: {len(daily_apt):,}")
    print(f"Monitored apartments count: {daily_apt['apartment'].nunique()}")
    
    # 4. Building-Wide Daily Totals
    print("Aggregating building-wide daily totals...")
    building_daily = valid_df.groupby("date").agg(
        total_litres=("litres", "sum"),
        total_m3=("value", "sum"),
        active_apartments=("apartment", "nunique"),
        total_events=("value", "count")
    ).reset_index()
    
    building_fixture = valid_df.pivot_table(
        index="date",
        columns="fixture",
        values="litres",
        aggfunc="sum",
        fill_value=0.0
    ).reset_index()
    
    building_daily = pd.merge(building_daily, building_fixture, on="date", how="left")
    print(f"Total days monitored building-wide: {len(building_daily)}")
    
    # 5. Apartment-Level Monthly Aggregation
    print("Aggregating apartment-level monthly totals...")
    daily_apt["date_dt"] = pd.to_datetime(daily_apt["date"])
    daily_apt["year_month"] = daily_apt["date_dt"].dt.to_period("M").astype(str)
    
    monthly_apt = daily_apt.groupby(["apartment", "cluster_name", "year_month"]).agg(
        active_days=("date", "count"),
        total_litres=("total_litres", "sum"),
        shower_litres=("shower_litres", "sum"),
        kitchen_litres=("kitchen_litres", "sum"),
        washbasin_litres=("washbasin_litres", "sum"),
        toilet_litres=("toilet_litres", "sum"),
        laundry_and_dish_litres=("laundry_and_dish_litres", "sum"),
        avg_daily_litres=("total_litres", "mean")
    ).reset_index()
    print(f"Apartment-monthly aggregated rows: {len(monthly_apt):,}")
    
    # 6. Feature Engineering for Future ML (True Calendar-Day Lags, Grouped by Apartment)
    print("Generating group-aware true calendar-day ML features for water dataset...")
    building_monitored_dates = set(building_daily["date"])
    
    min_date = daily_apt["date"].min()
    max_date = daily_apt["date"].max()
    all_calendar_dates = pd.date_range(min_date, max_date, freq="D")
    
    apartments = sorted(daily_apt["apartment"].unique())
    grid_records = []
    
    for apt in apartments:
        sub_apt = daily_apt[daily_apt["apartment"] == apt].copy()
        sub_apt["date_dt"] = pd.to_datetime(sub_apt["date"])
        sub_apt = sub_apt.set_index("date_dt")
        cluster = sub_apt["cluster_name"].dropna().iloc[0] if len(sub_apt["cluster_name"].dropna()) > 0 else "Unknown"
        
        full_apt = pd.DataFrame(index=all_calendar_dates)
        full_apt["apartment"] = apt
        full_apt["cluster_name"] = cluster
        full_apt["date"] = full_apt.index.strftime("%Y-%m-%d")
        full_apt["is_monitored_building_day"] = full_apt["date"].isin(building_monitored_dates)
        
        # Merge target and fixture volumes
        for col in ["total_litres", "total_m3", "events_count", "hot_water_litres",
                    "shower_litres", "kitchen_litres", "washbasin_litres", "toilet_litres", "laundry_and_dish_litres"]:
            if col in sub_apt.columns:
                full_apt[col] = sub_apt[col]
                # On monitored building days where no water events occurred, volume is 0.0 (unoccupied/idle)
                # On unmonitored building downtime days, volume is NaN (unobserved)
                full_apt[col] = np.where(
                    full_apt[col].notna(),
                    full_apt[col],
                    np.where(full_apt["is_monitored_building_day"], 0.0, np.nan)
                )
                
        # Compute true calendar-day lags and rolling statistics on continuous daily calendar
        s = full_apt["total_litres"]
        full_apt["lag_1"] = s.shift(1)
        full_apt["lag_7"] = s.shift(7)
        full_apt["lag_30"] = s.shift(30)
        full_apt["rolling_mean_7"] = s.shift(1).rolling(7, min_periods=3).mean()
        full_apt["rolling_std_7"] = s.shift(1).rolling(7, min_periods=3).std()
        full_apt["rolling_mean_30"] = s.shift(1).rolling(30, min_periods=10).mean()
        
        # Add calendar features
        full_apt = add_calendar_features(full_apt, date_col="date")
        
        # Filter to monitored days where apartment was monitored by building infrastructure
        monitored_apt = full_apt[full_apt["is_monitored_building_day"]].copy()
        grid_records.append(monitored_apt)
        
    daily_apt_features = pd.concat(grid_records).reset_index(drop=True)
    print(f"Generated {len(daily_apt_features):,} apartment-day records with true calendar-day lags.")
    
    if "date_dt" in daily_apt.columns:
        daily_apt = daily_apt.drop(columns=["date_dt"])
        
    # 7. Save Processed Outputs
    p_apt_daily_csv = os.path.join(PROCESSED_WAT_DIR, "water_daily_by_apartment.csv")
    p_apt_daily_parquet = os.path.join(PROCESSED_WAT_DIR, "water_daily_by_apartment.parquet")
    p_bldg_daily_csv = os.path.join(PROCESSED_WAT_DIR, "water_daily_building.csv")
    p_bldg_daily_parquet = os.path.join(PROCESSED_WAT_DIR, "water_daily_building.parquet")
    p_apt_monthly_csv = os.path.join(PROCESSED_WAT_DIR, "water_monthly_by_apartment.csv")
    p_apt_monthly_parquet = os.path.join(PROCESSED_WAT_DIR, "water_monthly_by_apartment.parquet")
    p_apt_features_csv = os.path.join(PROCESSED_WAT_DIR, "water_daily_apartment_features.csv")
    p_apt_features_parquet = os.path.join(PROCESSED_WAT_DIR, "water_daily_apartment_features.parquet")
    
    safe_save(daily_apt, p_apt_daily_csv, p_apt_daily_parquet)
    safe_save(building_daily, p_bldg_daily_csv, p_bldg_daily_parquet)
    safe_save(monthly_apt, p_apt_monthly_csv, p_apt_monthly_parquet)
    safe_save(daily_apt_features, p_apt_features_csv, p_apt_features_parquet)
    
    elapsed = time.time() - t0
    print(f"Water preprocessing completed in {elapsed:.2f}s.")
    print(f"Saved: {p_apt_daily_csv} ({os.path.getsize(p_apt_daily_csv) / 1024:.1f} KB)")
    print(f"Saved: {p_bldg_daily_csv} ({os.path.getsize(p_bldg_daily_csv) / 1024:.1f} KB)")
    print(f"Saved: {p_apt_features_csv} ({os.path.getsize(p_apt_features_csv) / 1024:.1f} KB)")
    
    return {
        "raw_records": total_raw_rows,
        "valid_records": len(valid_df),
        "zero_records": zero_count,
        "outlier_records": outlier_count,
        "apartments_count": int(daily_apt["apartment"].nunique()),
        "daily_apt_rows": len(daily_apt),
        "building_days": len(building_daily),
        "monthly_apt_rows": len(monthly_apt),
        "daily_features_shape": list(daily_apt_features.shape)
    }


def main():
    ensure_dirs()
    print("=" * 60)
    print("AQUAWATT PHASE 3: DATASET PREPROCESSING PIPELINE")
    print("=" * 60)
    start_all = time.time()
    
    ele_summary = preprocess_electricity()
    wat_summary = preprocess_water()
    
    print("\n" + "=" * 60)
    print("PREPROCESSING EXECUTION SUMMARY")
    print("=" * 60)
    print("Electricity Summary:", ele_summary)
    print("Water Summary:", wat_summary)
    print(f"All preprocessing tasks completed successfully in {time.time() - start_all:.2f}s.")


if __name__ == "__main__":
    main()
