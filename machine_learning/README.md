# AquaWatt — Machine Learning Subsystem

This directory contains the dataset research, acquisition scripts, preprocessing pipelines, exploratory data analysis (EDA), and machine learning models for the AquaWatt project.

---

## 1. Directory Structure

```text
machine_learning/
├── DATASET_RESEARCH.md            # Verified benchmark dataset research and comparative analysis
├── DATASET_REPORT.md              # Phase 3 exploratory data analysis and data health report
├── requirements.txt               # Python dependencies for ML (pandas, scikit-learn, matplotlib, etc.)
├── download_datasets.py           # Phase 2 acquisition and SHA-256 integrity verification script
├── acquisition_summary.json       # JSON record of raw dataset checksums and metadata
├── preprocessing.py               # Phase 3 preprocessing and zero-leakage feature engineering script
├── eda.py                         # Phase 3 exploratory data analysis and figure generation script
│
├── outputs/
│   ├── eda_summary.json           # Statistical summary of electricity and water datasets
│   └── figures/                   # 300 DPI publication-quality figures
│       ├── 01_electricity_daily_trend.png
│       ├── 02_electricity_weekly_monthly_profile.png
│       ├── 03_electricity_submetering_distribution.png
│       ├── 04_water_daily_trend_building.png
│       ├── 05_water_fixture_distribution.png
│       ├── 06_water_apartment_comparison.png
│       └── 07_water_weekly_profile.png
│
└── models/                        # Serialized .joblib model artifacts (for Phase 4)
```

---

## 2. Processed Datasets

Processed datasets are stored in `data/processed/` (in both CSV and Parquet formats):

* **Electricity (`data/processed/electricity/`):**
  * `electricity_daily.csv` / `.parquet`: 1,442 days (1,417 complete) with kWh active totals and sub-metering breakdown.
  * `electricity_monthly.csv` / `.parquet`: 48 calendar months with monthly totals and daily averages.
  * `electricity_daily_features.csv` / `.parquet`: Daily series with shifted lag features (`lag_1`, `lag_7`, `lag_30`), rolling statistics (7-day and 30-day means), and calendar indicators for future ML.
* **Water (`data/processed/water/`):**
  * `water_daily_by_apartment.csv` / `.parquet`: 20,095 apartment-day records across 28 units with fixture breakdowns in Litres.
  * `water_daily_building.csv` / `.parquet`: 946 building-wide daily totals.
  * `water_monthly_by_apartment.csv` / `.parquet`: 902 apartment-month records.
  * `water_daily_apartment_features.csv` / `.parquet`: Apartment-level daily series with strictly group-aware lag and rolling features.

---

## 3. How to Run Preprocessing & EDA

From the project root directory:

### Step 1: Install Dependencies
```powershell
backend\.venv\Scripts\python.exe -m pip install -r machine_learning/requirements.txt
```

### Step 2: Run Preprocessing Pipeline
```powershell
backend\.venv\Scripts\python.exe machine_learning/preprocessing.py
```

### Step 3: Run Exploratory Data Analysis & Generate Visualizations
```powershell
backend\.venv\Scripts\python.exe machine_learning/eda.py
```

---

## 4. Current Status
* **Phase 1 (Audit & Plan):** Completed.
* **Phase 2 (Acquisition & Verification):** Completed.
* **Phase 3 (Preprocessing & EDA):** Completed.
* **Phase 4 (Model Training & Evaluation):** Pending user approval. No models have been trained yet.

