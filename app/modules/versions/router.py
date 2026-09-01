from fastapi import APIRouter
from pydantic import HttpUrl
from app.modules.versions.schemas import (
    Endpoint,
    InterfaceRole,
    ModuleID,
    Version,
    VersionDetails,
)


router = APIRouter(
    prefix="/ocpi",
    tags=["Versions"],
)


# -----------------------------
# CPO
# -----------------------------

@router.get("/cpo/versions", response_model=list[Version])
def get_cpo_versions():
    return [
        Version(
            version="2.2.1",
            url=HttpUrl("http://localhost:8000/ocpi/cpo/2.2.1"),
        )
    ]


@router.get("/cpo/2.2.1", response_model=VersionDetails)
def get_cpo_version_details():
    return VersionDetails(
        version="2.2.1",
        endpoints=[
            Endpoint(
                identifier=ModuleID.CREDENTIALS,
                role=InterfaceRole.RECEIVER,
                url=HttpUrl("http://localhost:8000/ocpi/cpo/2.2.1/credentials"),
            )
        ],
    )


# -----------------------------
# eMSP
# -----------------------------

@router.get("/emsp/versions", response_model=list[Version])
def get_emsp_versions():
    return [
        Version(
            version="2.2.1",
            url=HttpUrl("http://localhost:8000/ocpi/emsp/2.2.1"),
        )
    ]


@router.get("/emsp/2.2.1", response_model=VersionDetails)
def get_emsp_version_details():
    return VersionDetails(
        version="2.2.1",
        endpoints=[
            Endpoint(
                identifier=ModuleID.CREDENTIALS,
                role=InterfaceRole.RECEIVER,
                url=HttpUrl("http://localhost:8000/ocpi/emsp/2.2.1/credentials"),
            )
        ],
    )