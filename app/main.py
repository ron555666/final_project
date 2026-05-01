from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import os
from fastapi.middleware.cors import CORSMiddleware

# Internal module imports
from app.database import engine, Base
from app import models
from app.routes import stores, auth, reviews, admin_users
from app.rate_limit import limiter

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Load allowed CORS origins from environment variables
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

# Initialize FastAPI application
app = FastAPI(
    title="Store Locator API",
    description="Final Project - Store Locator Service",
    version="1.0.0"
)

# Rate limiting configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(stores.router)
app.include_router(stores.public_router)
app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(admin_users.router)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Store Locator API is running"}

# System health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}