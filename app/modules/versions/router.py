from fastapi import APIRouter

router = APIRouter(
    prefix="/ocpi",
    tags=["Versions"],
)


@router.get("/cpo/versions")
def get_cpo_versions():
    return [
        {
            "version": "2.2.1",
            "url": "http://localhost:8000/ocpi/cpo/2.2.1",
        }
    ]


@router.get("/cpo/2.2.1")
def get_cpo_version_details():
    return {
        "version": "2.2.1",
        "endpoints": [
            {
                "identifier": "credentials",
                "role": "RECEIVER",
                "url": "http://localhost:8000/ocpi/cpo/2.2.1/credentials",
            }
        ],
    }