# AquaWatt — Phase 6.2A: Alembic Setup and Migration Script Authoring Report
## Database Migration Engine Configuration & Household Migration Specification

**Project:** AquaWatt — Water and Electricity Tracking App (Final-Year College Major Project)  
**Location:** `C:\Users\hp\Water-Electricity-Tracking-App`  
**Git Branch:** `feature/auth-and-consumption-forms`  
**Phase:** 6.2A — Alembic Setup & Migration Authoring Only  
**Date:** November 15, 2026  
**Status:** **CONFIGURED & AUTHORED — MIGRATIONS NOT EXECUTED**  

---

## Executive Summary

Phase 6.2A establishes the migration infrastructure for AquaWatt by configuring **Alembic**, authoring an accurate **baseline schema revision** reflecting the existing production/development tables, and authoring the **Phase 6 multi-member household migration revision** with comprehensive data backfill and safety constraints.

> [!CAUTION]
> **MIGRATION EXECUTION STATUS: STRICTLY NOT EXECUTED**  
> Per Phase 6.2A requirements, zero DDL statements have been executed, no migration scripts have been run (`alembic upgrade`, `alembic downgrade`, and `alembic stamp` were **not** executed), no database records were inserted, modified, or deleted, and no PostgreSQL sequences were altered. All database state remains identical to Phase 6.1.

---

## 1. Initial Git & Database Inspection Findings

Prior to authoring any files, a read-only audit of Git and the active PostgreSQL instance was performed:

### 1.1 Git Branch & Working Tree
* **Branch:** `feature/auth-and-consumption-forms`
* **Pre-existing Modified Files (16):**
  * `.gitignore`
  * `backend/app/main.py`
  * `backend/app/routes/consumption.py`
  * `backend/app/schemas/__init__.py`
  * `backend/tests/test_api.py`
  * `backend/tests/verify_flow.py`
  * `mobile/main.py`
  * `mobile/screens/__init__.py`
  * `mobile/screens/electricity_screen.py`
  * `mobile/screens/login_screen.py`
  * `mobile/screens/profile_screen.py`
  * `mobile/screens/register_screen.py`
  * `mobile/screens/water_screen.py`
  * `mobile/screens/welcome_screen.py`
  * `mobile/services/api_client.py`
  * `mobile/widgets/glass_widgets.py`
* **Pre-existing Untracked Artifacts:** Reports (`AQUAWATT_PROJECT_AUDIT.md`, `PHASE6_1_DATABASE_DESIGN.md`, etc.), ML modules, and new backend files.
* **Preservation Status:** All modified and untracked files remain preserved intact.

### 1.2 PostgreSQL Schema & Sequence Inspection (Read-Only)
A direct inspection via SQLAlchemy inspector confirmed exactly **four public tables** and their underlying sequence counters:

| Table Name | Live Row Count | Primary Key | Sequences & Current State | Constraints & Key Indexes |
| :--- | :---: | :--- | :--- | :--- |
| `users` | **165** | `id` (INTEGER) | `users_id_seq` (last_value=180, is_called=True) | `ix_users_email` (UNIQUE), `ix_users_id` |
| `household_profiles` | **80** | `id` (INTEGER) | `household_profiles_id_seq` (last_value=84, is_called=True) | `household_profiles_user_id_key` (UNIQUE), `ix_household_profiles_id` |
| `electricity_consumption` | **101** | `id` (INTEGER) | `electricity_consumption_id_seq` (last_value=106, is_called=True) | `ix_electricity_consumption_profile_id`, `ix_electricity_consumption_id` |
| `water_consumption` | **100** | `id` (INTEGER) | `water_consumption_id_seq` (last_value=105, is_called=True) | `ix_water_consumption_profile_id`, `ix_water_consumption_id` |

* **Orphan Audit:** Verified `0` orphaned household profiles, `0` orphaned electricity records, and `0` orphaned water records.
* **Credentials Notice:** Database connection strings, passwords, and JWT secret tokens were omitted from all configuration files and report logs.

### 1.3 Test Suite Database Isolation Analysis
* An inspection of `backend/tests/test_api.py` and `backend/tests/test_ml_endpoints.py` revealed that tests import `from main import app` and `from database import SessionLocal`, executing live transactions directly against the database specified in `DATABASE_URL`.
* Tests create transient user accounts (`user_{timestamp}@example.com`) and consumption records that are not rolled back on teardown.
* **Safety Conclusion:** Running `pytest` against the shared database inserts live rows into `users` and increments `users_id_seq`. In accordance with Phase 6.2A rules (*"If a validation step could modify the existing database, do not run it"*), tests were not executed during this migration authoring phase.

---

## 2. Alembic Configuration

Alembic (version `1.20.1`) was added to `backend/requirements.txt` and installed into the backend virtual environment (`backend/.venv`).

### 2.1 Configuration Files Created

1. **`alembic.ini` (Root Level):**
   * Configured with `script_location = %(here)s/backend/alembic` to allow running migrations seamlessly from the workspace root.
2. **`backend/alembic.ini` (Backend Subdirectory):**
   * Configured with `script_location = %(here)s/alembic` for developers executing Alembic commands directly inside `backend/`.
3. **`backend/alembic/env.py`:**
   * Automatically adds `backend/app` to `sys.path`.
   * Securely loads `DATABASE_URL` via `python-dotenv` from `.env` without hardcoding credentials.
   * Imports `Base` from `database` and registers all existing models (`import models`).
   * Binds `target_metadata = Base.metadata`.
   * Supports both **offline mode** (`run_migrations_offline`, generating SQL scripts via `literal_binds=True`) and **online mode** (`run_migrations_online`, utilizing `pool.NullPool` to prevent hanging connection pools).

### 2.2 FastAPI Startup & Migration Independence
* `Base.metadata.create_all(bind=engine)` inside `backend/app/main.py` is **retained unchanged** for this phase.
* In a future approved phase (Phase 6.3/6.4), once Alembic migrations are formally applied, `create_all` will be safely transitioned to an optional development flag or replaced by automated migration checks.

---

## 3. Schema Revision Specifications

Two migration revisions have been authored in `backend/alembic/versions/`:

```text
backend/alembic/versions/
├── 0001_baseline_schema.py            [REVISION 1: Existing Schema Baseline]
└── 0002_add_household_architecture.py  [REVISION 2: Household Architecture & Backfill]
```

Alembic history verification confirms the Directed Acyclic Graph (DAG):
```text
<base> -> 0001_baseline_schema -> 0002_add_household_architecture (head)
```

---

## 4. Revision 1: Baseline Schema (`0001_baseline_schema.py`)

### 4.1 Purpose & Execution Status
* **Status:** **NOT EXECUTED.**
* **Revision ID:** `0001_baseline_schema` | **Down Revision:** `None`
* **Scope:** Fully documents the exact existing schema of `users`, `household_profiles`, `electricity_consumption`, and `water_consumption`.

### 4.2 Phase 6.2B Stamping Procedure (Preventing Table Recreation)
Because the development/production database already contains live records, running `alembic upgrade 0001_baseline_schema` in Phase 6.2B would attempt to re-create existing tables and fail with `table already exists`.

Instead, Phase 6.2B will establish the baseline safely by executing:
```bash
alembic stamp 0001_baseline_schema
```
This writes the `0001_baseline_schema` revision ID into the `alembic_version` table without issuing any DDL statements, safely declaring the current database state as the baseline.

---

## 5. Revision 2: Proposed Household Migration (`0002_add_household_architecture.py`)

### 5.1 Purpose & Execution Status
* **Status:** **NOT EXECUTED.**
* **Revision ID:** `0002_add_household_architecture` | **Down Revision:** `0001_baseline_schema`

### 5.2 Schema Additions
1. **`households` Table:**
   * Columns: `id` (INTEGER PK), `household_name` (VARCHAR 100), `address` (VARCHAR 255), `house_type` (VARCHAR 50), `num_bathrooms` (INTEGER), `manual_member_count` (INTEGER), `people_usually_at_home` (INTEGER NULL), `unusual_occupancy` (VARCHAR 50), `invite_code_hash` (VARCHAR 64 UNIQUE), `created_by` (INTEGER FK -> `users.id` `ON DELETE SET NULL`), `created_at` (TIMESTAMP), `updated_at` (TIMESTAMP), `deleted_at` (TIMESTAMP NULL for soft deletion).
2. **`household_members` Table:**
   * Columns: `id` (INTEGER PK), `household_id` (INTEGER FK -> `households.id` `ON DELETE CASCADE`), `user_id` (INTEGER FK -> `users.id` `ON DELETE CASCADE`), `role` (VARCHAR 20 with check constraint `'OWNER', 'ADMIN', 'MEMBER'`), `membership_status` (VARCHAR 20 with check constraint `'ACTIVE', 'INVITED', 'INACTIVE'`), `joined_at` (TIMESTAMP).
   * Unique Constraint: `UniqueConstraint("household_id", "user_id", name="uq_household_member")`.
3. **`electricity_consumption` & `water_consumption` Updates:**
   * Added `household_id` (INTEGER FK -> `households.id` `ON DELETE RESTRICT`).
   * Added `submitted_by_user_id` (INTEGER FK -> `users.id` `ON DELETE SET NULL`).
   * Added composite indexes: `ix_elec_household_created` and `ix_water_household_created` on `(household_id, created_at DESC)`.
   * Retained legacy `profile_id` column to ensure 100% backward compatibility for existing code.

---

## 6. Mandatory Safety Safeguards Implementation

### Safeguard A: Protecting Consumption History
* **Problem:** If a household or user account were deleted with cascading foreign keys (`ON DELETE CASCADE`), months or years of utility billing records could be permanently erased.
* **Implemented Solution:**
  1. Foreign keys `fk_elec_consumption_household` and `fk_water_consumption_household` are configured with **`ondelete='RESTRICT'`**. PostgreSQL will actively block any hard deletion of a `Household` record that has associated consumption records.
  2. The `households` table includes a **`deleted_at`** column to support soft-deletion (archiving) rather than hard deletion.
  3. `submitted_by_user_id` uses **`ondelete='SET NULL'`**: If a contributing household member leaves or deletes their personal account, the consumption entry remains attached to the household with `submitted_by_user_id = NULL`.

### Safeguard B: Secure Invite Codes
* **Problem:** Storing raw invite codes in the database exposes households to unauthorized joining if database backups or dumps are accessed, or if brute-force code enumeration occurs.
* **Implemented Solution:**
  1. Plaintext join codes are **never stored** in the database.
  2. The schema stores **`invite_code_hash`** (a 64-character hex string representing the SHA-256 cryptographic digest of the join code).
  3. When an invite token is generated (e.g., `AQ-9B4X2K`), the backend computes `hashlib.sha256(token.encode('utf-8')).hexdigest()`.
  4. A unique index `ix_households_invite_code_hash` guarantees rapid lookup while preventing duplicate tokens.
  5. Application-layer requirements documented for Phase 6.4: Maximum 5 failed join attempts per user per hour, and on-demand invite code rotation (`POST /households/{id}/invite-code/rotate`).

### Safeguard C: Exactly One Active Owner Enforcement
* **Problem:** Multi-member households must maintain clear ownership authority without split brain (multiple owners) or abandonment (zero owners).
* **Implemented Solution:**
  1. **Upper Bound (At Most One Owner):** Enforced at the PostgreSQL engine level via a partial unique index:
     ```sql
     CREATE UNIQUE INDEX uq_one_active_owner_per_household 
     ON household_members (household_id) 
     WHERE role = 'OWNER' AND membership_status = 'ACTIVE';
     ```
     PostgreSQL will instantly reject any transaction attempting to create or promote a second active owner in the same household.
  2. **Lower Bound (At Least One Owner):** A partial index cannot enforce a minimum count. This is guaranteed through two layers:
     * *Migration Layer:* The backfill script guarantees that 100% of migrated households receive exactly one active `OWNER` membership.
     * *Service Layer (Phase 6.3):* Ownership transfer is transactional. An owner cannot self-demote or leave a household without explicitly designating an active successor. Account deletion for an owner of a multi-member household is blocked until ownership is transferred.

### Safeguard D: PostgreSQL Sequence Synchronization
* **Problem:** In PostgreSQL, inserting rows with explicit primary keys (`INSERT INTO households (id, ...) VALUES (1, ...)`) does not automatically advance the underlying sequence (`households_id_seq`). The next insert without an explicit ID would attempt `id = 1` and crash with a duplicate primary key error.
* **Implemented Solution:**
  The migration script concludes with safe sequence synchronization queries:
  ```sql
  SELECT setval(
      pg_get_serial_sequence('households', 'id'),
      COALESCE((SELECT MAX(id) FROM households), 1),
      (SELECT MAX(id) FROM households) IS NOT NULL
  );
  SELECT setval(
      pg_get_serial_sequence('household_members', 'id'),
      COALESCE((SELECT MAX(id) FROM household_members), 1),
      (SELECT MAX(id) FROM household_members) IS NOT NULL
  );
  ```

---

## 7. Deterministic Data Backfill Algorithm

The migration script executes the backfill transactionally in Step 4:

1. **Pre-condition Validation:**
   * Queries all `household_profiles` joined with `users`.
   * Checks that every profile's `user_id` corresponds to a valid existing record in `users`.
   * If any orphaned reference is detected, the script raises `RuntimeError` and aborts the transaction before modifying any data.
2. **Household & Membership Population:**
   * Iterates through all existing profiles (expected: 80).
   * Inserts into `households` preserving the original `HouseholdProfile.id` as `households.id` (maintaining 1:1 ID parity).
   * Sets `address = profile.location`, `house_type = profile.house_type`, `num_bathrooms = profile.num_bathrooms`, `manual_member_count = profile.household_members`, `created_by = profile.user_id`.
   * Generates a cryptographically secure token and stores its SHA-256 hash in `invite_code_hash`.
   * Inserts a corresponding row into `household_members` with `role = 'OWNER'` and `membership_status = 'ACTIVE'`.
3. **Consumption Mapping:**
   * Updates `electricity_consumption`: sets `household_id = profile_id` and `submitted_by_user_id = profile.user_id`.
   * Updates `water_consumption`: sets `household_id = profile_id` and `submitted_by_user_id = profile.user_id`.
4. **Post-condition Verification:**
   * Queries for any consumption rows where `household_id IS NULL`. If any exist, it raises `RuntimeError` and aborts.
   * Executes `ALTER TABLE electricity_consumption ALTER COLUMN household_id SET NOT NULL;`
   * Executes `ALTER TABLE water_consumption ALTER COLUMN household_id SET NOT NULL;`

---

## 8. Migration Reversibility Assessment

The `downgrade()` function in `0002_add_household_architecture.py` drops added constraints, indexes, columns, and tables in exact reverse order.

### Reversibility Caveats & Data Loss Risks:
* **Pre-existing Legacy Data:** Safe. Because `household_profiles` and legacy `profile_id` references are retained throughout Phase 6, rolling back from `0002` to `0001` preserves the original 80 profiles and their consumption links.
* **New Phase 6 Multi-Member Data:** **Lossy.** Any co-tenants or additional family members added to `household_members` after Phase 6.2B execution would be destroyed during a downgrade. Any newly created households without a legacy `household_profile` counterpart would be dropped.

---

## 9. Validation Performed & Results

Without executing migrations against the database, the following checks were performed:

1. **Python Compilation (`py_compile`):**
   * Verified `backend/alembic/env.py`: **0 errors.**
   * Verified `backend/alembic/versions/0001_baseline_schema.py`: **0 errors.**
   * Verified `backend/alembic/versions/0002_add_household_architecture.py`: **0 errors.**
2. **Alembic History Inspection:**
   * Executed `python -m alembic history` without connecting to PostgreSQL.
   * Confirmed clean revision chain from `<base>` to `0001_baseline_schema` to `0002_add_household_architecture (head)`.
3. **Database Read-Only Audit:**
   * Verified table list (`['electricity_consumption', 'household_profiles', 'users', 'water_consumption']`).
   * Verified row counts (`users`: 165, `household_profiles`: 80, `electricity_consumption`: 101, `water_consumption`: 100).
   * Verified sequence states (`users_id_seq`: 180, `household_profiles_id_seq`: 84, `electricity_id_seq`: 106, `water_id_seq`: 105).
   * Confirmed zero schema modifications, zero DDL execution, and zero sequence alterations.

---

## 10. Step-by-Step Procedure for Phase 6.2B (Execution)

When Phase 6.2B is approved, execution must follow these exact steps:

```bash
# Step 1: Navigate to project root
cd C:\Users\hp\Water-Electricity-Tracking-App

# Step 2: Establish baseline stamp (DO NOT run upgrade on 0001)
.\backend\.venv\Scripts\python.exe -m alembic stamp 0001_baseline_schema

# Step 3: Verify alembic_version table contains '0001_baseline_schema'
.\backend\.venv\Scripts\python.exe -m alembic current

# Step 4: Execute Phase 6 household architecture migration and backfill
.\backend\.venv\Scripts\python.exe -m alembic upgrade head

# Step 5: Verify post-migration state
# Expected:
# - households: 80 rows
# - household_members: 80 rows (all role='OWNER')
# - electricity_consumption: 101 rows (household_id NOT NULL)
# - water_consumption: 100 rows (household_id NOT NULL)
# - sequences: households_id_seq and household_members_id_seq synchronized to 80+
```

---

## 11. Final Safety Verification Sign-Off

- [x] **Git Branch:** `feature/auth-and-consumption-forms` (Unchanged).
- [x] **Uncommitted Work:** All 16 modified application files preserved.
- [x] **Database Tables:** 4 original tables intact; no new tables created.
- [x] **Database Row Counts:** 165 users, 80 profiles, 101 electricity, 100 water (Unchanged).
- [x] **PostgreSQL Sequences:** Unchanged (`last_value`: 180, 84, 106, 105).
- [x] **DDL Executed:** **None.**
- [x] **Migrations Applied:** **None (Status: NOT EXECUTED).**

*Report prepared and verified by Antigravity System Agent. Ready for review and Phase 6.2B approval.*

