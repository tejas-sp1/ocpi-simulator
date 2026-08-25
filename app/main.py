from fastapi import FastAPI

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