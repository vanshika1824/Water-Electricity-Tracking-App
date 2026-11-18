# AquaWatt — Water & Electricity Tracking App
## Phase 2: Data Acquisition & Integrity Verification Report

**Date of Acquisition:** November 15, 2026 (11:55 UTC)  
**Execution Environment:** Windows (PowerShell / Python 3.13.14)  
**Status:** Successfully Downloaded, Cryptographically Verified & Extracted  
**Primary Auditor:** Antigravity System Agent (in collaboration with Student Developer)

---

## 1. Executive Summary

Phase 2 (Dataset Acquisition) has been completed in strict accordance with the project integrity guidelines:
- **No data was fabricated or synthetically generated.**
- **Original downloaded archives are saved unchanged** in `data/raw/electricity/` and `data/raw/water/`.
- **Extracted inspection copies** were extracted into dedicated directories (`data/extracted/electricity/` and `data/extracted/water/`) without touching the raw originals.
- **Cryptographic SHA-256 checksums** were computed and verified against official repository metadata.
- **No preprocessing, cleaning, feature transformation, or model training** has been performed yet.

---

## 2. Acquired Datasets Summary Table

| Attribute | Electricity Dataset | Water Dataset |
| :--- | :--- | :--- |
| **Dataset Name** | Individual Household Electric Power Consumption | HSB Living Lab Fixture-Level Household Water Consumption |
| **Primary Creator / Author** | Georges Hébrail & Alice Bérard (EDF R&D) | Jesper Knutsson (Chalmers University of Technology) |
| **Hosting Platform** | UCI Machine Learning Repository (ID: 235) | Zenodo Open Science Repository |
| **Official Record / DOI** | [10.24432/C58K54](https://doi.org/10.24432/C58K54) | [10.5281/zenodo.22076411](https://doi.org/10.5281/zenodo.22076411) |
| **Official Source URL** | `https://archive.ics.uci.edu/static/public/235/...` | `https://zenodo.org/api/records/22076411/files/...` |
| **License** | Creative Commons Attribution 4.0 (**CC BY 4.0**) | Creative Commons Attribution 4.0 (**CC BY 4.0**) |
| **Original Archive Name** | `individual+household+electric+power+consumption.zip` | `HSB_Living_Lab_Data_Package.zip` |
| **Raw File Path** | `data/raw/electricity/individual+household+electric+power+consumption.zip` | `data/raw/water/HSB_Living_Lab_Data_Package.zip` |
| **Raw Archive Size** | **20,640,916 bytes** (19.68 MB) | **6,244,502 bytes** (5.96 MB) |
| **Raw SHA-256 Checksum** | `9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff` | `ff766b30d05e65c2477fc929d56a112d5b0775619075daa2bd6dd687c57c7c89` |
| **Extracted Folder** | `data/extracted/electricity/` | `data/extracted/water/` |
| **Primary Data File** | `household_power_consumption.txt` (126.8 MB) | `HSB_Living_Lab_Water_Consumption_Anonymized.csv` (81.2 MB)|
| **Total Valid Records** | **2,075,259 data rows** (+1 header) | **652,315 data rows** (+1 header) |

---

## 3. Electricity Dataset Verification (UCI Repository)

### 3.1 Download Verification
- **Source URL:** `https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip`
- **Downloaded To:** `data/raw/electricity/individual+household+electric+power+consumption.zip`
- **Size:** 20,640,916 bytes (~19.68 MB)
- **SHA-256 Checksum:** `9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff`

### 3.2 Extracted Structure & File Inspection
Archive extracted to: `data/extracted/electricity/`
Contains 1 single primary text file:
* **Filename:** `household_power_consumption.txt`
* **Uncompressed Size:** 132,960,755 bytes (~126.8 MB)
* **SHA-256 Checksum:** `4259c9d7ece5dbee9ab8d53682baac68d791c864f0f64a52b4043cb3b90894b7`
* **Total Line Count:** **2,075,260 lines** (1 header line + exactly 2,075,259 data rows).
* **Header Line:**
  ```text
  Date;Time;Global_active_power;Global_reactive_power;Voltage;Global_intensity;Sub_metering_1;Sub_metering_2;Sub_metering_3
  ```
* **Sample Initial Records:**
  ```text
  16/12/2006;17:24:00;4.216;0.418;234.840;18.400;0.000;1.000;17.000
  16/12/2006;17:25:00;5.360;0.436;233.630;23.000;0.000;1.000;16.000
  16/12/2006;17:26:00;5.374;0.498;233.290;23.000;0.000;2.000;17.000
  ```
* **License & Attribution:** Creative Commons Attribution 4.0 International (**CC BY 4.0**). Author attribution: Georges Hébrail & Alice Bérard, EDF R&D.

---

## 4. Water Dataset Verification (Zenodo Record 22076411)

### 4.1 Official Record Pre-Download Verification
Prior to downloading, the Zenodo REST API endpoint (`https://zenodo.org/api/records/22076411`) was queried to authenticate the record:
* **Zenodo Title:** `"HSB Living Lab Fixture-Level Household Water Consumption Dataset (2019–2023)"`
* **Registered DOI:** `10.5281/zenodo.22076411`
* **Author / Affiliation:** `Knutsson, Jesper` (Chalmers University of Technology)
* **Registered License ID:** `cc-by-4.0`
* **Official MD5 Checksum:** `1db6a143f39da53710e63c6bb353d5b1` (matches downloaded archive)

### 4.2 Downloaded Raw Archives & Companion Files
Saved in `data/raw/water/`:
1. `HSB_Living_Lab_Data_Package.zip`:
   * Size: 6,244,502 bytes (~5.96 MB)
   * SHA-256: `ff766b30d05e65c2477fc929d56a112d5b0775619075daa2bd6dd687c57c7c89`
2. `verify_R5.py` (Official author verification script):
   * Size: 14,292 bytes
   * SHA-256: `af1f32f9cc51535604a8e40cd3668194c84fa4034f655dfb5ee6c332476134a5`
3. `verified_numbers_R5.json` (Official benchmark statistics):
   * Size: 4,883 bytes
   * SHA-256: `852b590441e6fda92ab32280586f2c91382654124f3b979719fa9dae25f9c306`

### 4.3 Extracted Structure & File Inspection
Archive extracted to: `data/extracted/water/`

| Extracted Relative Path | File Size | SHA-256 Checksum | Line Count | Description / Role |
| :--- | :--- | :--- | :--- | :--- |
| `HSB_Living_Lab_Water_Consumption_Anonymized.csv` | 85,140,852 B (81.2 MB) | `e9b8f34245b5cfb2b43d8fe3274056bcc5f3dca0cbf8904a6c4227ddd42d0be8` | **652,316** | Primary dataset (1 header + 652,315 observations) |
| `DATA_DICTIONARY.txt` | 7,531 B (0.01 MB) | `6dd0a5fdaee4472f05f08deb7561624c4267e576f7f3dea45758ab5014408720` | 180 | Variable documentation, units, anonymization rules |
| `README.txt` | 3,798 B (0.00 MB) | `a2726d9189e870cf347a0e1e865f392295d9f92a584ac4a915200f21f0b51582` | 88 | Dataset overview, authors, contact, license |
| `scripts/anonymize_data.py` | 5,803 B (0.01 MB) | `f92ffc50e29b4509301294a60f8de53df59fa2860d2d753d68fd0cfb066df907` | 191 | Cleaning pipeline, outlier & zero removal logic |
| `scripts/water_analysis.py` | 27,310 B (0.03 MB) | `1c50feb216eba855a6e2c3e7a99d301835c1ca0d567ce4ffd731e6d225186bd4` | 657 | Descriptive statistics, non-parametric tests |
| `scripts/generate_figures.py` | 31,660 B (0.03 MB) | `dd9f5d9c7da87617d9745f3be0e2d92f93a496e69eed544f0b1a298147835700` | 779 | Publication figure generation code |

### 4.4 Header Line & Columns
Header in `HSB_Living_Lab_Water_Consumption_Anonymized.csv`:
```text
timestamp;date;hour;day_of_week;day_name;month;year;sensor_id;apartment;cluster_name;room_number;room_type;type;attached_to;value;aggregated_value
```

### 4.5 Critical Unit Discovery & Clarification
During source code inspection of `scripts/anonymize_data.py` and `scripts/water_analysis.py`, a critical domain insight was confirmed:
- While `DATA_DICTIONARY.txt` casually refers to liters, the actual numerical values in the `value` column are recorded in **cubic meters ($m^3$)**:
  * An individual toilet flush is recorded as `value = 0.010` ($0.010\text{ m}^3 = 10.0\text{ Litres}$).
  * A kitchen tap draw is recorded as `value = 0.006` ($0.006\text{ m}^3 = 6.0\text{ Litres}$).
  * An individual washbasin event is recorded as `value = 0.004` ($0.004\text{ m}^3 = 4.0\text{ Litres}$).
  * In `anonymize_data.py`, line 21 defines the extreme outlier threshold: `df = df[df['value'] <= 0.3]`, where $0.3\text{ m}^3 = 300\text{ Litres}$ in a single 10-minute interval.
- **Conversion Formula for AquaWatt:**
  $$\text{Volume in Litres} = \text{value} \times 1000$$

---

## 5. License & Attribution Compliance Verification

* **Electricity Dataset:**
  * **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
  * **Attribution Requirement:** *"Individual Household Electric Power Consumption dataset, Georges Hébrail and Alice Bérard, EDF R&D / UCI Machine Learning Repository."*
  * **Status:** Compliant.
* **Water Dataset:**
  * **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
  * **Attribution Requirement:** *"HSB Living Lab Fixture-Level Household Water Consumption Dataset (2019–2023), Jesper Knutsson, Chalmers University of Technology, Zenodo DOI: 10.5281/zenodo.22076411."*
  * **Status:** Compliant.

---

## 6. Directory Layout at Completion of Phase 2

```text
Water-Electricity-Tracking-App/
│
├── data/
│   ├── raw/                               # IMMUTABLE ORIGINAL DOWNLOADS
│   │   ├── electricity/
│   │   │   └── individual+household+electric+power+consumption.zip (20.64 MB)
│   │   └── water/
│   │       ├── HSB_Living_Lab_Data_Package.zip (6.24 MB)
│   │       ├── verify_R5.py (14.29 KB)
│   │       └── verified_numbers_R5.json (4.88 KB)
│   │
│   └── extracted/                         # INSPECTION COPIES (UNMODIFIED)
│       ├── electricity/
│       │   └── household_power_consumption.txt (126.80 MB, 2,075,259 records)
│       └── water/
│           ├── HSB_Living_Lab_Water_Consumption_Anonymized.csv (81.20 MB, 652,315 records)
│           ├── DATA_DICTIONARY.txt (7.53 KB)
│           ├── README.txt (3.80 KB)
│           └── scripts/
│               ├── anonymize_data.py
│               ├── water_analysis.py
│               └── generate_figures.py
│
├── machine_learning/
│   ├── DATASET_RESEARCH.md                # Research report with verified sources
│   ├── download_datasets.py               # Reproducible acquisition script
│   └── acquisition_summary.json           # Machine-readable hashes and metadata
│
├── AQUAWATT_PROJECT_AUDIT.md              # Project audit report
├── AQUAWATT_IMPLEMENTATION_PLAN.md        # Master phase-by-phase implementation plan
└── DATA_ACQUISITION_REPORT.md             # This acquisition and verification report
```

---

## 7. Recommended Next Steps for Phase 3

Now that authentic datasets have been acquired and verified:
1. **Prepare Dependencies:** Install data science packages (`pandas`, `numpy`, `scikit-learn`, `joblib`, `matplotlib`) into the virtual environment.
2. **Exploratory Data Analysis (EDA):** Inspect distributions, verify date spans, plot diurnal cycles, and record missing value statistics.
3. **Build `machine_learning/preprocessing.py`:**
   - Resample minutely electricity power ($kW$) to daily and monthly energy ($kWh$).
   - Multiply water `value` by 1000 to convert from $m^3$ to Litres, and aggregate to daily and monthly apartment/fixture totals.
   - Construct lag features ($t-1, t-7, t-30$), rolling statistics (7-day and 30-day moving averages), and calendar features.
4. **Compile `machine_learning/dataset_report.md`:** Comprehensive data quality and exploratory documentation before training any models.

