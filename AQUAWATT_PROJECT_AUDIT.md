# AquaWatt — Water and Electricity Tracking App
## Comprehensive Project Audit & Technical Architecture Review

**Date:** November 15, 2026  
**Project:** Final-Year Major Project — AquaWatt  
**Location:** `C:\Users\hp\Water-Electricity-Tracking-App`  
**Git Branch:** `feature/auth-and-consumption-forms`  
**Author / Auditor:** Antigravity System Agent (in collaboration with Student Developer)

---

## 1. Executive Summary

AquaWatt is an urban residential resource tracking and management platform built with a **FastAPI + SQLAlchemy + PostgreSQL** backend and a **Kivy + KivyMD** liquid-glass desktop/mobile frontend.

The project currently has a functional **Phase 1 MVP foundation** with recent extensions for:
- User registration and login with bcrypt password hashing and JWT bearer tokens.
- 1-to-1 Household demographic profile management.
- Monthly electricity consumption entry with appliance inventory counts.
- Monthly water consumption entry with fixture and habit notes.
- Summary and analytics API (`/consumption/summary`) computing per-person metrics and month-over-month trend changes.
- Liquid-glass frontend featuring an 8-screen navigation stack with sidebar layout and custom canvas graphics.
- Automated pytest test suite verifying core endpoints and edge cases.

**Critical Findings:**
1. **Machine Learning:** Zero datasets, ML scripts, or models exist in the repository currently. No ML training has been performed.
2. **Git Working Tree:** 14 modified files and 4 untracked directories/files exist unstaged in `feature/auth-and-consumption-forms`. All modifications are preserved intact.
3. **Test Suite:** The automated pytest suite contains **10 passing tests (100% pass rate)**. However, executing tests inside the Windows sandbox requires addressing binary DLL security policy for `psycopg2` C-extensions.
4. **Domain Model Limitations:** The current database model stores consumption only with creation timestamps (`created_at`) rather than explicit meter billing cycles, does not handle meter resets or previous/current meter sequences, does not store tariffs or monetary costs, and associates household profiles strictly 1-to-1 with a single user (preventing multi-member household sharing).

---

## 2. Technology Stack Verification

The repository was inspected to verify all active libraries, versions, and runtimes:

| Component | Technology | Version Detected | Status |
| :--- | :--- | :--- | :--- |
| **Runtime** | Python | 3.13.14 (in `.venv`) | Verified active |
| **Backend Framework** | FastAPI | 0.141.1 | Installed & operational |
| **ASGI Server** | Uvicorn | 0.54.0 | Installed |
| **ORM** | SQLAlchemy | 2.1.1 (2.0 declarative) | Configured with `pool_pre_ping` |
| **Database Driver** | psycopg2-binary | 2.9.13 | Connected to PostgreSQL port 5432 |
| **Data Validation** | Pydantic | 2.13.5 (Pydantic v2) | Strict type checking & validators |
| **Security / Auth** | bcrypt & PyJWT | bcrypt 5.0.0, PyJWT 2.15.1 | Salted hashing & HS256 tokens |
| **Testing** | pytest & Starlette TestClient | pytest 9.1.1, httpx 0.28.1 | 10 automated test cases |
| **Frontend UI** | Kivy & KivyMD | Kivy 2.3.1, KivyMD 2.0.0 | Liquid-glass desktop UI (960x680) |
| **Networking** | Requests | 2.34.2 | Synchronous HTTP client |
| **Graphics / Assets** | Pillow (PIL) | 12.3.0 | Asset generation script active |
| **Machine Learning** | pandas, NumPy, scikit-learn | **Not installed** | Required for Phase 2–4 |

---

## 3. Git Repository & Working Tree Status

- **Current Branch:** `feature/auth-and-consumption-forms`
- **Head Commit:** `d8f4cdf` (*"feat: implement Phase 1 auth, household profile, and consumption forms with PostgreSQL storage and KivyMD UI"*)

### Modified Uncommitted Files (14 files)
The working tree contains extensive uncommitted enhancements in active development:
1. `backend/app/routes/consumption.py`: Added `/consumption/summary` endpoint with per-person calculations and MoM percentage changes.
2. `backend/app/schemas/__init__.py`: Registered summary schema exports.
3. `backend/tests/test_api.py`: Extended test suite from 6 to 10 tests covering summary endpoint edge cases (zero baseline, missing profile, calculation accuracy).
4. `backend/tests/verify_flow.py`: Updated E2E verification script testing summary metrics.
5. `mobile/main.py`: Updated screen manager to include `dashboard` and `history` screens; resized window to widescreen desktop layout (960×680).
6. `mobile/screens/__init__.py`: Exported `DashboardScreen` and `HistoryScreen`.
7. `mobile/screens/electricity_screen.py`: Refactored to liquid-glass sidebar layout.
8. `mobile/screens/login_screen.py`: Refactored to liquid-glass card layout.
9. `mobile/screens/profile_screen.py`: Refactored to liquid-glass card layout.
10. `mobile/screens/register_screen.py`: Refactored with live validation feedback.
11. `mobile/screens/water_screen.py`: Refactored to liquid-glass sidebar layout.
12. `mobile/screens/welcome_screen.py`: Refactored to welcome view with server health indicator.
13. `mobile/services/api_client.py`: Added `get_consumption_summary()`, `get_electricity_history()`, `get_water_history()`, and `logout()`.
14. `mobile/widgets/glass_widgets.py`: Expanded with `GlassSidebar`, `GlassHeader`, `GlassCard` variants, and visual palette tokens.

### Untracked Files & Folders (4 items)
1. `backend/app/schemas/summary.py`: Pydantic schema for `ConsumptionSummaryResponse`, `ElectricitySummaryMetrics`, and `WaterSummaryMetrics`.
2. `mobile/screens/dashboard_screen.py`: Dashboard screen with greeting, dual metric cards, recent logs table, and navigation.
3. `mobile/screens/history_screen.py`: Consumption history screen with filter tabs (All, Electricity, Water).
4. `mobile/assets/`: Generated visual assets (`bg_water.png`, `bg_welcome.png`, `logo_droplet.png`, `logo_droplet_white.png`, `build_assets.py`).

*No uncommitted work was overwritten or reverted during this audit.*

---

## 4. Test Suite Execution & Recorded Results

The test suite was executed against the PostgreSQL test database:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\hp\Water-Electricity-Tracking-App
collected 10 items

backend/tests/test_api.py::test_health_check PASSED                      [ 10%]
backend/tests/test_api.py::test_root_endpoint PASSED                     [ 20%]
backend/tests/test_api.py::test_registration_validation_password_mismatch PASSED [ 30%]
backend/tests/test_api.py::test_user_registration_and_login_flow PASSED  [ 40%]
backend/tests/test_api.py::test_household_profile_and_consumption_flow PASSED [ 50%]
backend/tests/test_api.py::test_unauthorized_access_protection PASSED    [ 60%]
backend/tests/test_api.py::test_consumption_summary_missing_profile PASSED [ 70%]
backend/tests/test_api.py::test_consumption_summary_with_profile_no_records PASSED [ 80%]
backend/tests/test_api.py::test_consumption_summary_calculation_accuracy_and_trends PASSED [ 90%]
backend/tests/test_api.py::test_consumption_summary_zero_baseline_division_safety PASSED [100%]

======================== 10 passed, 1 warning in 5.56s ========================
```

### Sandbox Execution Note
Under Windows Standard Sandbox Mode, loading C-extension dynamic-link libraries located in the virtual environment (`psycopg2/_psycopg.pyd`) triggers an Application Control policy error:
`ImportError: DLL load failed while importing _psycopg: An Application Control policy has blocked this file.`
When run with standard OS privileges (or `BypassSandbox: true`), `psycopg2` loads smoothly and all 10 tests pass without error.

---

## 5. Detailed Feature Status Matrix

| Feature Module | Prompt Requirement | Current Implementation Status | Notes |
| :--- | :--- | :--- | :--- |
| **Authentication** | Register, Login, JWT, Bcrypt | **Implemented & Tested** | Secure password hashing, email uniqueness, bearer token validation in place. |
| **User Profile** | Household size, type, location | **Implemented & Tested** | 1-to-1 relationship with `User`. Basic occupancy notes captured. |
| **Electricity Logging** | Monthly kWh, appliance counts | **Implemented & Tested** | Stores `monthly_consumption_kwh`, appliance counts, and free-text usage notes. |
| **Water Logging** | Monthly litres, fixture habits | **Implemented & Tested** | Stores `monthly_consumption_litres`, shower counts, wash cycles, pump runtime. |
| **Summary & Metrics** | Per-capita metrics, MoM trends | **Implemented & Tested** | Computes per-person kWh and water LPCD; handles 0-baseline division safely. |
| **Mobile Navigation** | Multi-screen flow, UI theme | **Implemented** | 8 screens connected via `ScreenManager` and `GlassSidebar`. |
| **Liquid-Glass Design** | Deep teal, aqua, pale mint | **Implemented** | Custom Kivy canvas shaders/shapes, frosted cards, and branding assets active. |
| **Household Sharing** | Multi-tenant households, invites | **Missing** | Current schema only supports single-user 1-to-1 profile. |
| **Meter Readings** | Previous/current sequence, resets | **Missing** | App only captures aggregate monthly totals; no meter index sequence. |
| **Tariffs & Budgets** | Electricity/Water rates, targets | **Missing** | No tariff or financial cost calculation engine exists. |
| **Appliance Tracking** | Wattage, hours/day, cost estimates | **Partially Implemented** | Only raw appliance count is stored; no power rating or cost estimation. |
| **Water Activity Tracking**| Volume/occurrence, daily frequency | **Partially Implemented** | Fixture frequency is stored as free-text strings; no volume computation. |
| **Renewable Tracking** | Solar generation, rainwater harvest | **Missing** | Not modeled in database or UI. |
| **Weekly Challenges** | Savings goals, streaks, milestones | **Missing** | Not modeled in database or UI. |
| **Bill OCR** | PDF/Image meter reading extraction| **Missing** | Not implemented. |
| **Peer Comparison** | Anonymized cluster benchmarking | **Missing** | Requires multiple households and normalization baselines. |
| **AI Assistant** | Natural language utility advisor | **Missing** | Optional LLM integration not yet implemented. |
| **Reports & Export** | PDF reports, CSV export | **Missing** | Not implemented. |
| **ML Dataset** | Real-world benchmark data | **Missing** | No dataset added or prepared yet. |
| **ML Forecasting** | Time-series regression (kWh, L) | **Missing** | No models, training scripts, or inference endpoints exist yet. |
| **Anomaly Detection** | Unusual spike detection | **Missing** | Not implemented. |

---

## 6. Architecture & Code Limitations

### Architectural Issues
1. **Coupling of User and Household:**  
   In `models/profile.py`, `HouseholdProfile` has `user_id = Column(Integer, ForeignKey("users.id"), unique=True)`. This makes household data strictly single-user. A proper household management system requires a `Household` entity with a many-to-many or one-to-many `HouseholdMember` relationship supporting roles (Owner, Member) and invitation tokens.
2. **Lack of Explicit Billing Cycle / Timestamp Fidelity:**  
   Consumption records currently rely solely on PostgreSQL `server_default=func.now()` for `created_at`. If a user logs a bill from last month, the creation date reflects the moment of submission rather than the actual consumption period (`billing_period_start`, `billing_period_end`).
3. **No Incremental Meter Reading Model:**  
   Users currently enter an aggregate monthly kWh or Litre figure. Real utility tracking requires recording meter dial readings (`previous_reading`, `current_reading`, `reading_date`, `meter_multiplier`, `is_reset`) so that consumption is verified mathematically ($Reading_{current} - Reading_{previous}$).
4. **Tariffs and Cost Logic Missing:**  
   There is no concept of utility tariffs (e.g., \$ / kWh or ₹ / kWh, tiered slab pricing, water fixed charges). As a result, budget tracking and estimated bill forecasting cannot be calculated.
5. **Appliance and Water Activities Stored as Unstructured Strings:**  
   Fields such as `washing_machine_usage = Column(String(100))` and `usage_notes = Column(Text)` prevent mathematical modeling. They need structured schemas: `ApplianceInventory` (watts, quantity, hours_per_day) and `WaterActivity` (litres_per_use, frequency_per_day).
6. **Mobile Networking Synchronicity:**  
   `ApiClient` in `mobile/services/api_client.py` uses synchronous `requests.get` / `requests.post`. While timeouts are set to 8.0s, calling network operations on the Kivy main thread can cause slight UI stuttering during slow connections.
7. **Database Migrations:**  
   Tables are created using `Base.metadata.create_all(bind=engine)` inside the FastAPI lifespan handler. There is no Alembic migration setup, meaning any schema modification requires manual migration or recreation.

---

## 7. Audit Conclusion & Next Steps

The AquaWatt core foundation is solid and well-structured: the FastAPI backend follows clean REST design with Pydantic validation, the test suite achieves 100% pass rate on current features, and the Kivy frontend provides an aesthetic liquid-glass interface.

To elevate this into a major final-year project, the immediate priorities are:
1. Conduct verified research into real-world household electricity and water datasets (`machine_learning/DATASET_RESEARCH.md`).
2. Establish the machine-learning pipeline architecture and dataset acquisition plan (`AQUAWATT_IMPLEMENTATION_PLAN.md`).
3. Prepare preprocessing scripts and model training pipelines with cross-validated performance metrics.
4. Integrate ML inference with authenticated FastAPI endpoints and surface predictions clearly on the dashboard.

