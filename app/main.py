import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes
from .api.admin_routes import admin_router
from .core.models import Base
from .core.config import engine

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Company Wallet Intelligence API",
    description="An API to analyze company user wallets for product, marketing, and risk intelligence.",
    version="1.0.0"
)

# M8: CORS middleware — allow frontend and configured origins
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.include_router(admin_router)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Wallet Intelligence API"}
