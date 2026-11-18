import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models  # Ensures all models are registered before create_all
from routes import auth, consumption, profile, ml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("water-electricity-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in PostgreSQL
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down API server...")


app = FastAPI(
    title="Water & Electricity Tracking App",
    description="Backend REST API for urban household water and electricity consumption tracking.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for mobile application and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(consumption.router)
app.include_router(ml.router)


@app.get("/")
def root():
    return {
        "app": "Water & Electricity Tracking App",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }