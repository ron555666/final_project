from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.database import engine, Base
from app import models
from app.routes import stores, auth, reviews
from app.rate_limit import limiter

# create the table
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Store Locator API",
    description="Final Project - Store Locator Service",
    version="1.0.0"
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(stores.router)
app.include_router(auth.router)
app.include_router(reviews.router)


@app.get("/")
def root():
    return {"message": "Store Locator API is running"}