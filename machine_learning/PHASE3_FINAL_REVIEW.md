# AquaWatt Machine Learning Subsystem
# Phase 3 Final Technical Review Before ML Training

**Document:** `machine_learning/PHASE3_FINAL_REVIEW.md`  
**Review Date:** November 15, 2026  
**Auditor / Technical Lead:** Antigravity System Agent (in collaboration with Student Developer)  
**Project:** AquaWatt — Water and Electricity Tracking App  
**Status:** **AUDIT PASSED** — Preprocessing Verified, Zero Code Bugs Identified, Ready for Phase 4

---

## Executive Summary

Prior to initiating Phase 4 (Machine Learning Model Training & Evaluation), a rigorous, multi-dimensional technical audit of the Phase 3 Preprocessing and Exploratory Data Analysis (EDA) pipeline was conducted.

The audit verified:
1. **Mathematical correctness** of energy calculations and missing-value normalization.
2. **Aggregation semantics** of the water dataset, confirming the exact origin and physical meaning of the difference between apartment-level ($1,986.46\text{ m}^3$) and building-level ($3,270.79\text{ m}^3$) consumption.
3. **Absence of target leakage** across all autoregressive lag and rolling window features.
4. **Group isolation** across 28 residential apartments with zero cross-tenant historical contamination.
5. **Reproducibility** from the workspace root and byte-level integrity of raw archives.
6. **Backend stability and Git tree preservation** (10/10 tests passing on branch `feature/auth-and-consumption-forms`).

**Result:** No code bugs or data contamination were found in `machine_learning/preprocessing.py` or `machine_learning/eda.py`. No modifications to the codebase or raw archives are required. Crucial operational guidelines and an optimal train/validation/test evaluation strategy for Phase 4 have been defined and documented below.

---

## 1. Audit Scope & Checks Performed

| Dimension | Inspection Focus | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **1. Electricity Missing Values** | Proportional scaling formula, boundary month truncation, coverage thresholds | Python numerical simulation & manual formula derivation | **VERIFIED CORRECT** |
| **2. Water Aggregation** | `value` vs `aggregated_value`, in-unit vs shared building facilities, m³ to Litres | Event-level SQL/Pandas breakdown of raw sensor tags | **VERIFIED CORRECT** |
| **3. Feature Engineering** | Shifted lags, rolling windows, strictly past observations ($t$ exclusion) | Lag-to-target row indexing check & boundary inspection | **VERIFIED CORRECT** |
| **4. Group Isolation** | Cross-apartment independence in water lag and rolling features | Inter-apartment transition boundary index inspection | **VERIFIED CORRECT** |
| **5. ML Evaluation Readiness** | Sample size, temporal coverage, apartment inactivity, seasonal distribution | Panel analysis across all 28 apartments & 1,442 daily rows | **VERIFIED READY** |
| **6. Reproducibility & Hashes** | Project root execution, artifact existence, SHA-256 archive hashes | PowerShell hash verification & output schema check | **VERIFIED IDENTICAL** |
| **7. Backend & Working Tree** | Branch status, uncommitted modifications preserved, pytest suite | `git status` check & `pytest backend/tests/test_api.py -v` | **10/10 PASSING** |

---

## 2. Confirmed Correct Implementations

### 2.1 Electricity Missing-Value Handling & Proportional Normalization
* **Proportional Scaling Formula:**
  $$\text{normalized\_daily\_kwh} = \frac{\text{total\_active\_kwh}}{\text{coverage\_ratio}} = \frac{\sum (P_{\text{active}} / 60)}{\text{valid\_minutes} / 1440} = \left( \frac{\sum P_{\text{active}}}{\text{valid\_minutes}} \times \frac{1}{60} \right) \times 1440$$
  * For complete days ($\ge 95\%$ valid minutes; $\ge 1,368$ observations), minor sensor dropouts ($\le 5\%$) are scaled proportionally to full 24-hour equivalent energy.
  * For incomplete days ($< 95\%$ valid minutes), the code explicitly sets `is_complete_day = False` and retains the unscaled `total_active_kwh`, preventing mathematical explosion on near-zero days.
* **Empirical Validation:**
  * Total daily observations: **1,442 days**.
  * Complete days: **1,417 days (98.27%)**.
  * Incomplete days: **25 days (1.73%)**, including 2 zero-reading blackout days (`2007-04-29` and `2009-06-14`). Neither produced `NaN` or division-by-zero errors.

### 2.2 Water Aggregation Semantics & Shared Facilities Resolution
* **Exclusion of `aggregated_value`:**
  * The raw column `value` is exclusively summed. `aggregated_value` (the cumulative odometer counter) is omitted from all aggregations, eliminating any risk of double-counting.
* **Volume Conversion:**
  * Formula: $\text{litres} = \text{value} \times 1000.0$.
  * Verified: $0.010\text{ m}^3 = 10.0\text{ L}$ (toilet flush), $0.006\text{ m}^3 = 6.0\text{ L}$ (kitchen tap draw).
* **Apartment vs. Building Aggregation Resolution:**
  * In `data/extracted/water/HSB_Living_Lab_Water_Consumption_Anonymized.csv`:
    * Valid consumption events with `apartment != NaN`: **498,046 rows**, totaling **$1,986.464\text{ m}^3$ ($1,986,464\text{ L}$)**.
    * Valid consumption events with `apartment == NaN`: **154,269 rows**, totaling **$1,284.325\text{ m}^3$ ($1,284,325\text{ L}$)**.
    * Total building consumption: **$3,270.789\text{ m}^3$ ($3,270,789\text{ L}$)** across 652,315 valid rows.
  * **Physical Breakdown of Unassigned Rows:**
    * `cluster_name == NaN`: Shared ground-floor laundry studio washing machines ($160.02\text{ m}^3$), common foyer toilets ($114.09\text{ m}^3$), and shared sinks ($80.42\text{ m}^3$).
    * `cluster_name` in `[CL_B, CL_D, CL_G, CL_H]`: Communal student cluster kitchens and shared bathrooms ($929.80\text{ m}^3$).
  * **Conclusion:** Both aggregation tables (`water_daily_by_apartment.csv` and `water_daily_building.csv`) are 100% physically accurate and serve distinct modeling roles: in-unit household tracking vs. whole-building load forecasting.

### 2.3 Zero-Leakage Feature Engineering
* **Strict Past-Only Windows:**
  * `add_lag_and_rolling_features()` applies `shift(1)` *prior* to rolling calculations:
    ```python
    out["lag_1"] = s.shift(1)
    out["rolling_mean_7"] = s.shift(1).rolling(7, min_periods=3).mean()
    out["rolling_std_7"] = s.shift(1).rolling(7, min_periods=3).std()
    out["rolling_mean_30"] = s.shift(1).rolling(30, min_periods=10).mean()
    ```
  * At index $t$, the rolling window spans $[t-7, t-1]$ or $[t-30, t-1]$. Observation $y_t$ is strictly excluded from all input feature columns.
* **Monotonic Chronological Sorting:**
  * Verified: `df_ele['date'].is_monotonic_increasing == True`.
* **Group Isolation:**
  * Water features are calculated within `groupby("apartment")`.
  * Verified: At the boundary between `APT_001` (row index 604) and `APT_002` (row index 605), row 605 resets all lags (`lag_1`, `lag_7`, `lag_30`) and rolling statistics to `NaN`. Zero historical leakage occurs across apartments.

---

## 3. Key Operational Findings & Phase 4 Modeling Guidance

Although no bugs exist in the preprocessing scripts, the audit uncovered several structural nuances that Phase 4 model training scripts must address:

### Finding 1: Boundary Month Truncation in Electricity Dataset
* The UCI electricity dataset starts on **December 16, 2006** (16 days recorded) and ends on **November 26, 2010** (26 days recorded).
* Consequently, `electricity_monthly.csv` records `total_kwh` as $696.88\text{ kWh}$ for Dec 2006 and $743.31\text{ kWh}$ for Nov 2010, compared to full winter months that exceed $1,000\text{–}1,200\text{ kWh}$.
* **Phase 4 Action:** Monthly forecasting experiments should train on `avg_daily_kwh` (which is $43.56\text{ kWh/day}$ for Dec 2006 and $28.59\text{ kWh/day}$ for Nov 2010) rather than unadjusted `total_kwh`, or exclude the two truncated boundary months from the monthly evaluation set.

### Finding 2: Incomplete Days in Daily Electricity Series
* 25 out of 1,442 days have $< 95\%$ coverage (`is_complete_day == False`).
* Two days (`2007-04-29` and `2009-06-14`) have 0 recorded minutes.
* **Phase 4 Action:** For daily model training and evaluation, Phase 4 should filter to complete days (`df[df["is_complete_day"] == True]`) or explicitly document performance with and without partial days.

### Finding 3: Missing Values in Initial Lags (Cold Start Period)
* Because of `shift(1)`, `shift(7)`, and `shift(30)`, the initial 30 daily observations of any series contain `NaN` values for `lag_30` and `rolling_mean_30`.
* Standard scikit-learn regressors (`LinearRegression`, `RandomForestRegressor`, `GradientBoostingRegressor`) raise `ValueError` on `NaN` feature inputs.
* **Phase 4 Action:** In Phase 4, the training set must either:
  1. Drop the initial 30 rows per entity: `df.dropna(subset=['lag_30', 'rolling_mean_30'])`.
  2. For the water dataset, apply the 30-day drop *per apartment* after group feature generation.

### Finding 4: Apartment Occupancy & Inactivity Patterns
* Active monitored days per apartment range from **323 days** (APT_006) to **945 days** (APT_017).
* Student apartments experience extended zero-consumption periods during university summer and winter holidays.
* Mean consumption varies significantly between single-occupant studios (e.g. APT_007: $23.6\text{ L/day}$) and communal cluster flats (e.g. APT_017: $394.4\text{ L/day}$).
* **Phase 4 Action:** Evaluation metrics must report both Mean Absolute Error ($MAE$) and Median Absolute Error ($MedAE$), as standard Root Mean Squared Error ($RMSE$) is disproportionately inflated by intermittent unoccupied days and single-day leakage spikes (e.g. APT_005's $9,660\text{ L}$ event).

---

## 4. Required Corrections

* **Codebase Corrections:** **None required.**
* **Pipeline Integrity:** `preprocessing.py` and `eda.py` executed cleanly, adhere to zero-leakage constraints, and produce auditable CSV and Parquet files.
* **Raw Data:** Raw archives remain untouched with verified cryptographic checksums.

---

## 5. Recommended Phase 4 Train/Validation/Test Split Strategy

To ensure scientific rigor, avoid look-ahead bias, and mirror real-world production deployment in AquaWatt, the following split strategy is recommended for Phase 4:

### 5.1 Electricity Dataset Split Strategy (Strict Chronological Out-of-Time)

Because electricity data represents a single continuous longitudinal time series (1,442 days; Dec 2006 – Nov 2010), **random k-fold splitting is strictly prohibited** due to temporal autocorrelation.

| Partition | Date Range | Duration | Approximate Share | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Train Set** | Dec 16, 2006 – Dec 31, 2008 | ~24.5 months (747 days) | **~52%** | Captures two full annual cycles (winter peaks, summer troughs). |
| **Validation Set** | Jan 1, 2009 – Dec 31, 2009 | 12 months (365 days) | **~25%** | Full 4-season validation set for hyperparameter tuning. |
| **Test Set** | Jan 1, 2010 – Nov 26, 2010 | ~11 months (330 days) | **~23%** | Unseen out-of-time test set for final generalization benchmarking. |

*Alternative (70 / 15 / 15 percentile split):*
* **Train:** Dec 16, 2006 – Sep 20, 2009 (1,009 days; 70.0%)
* **Val:** Sep 21, 2009 – Apr 23, 2010 (215 days; 15.0%)
* **Test:** Apr 24, 2010 – Nov 26, 2010 (218 days; 15.0%)

### 5.2 Water Dataset Split Strategy (Group-Aware Temporal Panel Split)

For the water dataset, we have a panel structure: 28 individual apartments monitored over the same calendar window (Jan 2020 – Jan 2023).

**Recommended Method: Temporal Panel Split (Group-Aware Out-of-Time)**
Rather than withholding entire apartments (which would test cold-start transfer learning without occupant-specific baselines), we evaluate the model's ability to forecast future consumption for known households:
* **Train Set:** Jan 1, 2020 – Dec 31, 2021 (Years 1 & 2; all 28 apartments; ~65% of observations).
* **Validation Set:** Jan 1, 2022 – Jun 30, 2022 (First half of Year 3; all 28 apartments; ~17% of observations).
* **Test Set:** Jul 1, 2022 – Jan 31, 2023 (Second half of Year 3; all 28 apartments; ~18% of observations).

**Why this is optimal for AquaWatt:**
1. In the actual mobile app, a registered user logs consumption over time. The ML model learns the user's specific baseline and forecasts their future consumption.
2. Training on 2020–2021 and testing on 2022–2023 ensures zero look-ahead bias while maintaining per-household calibration.

### 5.3 Candidate Model Architecture Suite for Phase 4

For each benchmark dataset, evaluate a progressive 3-tier hierarchy:
1. **Baseline Regressors:**
   * Naive Persistence Model ($y_t = y_{t-1}$).
   * 7-day Seasonal Moving Average ($y_t = \text{mean}(y_{t-1..t-7})$).
   * Ridge / Lasso Linear Regression (interpretable linear baseline with L2/L1 regularization).
2. **Nonlinear Ensemble Trees:**
   * Random Forest Regressor (`n_estimators=100`, bounded depth to prevent overfitting).
3. **Gradient Boosted Decision Trees:**
   * Gradient Boosting Regressor / HistGradientBoostingRegressor (handles non-linear interactions between lags, calendar features, and seasonal cycles).

### 5.4 Primary Evaluation Metrics
* **MAE (Mean Absolute Error):** Primary metric in physical units ($\text{kWh}$ and $\text{Litres}$) for direct interpretability.
* **RMSE (Root Mean Squared Error):** Penalizes large forecast misses.
* **$R^2$ (Coefficient of Determination):** Measures variance explained relative to mean baseline.
* **MedAE (Median Absolute Error):** Robust to apartment vacancy days and sudden leak outliers.

---

## 6. Verification Checklist & Sign-Off

- [x] **Raw Data Untouched:** `data/raw/` archives cryptographically match initial download hashes.
- [x] **No Synthetic Data:** All datasets originate from official peer-reviewed repositories (UCI and Zenodo).
- [x] **Preprocessing Soundness:** Zero code bugs or math errors in `preprocessing.py`.
- [x] **EDA Complete:** 7 high-resolution figures and statistical summary JSON generated and verified.
- [x] **Target Leakage Audited:** Zero future leakage; shifted windows strictly verified.
- [x] **Group Boundaries Verified:** Water lag features strictly isolated by apartment.
- [x] **Backend Intact:** All 10 FastAPI backend tests pass with 0 regressions.
- [x] **Working Tree Preserved:** All 15 uncommitted files on `feature/auth-and-consumption-forms` preserved.
- [x] **Zero Models Trained:** System remains clean and prepared for Phase 4 model training.

**Phase 3 Technical Review Status:** **APPROVED FOR PHASE 4 TRAINING**

