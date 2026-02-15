from fastapi import FastAPI
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

app.include_router(routes.router)
app.include_router(admin_router)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Wallet Intelligence API"}
