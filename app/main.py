from fastapi import FastAPI
from app.modules.credentials.router import router as credentials_router
from app.modules.versions.router import router as versions_router

app = FastAPI(
    title="OCPI 2.2.1-d2 Simulator",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "name": "OCPI 2.2.1-d2 Simulator",
        "supported_roles": ["CPO", "EMSP"],
        "status": "running",
    }


app.include_router(versions_router)
app.include_router(credentials_router)