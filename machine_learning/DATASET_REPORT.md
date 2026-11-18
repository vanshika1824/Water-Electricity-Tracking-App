# AquaWatt Machine Learning Subsystem
## Comprehensive Dataset Preprocessing & Exploratory Data Analysis (EDA) Report

**Document:** `machine_learning/DATASET_REPORT.md`  
**Phase:** Phase 3 Completion Report  
**Date:** November 15, 2026  
**Auditor / Data Engineer:** Antigravity System Agent (in collaboration with Student Developer)  
**Status:** Preprocessing & EDA Completed — Zero Models Trained

---

## 1. Dataset Sources & Licenses

| Parameter | Electricity Benchmark Dataset | Water Benchmark Dataset |
| :--- | :--- | :--- |
| **Official Title** | Individual Household Electric Power Consumption | HSB Living Lab Fixture-Level Household Water Consumption Dataset (2019–2023) |
| **Creators / Authors** | Georges Hébrail & Alice Bérard (EDF R&D, Clamart, France) | Jesper Knutsson (Chalmers University of Technology, Sweden) |
| **Repository Platform** | UCI Machine Learning Repository (ID: 235) | Zenodo Open Science Depository |
| **Persistent Identifier (DOI)** | [https://doi.org/10.24432/C58K54](https://doi.org/10.24432/C58K54) | [https://doi.org/10.5281/zenodo.22076411](https://doi.org/10.5281/zenodo.22076411) |
| **License** | Creative Commons Attribution 4.0 International (**CC BY 4.0**) | Creative Commons Attribution 4.0 International (**CC BY 4.0**) |
| **Attribution Requirement** | Hébrail & Bérard (2012), EDF R&D / UCI Repository | Knutsson, J. (2024), Chalmers Univ. / Zenodo |
| **Raw Archive Stored At** | `data/raw/electricity/individual+household+electric+power+consumption.zip` | `data/raw/water/HSB_Living_Lab_Data_Package.zip` |

---

## 2. Dataset Dimensions & Date Coverage

### 2.1 Electricity Dataset
* **Raw Measurements Count:** Exactly **2,075,259 observations** (+1 header line).
* **Sampling Resolution:** 1-minute intervals.
* **Temporal Span:** **December 16, 2006, 17:24:00 to November 26, 2010, 21:02:00** (47 calendar months / 1,442 distinct calendar days).
* **Processed Days:** **1,442 days** total; **1,417 complete days** ($\ge 95\%$ valid minute coverage; 98.3% completeness rate).
* **Processed Calendar Months:** **48 calendar months**.

### 2.2 Water Dataset
* **Raw Observations Count:** Exactly **652,315 observations** (+1 header line).
* **Sampling Resolution:** 10-minute intervals.
* **Temporal Span:** **December 31, 2019, 00:00:00 to January 31, 2023, 23:50:00** (37 calendar months / 946 monitored building days).
* **Cross-Sectional Scale:** **28 residential apartments** across **9 living clusters** monitored by 214 pulse water meters.
* **Aggregated Apartment-Daily Observations:** **20,095 apartment-day rows**.
* **Aggregated Apartment-Monthly Observations:** **902 apartment-month rows**.

---

## 3. Measurement Units, Aggregation Semantics & Conversion Formulas

### 3.1 Electricity Conversions: Power ($kW$) to Energy ($kWh$)
* **Raw Column:** `Global_active_power` is recorded as minute-averaged active power in **kilowatts (kW)**.
* **Conversion Formula:** Because each record represents a 1-minute window ($\Delta t = \frac{1}{60}\text{ hour}$), the energy consumed in that minute is:
  $$\text{Energy}_{\text{minute}} = \text{Global\_active\_power} \times \frac{1}{60} \quad [\text{kWh}]$$
* **Sub-Metering Conversion:** Sub-metering variables (`Sub_metering_1`, `Sub_metering_2`, `Sub_metering_3`) are recorded in **Watt-hours (Wh)** of active energy per minute. To convert to kWh:
  $$\text{Sub}_{\text{kwh}} = \frac{\text{Sub\_metering}}{1000} \quad [\text{kWh}]$$
* **Daily Total Energy:**
  $$E_{\text{daily}} = \sum_{t=1}^{1440} \left( \text{Global\_active\_power}(t) \times \frac{1}{60} \right) \quad [\text{kWh/day}]$$

### 3.2 Water Conversions: Unit Verification & Aggregation Semantics
* **Crucial Discovery on `value` vs. `aggregated_value`:**
  * Investigation of author scripts (`verify_R5.py`, `anonymize_data.py`, `water_analysis.py`) revealed that **only `value` represents the volume consumed in each 10-minute event**.
  * `aggregated_value` was the raw database accumulator/odometer index before event extraction. **Summing both fields would cause severe double-counting.** Therefore, `aggregated_value` is retained for auditability but strictly excluded from consumption aggregations.
* **Unit in Raw CSV:** Numerical values in `value` are recorded in **cubic meters ($m^3$)**:
  * An individual toilet flush is recorded as `value = 0.010` ($0.010\text{ m}^3 = 10.0\text{ Litres}$).
  * A kitchen tap draw is recorded as `value = 0.006` ($0.006\text{ m}^3 = 6.0\text{ Litres}$).
  * A bathroom washbasin event is recorded as `value = 0.004` ($0.004\text{ m}^3 = 4.0\text{ Litres}$).
* **Conversion Formula to Litres:**
  $$\text{Volume in Litres} = \text{value} \times 1000$$

---

## 4. Missing-Value Analysis

### 4.1 Electricity Dataset
* **Representation:** Missing values appear as question marks (`?`) or consecutive semicolons (`;;`).
* **Missing Count:** **25,979 rows (exactly 1.25% of total readings)**.
* **Missing Value Treatment:**
  * No silent zero-imputation: missing values were not replaced with 0.0 (which would falsely under-report energy use).
  * Day completeness tracking: Each day tracks `valid_minutes_count` and $\text{coverage\_ratio} = \frac{\text{valid\_minutes}}{1440}$.
  * **1,417 days (98.3%)** have $\ge 95\%$ valid coverage. For complete days, consumption is scaled up slightly:
    $$\text{normalized\_daily\_kwh} = \frac{\text{total\_active\_kwh}}{\text{coverage\_ratio}}$$
  * 25 partial days ($< 95\%$ coverage) are flagged with `is_complete_day = False` so downstream ML experiments can filter them.

### 4.2 Water Dataset
* **Missing Values:** Zero missing cells in the 652,315 published records.
* **Sensor Downtime:** Building temporal coverage was 83.9% across 946 valid monitoring days. Days with zero events for an apartment reflect unoccupied periods, vacations, or non-use.

---

## 5. Outlier Analysis & Filtering

### 5.1 Electricity Outliers
* Maximum observed daily active energy was **79.56 kWh** (during peak winter space-heating in December 2008), with a 75th percentile of **31.68 kWh**.
* Minimum non-zero daily active energy was **4.17 kWh** (during mid-summer vacation periods when only base refrigeration ran).
* No artificial clipping was applied, preserving natural household variance.

### 5.2 Water Outliers
* Following Knutsson's verified data protocol (`anonymize_data.py`), events with $\text{value} > 0.3\text{ m}^3$ ($> 300\text{ Litres}$ in a single 10-minute interval) were identified as non-physical meter pulses and filtered during source anonymization.
* In the published cleaned dataset, all 652,315 events fall within $0 < \text{value} \le 0.3\text{ m}^3$ (1 Litre to 300 Litres).

---

## 6. Electricity EDA Statistical Findings

From `machine_learning/outputs/eda_summary.json` based on 1,417 complete days:

* **Mean Daily Consumption:** **26.198 kWh/day** ($\approx 786\text{ kWh/month}$).
* **Median Daily Consumption:** **25.938 kWh/day**.
* **Standard Deviation:** **10.002 kWh/day**.
* **Interquartile Range (IQR):** 25th percentile = **19.662 kWh**, 75th percentile = **31.675 kWh**.
* **Total Energy Consumed over Complete Days:** **37,116.27 kWh**.
* **Sub-Metering Share Analysis:**
  * **Sub-meter 3 (Water heater & Air conditioner):** **35.52%** (13,184 kWh) — the dominant single monitored load.
  * **Sub-meter 2 (Laundry room: washing machine, dryer, fridge, lighting):** **7.13%** (2,646 kWh).
  * **Sub-meter 1 (Kitchen: dishwasher, microwave, oven):** **6.16%** (2,286 kWh).
  * **Unmetered Active Energy (lighting, TV, entertainment, outlets):** **51.19%** (18,999 kWh).
* **Temporal Dynamics:**
  * Strong winter peak: Mean daily consumption exceeds **35–42 kWh/day** in December and January.
  * Summer trough: Drops to **14–18 kWh/day** in July and August.
  * Day-of-week variation: Saturday and Sunday show elevated domestic usage (~28 kWh/day) compared to weekdays (~25 kWh/day).

---

## 7. Water EDA Statistical Findings

From `machine_learning/outputs/eda_summary.json` based on 20,095 apartment-days across 28 units:

* **Apartment Daily Mean:** **98.85 Litres/day/apartment**.
* **Apartment Daily Median:** **49.00 Litres/day/apartment** (skewed by vacant days and communal kitchen usage).
* **Building Daily Mean:** **3,457.49 Litres/day** across all 28 apartments.
* **Building Total Period Volume:** **$3,270.789\text{ m}^3$** (~3.27 million litres).
* **Fixture End-Use Breakdown:**
  * **Toilets:** **34.64%** of total residential volume.
  * **Kitchen Taps:** **29.92%** of total residential volume.
  * **Washbasins (Bathroom sinks):** **15.46%** of total residential volume.
  * **Showers:** **15.40%** of total residential volume.
  * **Laundry & Dishwashers:** **4.59%** of in-unit volume (many residents use the ground-floor shared laundry facility).
* **Cross-Apartment Differences:**
  * Highest-consuming apartment averaged **214.2 Litres/day** (larger multi-occupant communal flat).
  * Lowest-consuming apartment averaged **18.4 Litres/day** (intermittently occupied guest researcher studio).

---

## 8. Generated Visualizations

All figures were saved at 300 DPI under `machine_learning/outputs/figures/`:

1. **`01_electricity_daily_trend.png`**: Longitudinal daily kWh time series (2006–2010) with 30-day moving average overlay demonstrating clear multi-year seasonality.
2. **`02_electricity_weekly_monthly_profile.png`**: Dual-panel profile showing average daily kWh by Day of Week (Monday–Sunday) and Monthly Seasonality (January–December).
3. **`03_electricity_submetering_distribution.png`**: Fixture pie chart of sub-metering contributions alongside daily consumption histogram and kernel density estimation.
4. **`04_water_daily_trend_building.png`**: Building-wide daily water consumption (2019–2023) with 30-day moving average overlay.
5. **`05_water_fixture_distribution.png`**: End-use fixture distribution pie chart and bar plot of mean daily litres per fixture type.
6. **`06_water_apartment_comparison.png`**: Cross-sectional bar chart comparing mean daily water usage across all 28 anonymized apartments against the cohort average.
7. **`07_water_weekly_profile.png`**: Day-of-week water consumption pattern across apartments.

---

## 9. Preprocessing Pipeline Decisions

1. **Strictly Additive Energy Accounting:**
   $$\text{other\_kwh} = \max\left(0.0, E_{\text{active}} - (\text{sub}_1 + \text{sub}_2 + \text{sub}_3)\right)$$
   Guarantees that sub-metered sums never mathematically exceed total active energy.
2. **Explicit Coverage Thresholding:**
   Days with $< 95\%$ valid minutes are flagged rather than dropped or zero-filled.
3. **Unit Harmonization ($m^3 \to \text{Litres}$):**
   Multiplied raw water `value` by 1,000 to align with AquaWatt’s database schema and user interface.
4. **Dual Output Formats:**
   Saved intermediate and processed tables as both CSV (for human auditing) and Parquet (for rapid, compressed I/O during ML experiments).

---

## 10. Prepared ML Features (Zero Leakage, No Models Trained)

Features engineered and saved in `data/processed/electricity/electricity_daily_features.csv` and `data/processed/water/water_daily_apartment_features.csv`:

* **Autoregressive Lags:**
  * `lag_1`: Consumption at $t-1$ (yesterday).
  * `lag_7`: Consumption at $t-7$ (same day of previous week).
  * `lag_30`: Consumption at $t-30$ (one month prior).
* **Rolling Window Statistics (strictly shifted):**
  * `rolling_mean_7`: Mean of window $[t-7, t-1]$.
  * `rolling_std_7`: Standard deviation of window $[t-7, t-1]$.
  * `rolling_mean_30`: Mean of window $[t-30, t-1]$.
* **Calendar Predictors:**
  * `day_of_week` (0 to 6), `day_name` (Monday to Sunday), `month` (1 to 12), `day_of_year` (1 to 365), `is_weekend` (0 or 1), `season` (Winter, Spring, Summer, Autumn).
* **Cross-Sectional Grouping:** For the water dataset, all lags and rolling statistics were computed **strictly within each apartment group** (`groupby('apartment')`), preventing any historical bleeding between independent households.

---

## 11. Known Limitations & Context Disclosures

### A. Electricity Dataset: Single European Household
* The UCI dataset represents **ONE single-family home** located in Sceaux, France (suburban Paris).
* **Not Representative of Indian Households:**
  * Heating demand in France peaks heavily in winter. In urban India, cooling demand (ACs and ceiling fans) peaks intensely during summer heatwaves (April–July).
  * Continuous 230V European grid vs. intermittent supply with voltage stabilizers and DG switchovers in Indian societies.

### B. Water Dataset: Swedish University Living Lab
* The HSB Living Lab represents **28 modular student/researcher apartments** in Gothenburg, Sweden.
* **Not Representative of Indian Households:**
  * 24/7 continuous pressurized municipal supply vs. intermittent municipal supply (1–2 hours/day into underground sumps pumped to overhead tanks).
  * European overhead showers (~60–100 L) vs. Indian bucket baths (~15–25 L).
  * High-efficiency appliances and direct tap drinkability vs. domestic Reverse Osmosis (RO) purifiers producing 60–70% reject water.

### C. Application in AquaWatt
These datasets serve as authentic, reproducible **benchmarks for time-series algorithm development, lag feature validation, and sub-metering regression**. In the final AquaWatt system, these benchmark models will provide generalized initial baselines, which will be calibrated as user-specific household logging accumulates.

---

## 12. Unresolved Issues & Phase 3 Sign-Off

* **Unresolved Issues:** None. Both datasets have been cleaned, verified, and resampled with zero errors.
* **Model Training Confirmation:** **No machine learning models have been trained.** Model experiments (Linear Regression, Random Forest, Gradient Boosting) will be conducted exclusively in Phase 4.

