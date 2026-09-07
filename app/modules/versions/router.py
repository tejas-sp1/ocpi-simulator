from fastapi import APIRouter, Header, Response
from pydantic import HttpUrl

from app.core.response import OCPIResponse, create_ocpi_response

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


# ---------------------------------------------------------
# CPO - Versions
# ---------------------------------------------------------
@router.get("/cpo/versions", response_model=OCPIResponse)
def get_cpo_versions(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(..., alias="X-Correlation-ID"),
):
    versions = [
        Version(
            version="2.2.1",
            url=HttpUrl(
                "http://localhost:8000/ocpi/cpo/2.2.1"
            ),
        )
    ]

    return create_ocpi_response(
        data=versions,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# ---------------------------------------------------------
# CPO - Version Details
# ---------------------------------------------------------
@router.get("/cpo/2.2.1", response_model=OCPIResponse)
def get_cpo_version_details(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(..., alias="X-Correlation-ID"),
):
    version_details = VersionDetails(
        version="2.2.1",
        endpoints=[
            Endpoint(
                identifier=ModuleID.CREDENTIALS,
                role=InterfaceRole.SENDER,
                url=HttpUrl(
                    "http://localhost:8000/ocpi/cpo/2.2.1/credentials"
                ),
            )
        ],
    )

    return create_ocpi_response(
        data=version_details,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# ---------------------------------------------------------
# eMSP - Versions
# ---------------------------------------------------------
@router.get("/emsp/versions", response_model=OCPIResponse)
def get_emsp_versions(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(..., alias="X-Correlation-ID"),
):
    versions = [
        Version(
            version="2.2.1",
            url=HttpUrl(
                "http://localhost:8000/ocpi/emsp/2.2.1"
            ),
        )
    ]

    return create_ocpi_response(
        data=versions,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# ---------------------------------------------------------
# eMSP - Version Details
# ---------------------------------------------------------
@router.get("/emsp/2.2.1", response_model=OCPIResponse)
def get_emsp_version_details(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(..., alias="X-Correlation-ID"),
):
    version_details = VersionDetails(
        version="2.2.1",
        endpoints=[
            Endpoint(
                identifier=ModuleID.CREDENTIALS,
                role=InterfaceRole.SENDER,
                url=HttpUrl(
                    "http://localhost:8000/ocpi/emsp/2.2.1/credentials"
                ),
            )
        ],
    )

    return create_ocpi_response(
        data=version_details,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )