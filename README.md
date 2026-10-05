# Water & Electricity Tracking App (AquaWatt)

> **Final-Year Major Project — Phase 1 MVP Foundation**  
> A modern mobile application designed for urban residential households to track water and electricity consumption, normalize usage against household context, and prepare the foundation for behavioral recommendations and nudges.

---

## 1. Project Overview

Urban residential households often struggle to understand their resource footprints because utility bills only provide aggregate figures without context. High consumption does not necessarily imply inefficiency—a home of 5 members with 3 bathrooms naturally consumes more than a single-occupant flat.

The **AquaWatt Tracker** addresses this by:
1. Recording household occupancy, structure, and appliance inventory.
2. Collecting monthly electricity consumption (kWh) with appliance-level context.
3. Collecting monthly water consumption (litres) with fixture, duration, and utility habits.
4. Persisting all data in a structured PostgreSQL schema, laying the groundwork for personalized baselines, gap analysis, and behavioral nudges in future phases.

---

## 2. Current Implementation Scope (Phase 1 MVP)

This phase establishes the core foundational pipeline:
- **User Authentication**: Secure user registration & login with bcrypt password hashing and signed JWT bearer tokens.
- **Household Profile**: Collection of household member count, house type, location, bathroom count, daytime occupancy, and unusual occupancy notes.
- **Electricity Consumption Tracking**: Monthly kWh log with appliance quantities (AC, fans, fridge, TV, geyser, washing machine, water pump, other appliances) and usage duration notes.
- **Water Consumption Tracking**: Monthly litres log with daily shower counts, average duration, bucket usage, washing machine cycles, garden watering, vehicle washing, and pump runtimes.
- **PostgreSQL Persistence**: Fully normalized relational schema with cascading foreign keys and timestamps.
- **Glassmorphic Mobile UI**: Fluid 6-screen navigation in Kivy & KivyMD featuring translucent cards, ambient gradients, tactile counters, responsive layouts, and success modals.

> **Note on Scope**: The recommendation engine, dashboard analytics, ML models, nudge notifications, weather integration, and IoT smart meter integrations are planned for future phases and are intentionally excluded from Phase 1.

---

## 3. Technology Stack

### Backend
- **Python 3.13**
- **FastAPI**: Modern, high-performance async REST API framework.
- **SQLAlchemy 2.0**: Declarative ORM for relational modeling.
- **PostgreSQL**: Production-grade relational database (`water_electricity_tracking`).
- **Pydantic v2**: Strict request and response data validation.
- **bcrypt & PyJWT**: Secure password hashing and stateless token authentication.
- **pytest & HTTPX**: Automated test suite and client simulation.

### Mobile Frontend
- **Python 3.13**
- **Kivy 2.3.1**: Cross-platform Python GUI framework with custom canvas graphics.
- **KivyMD 2.0.0**: Material Design components and dark theme foundations.
- **Requests**: HTTP networking communicating with the FastAPI REST API.

---

## 4. Project Structure

```text
Water-Electricity-Tracking-App/
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app initialization, CORS, routers & startup table creation
│   │   ├── database.py            # SQLAlchemy engine, session maker, get_db dependency
│   │   ├── test_db.py             # Quick DB connectivity script
│   │   ├── models/                # SQLAlchemy database entities
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # User credentials & profile relationship
│   │   │   ├── profile.py         # HouseholdProfile (members, type, location)
│   │   │   ├── electricity.py     # ElectricityConsumption & appliance breakdown
│   │   │   └── water.py           # WaterConsumption & fixture usage details
│   │   ├── schemas/               # Pydantic v2 data transfer schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # UserCreate, UserLogin, UserResponse, TokenResponse
│   │   │   ├── profile.py         # HouseholdProfileCreate, HouseholdProfileResponse
│   │   │   ├── electricity.py     # ElectricityConsumptionCreate, Response
│   │   │   └── water.py           # WaterConsumptionCreate, Response
│   │   ├── routes/                # FastAPI endpoint routers
│   │   │   ├── auth.py            # /auth/register, /auth/login, /auth/me
│   │   │   ├── profile.py         # /profile (GET, POST)
│   │   │   └── consumption.py     # /consumption/electricity, /consumption/water
│   │   └── services/
│   │       └── auth_service.py    # bcrypt hashing, JWT issuance & token verification
│   ├── tests/
│   │   ├── test_api.py            # Pytest suite for all endpoints & validations
│   │   └── verify_flow.py         # End-to-end client verification script
│   └── requirements.txt
│
├── mobile/
│   ├── main.py                    # Kivy/KivyMD application entrypoint
│   ├── screens/                   # Screen views
│   │   ├── __init__.py
│   │   ├── welcome_screen.py      # Splash / brand introduction with API health badge
│   │   ├── login_screen.py        # Resident sign-in with live error handling
│   │   ├── register_screen.py     # New user registration with password match checks
│   │   ├── profile_screen.py      # Household demographics & occupancy form
│   │   ├── electricity_screen.py  # Monthly kWh & appliance inventory form
│   │   └── water_screen.py        # Monthly Litres & water fixtures form
│   ├── widgets/
│   │   ├── __init__.py
│   │   └── glass_widgets.py       # GlassCard, GlassInput, ModernButton, CounterWidget, Popups
│   ├── services/
│   │   └── api_client.py          # HTTP API client connecting mobile to FastAPI
│   └── requirements.txt
│
├── docs/
├── .env                           # Environment secrets (ignored from Git)
├── .gitignore
└── README.md
```

---

## 5. PostgreSQL Database Setup

1. Ensure PostgreSQL is installed and running locally on port `5432`.
2. Create the project database (if not already existing):
   ```sql
   CREATE DATABASE water_electricity_tracking;
   ```
3. Set the database connection string in your `.env` file at the project root:
   ```env
   DATABASE_URL=postgresql://postgres:<your_password>@localhost:5432/water_electricity_tracking
   JWT_SECRET_KEY=your_secure_random_jwt_secret_key_here
   ```

### Database Tables Created
The application automatically creates and manages four tables in PostgreSQL upon startup:
1. `users`: Stores user credentials (`id`, `full_name`, `email`, `hashed_password`, `is_active`, `created_at`).
2. `household_profiles`: Stores 1-to-1 household context (`id`, `user_id`, `household_members`, `house_type`, `location`, `num_bathrooms`, `people_usually_at_home`, `unusual_occupancy`, `created_at`, `updated_at`).
3. `electricity_consumption`: Stores monthly electricity logs with foreign key to profile (`id`, `profile_id`, `monthly_consumption_kwh`, appliance counts, `other_appliances`, `usage_notes`, `created_at`).
4. `water_consumption`: Stores monthly water logs with foreign key to profile (`id`, `profile_id`, `monthly_consumption_litres`, `num_showers`, `avg_shower_duration_mins`, `bucket_usage`, `washing_machine_usage`, `garden_watering`, `vehicle_washing`, `water_pump_usage`, `other_water_usage`, `created_at`).

---

## 6. How to Run the Backend (FastAPI)

1. **Activate the virtual environment**:
   ```powershell
   # Windows PowerShell
   backend\.venv\Scripts\Activate.ps1
   ```
2. **Install backend dependencies** (if not already installed):
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. **Start the FastAPI server with live reload**:
   ```powershell
   python -m uvicorn main:app --app-dir backend/app --host 127.0.0.1 --port 8000 --reload
   ```
4. **Access Interactive API Docs**:
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 7. How to Run the Mobile Application (Kivy / KivyMD)

1. Ensure the FastAPI backend is running on `http://127.0.0.1:8000`.
2. From the root directory, launch the Kivy mobile application:
   ```powershell
   backend\.venv\Scripts\python.exe mobile/main.py
   ```
3. The mobile window opens emulating a modern mobile screen (400×780) with interactive glassmorphic cards, steppers, and smooth transitions.

---

## 8. Current API Endpoints

| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Server health status check | No |
| `GET` | `/` | Root API status and version | No |
| `POST` | `/auth/register` | Register new resident, returns JWT token | No |
| `POST` | `/auth/login` | Authenticate resident credentials, returns JWT | No |
| `GET` | `/auth/me` | Fetch currently authenticated user info | Yes |
| `GET` | `/profile` | Fetch logged-in user's household profile | Yes |
| `POST` | `/profile` | Create or update household profile | Yes |
| `POST` | `/consumption/electricity` | Submit monthly kWh with appliance quantities | Yes |
| `GET` | `/consumption/electricity` | Retrieve user's electricity consumption history | Yes |
| `POST` | `/consumption/water` | Submit monthly litres with fixture habits | Yes |
| `GET` | `/consumption/water` | Retrieve user's water consumption history | Yes |

---

## 9. Running Tests

Execute the automated test suite with pytest:
```powershell
backend\.venv\Scripts\pytest.exe backend/tests/test_api.py -v
```

Execute the full end-to-end integration flow test:
```powershell
backend\.venv\Scripts\python.exe backend/tests/verify_flow.py
```

---

## 10. Current Limitations (Phase 1)
- Data entry is manual (monthly bill entry) rather than continuous automated IoT telemetry.
- Recommendations and baseline comparisons are not yet computed (scheduled for Phase 3).
- Analytics charts and historical trend visualizations are not yet rendered in the mobile UI.

---

## 11. Future Phases Roadmap

- **Phase 2 — Analytics & Baselines**:
  - Consumption historical timeline
  - Household-normalized baseline calculations (per-capita and per-sqft metrics)
  - User-defined reduction targets and gap analysis
- **Phase 3 — Behavioral Recommendation Engine**:
  - Rule-based heuristic behavioral engine
  - Contextual nudges based on occupancy and appliance count
  - Habit tracking and gamified savings milestones
- **Phase 4 — Context & Machine Learning**:
  - Weather and seasonal integration (temperature, humidity, precipitation)
  - Unsupervised clustering for peer comparison (similar households)
  - Push notifications and smart alerts
- **Phase 5 — Smart Meter / IoT Integration**:
  - Real-time pulse/smart-meter ingestion via MQTT/WebSockets
  - Anomaly and leak detection algorithms
