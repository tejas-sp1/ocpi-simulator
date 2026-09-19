from dotenv import load_dotenv

# Load variables from .env BEFORE importing modules
# that use environment variables.
load_dotenv(override=True)

from fastapi import FastAPI

from app.modules.versions.router import router as versions_router
from app.modules.credentials.router import router as credentials_router
from app.modules.locations.router import router as locations_router


app = FastAPI(
    title="OCPI 2.2.1-d2 Simulator"
)


app.include_router(versions_router)
app.include_router(credentials_router)
app.include_router(locations_router)