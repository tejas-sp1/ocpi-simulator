from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import HttpUrl

from app.core.response import OCPIResponse, create_ocpi_response
from app.modules.credentials.schemas import (
    BusinessDetails,
    Credentials,
    CredentialsRole,
    Role,
)


router = APIRouter(
    prefix="/ocpi",
    tags=["Credentials"],
)


# =========================================================
# Registration state
# =========================================================
#
# These store the credentials received from the connected
# remote OCPI party.
#
# None = no party is currently registered.
#
registered_cpo_client: Credentials | None = None
registered_emsp_client: Credentials | None = None


# =========================================================
# Server credentials
# =========================================================
#
# These are the credentials of THIS simulator that are
# returned to the remote party during GET/POST/PUT.
#

CPO_SERVER_CREDENTIALS = Credentials(
    token=uuid4().hex,
    url=HttpUrl(
        "http://localhost:8000/ocpi/cpo/versions"
    ),
    roles=[
        CredentialsRole(
            role=Role.CPO,
            business_details=BusinessDetails(
                name="OCPI Simulator CPO",
                website=HttpUrl(
                    "http://localhost:8000"
                ),
            ),
            party_id="SIM",
            country_code="IN",
        )
    ],
)


EMSP_SERVER_CREDENTIALS = Credentials(
    token=uuid4().hex,
    url=HttpUrl(
        "http://localhost:8000/ocpi/emsp/versions"
    ),
    roles=[
        CredentialsRole(
            role=Role.EMSP,
            business_details=BusinessDetails(
                name="OCPI Simulator eMSP",
                website=HttpUrl(
                    "http://localhost:8000"
                ),
            ),
            party_id="SIM",
            country_code="IN",
        )
    ],
)


# =========================================================
# CPO Credentials
# =========================================================


@router.get(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse,
)
def get_cpo_credentials(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Return the CPO simulator's credentials.
    """

    return create_ocpi_response(
        data=CPO_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse,
)
def register_cpo_credentials(
    credentials: Credentials,
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Register credentials received from a remote OCPI party.
    """

    global registered_cpo_client

    if registered_cpo_client is not None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has already been registered. "
                "Use PUT to update credentials."
            ),
        )

    registered_cpo_client = credentials

    return create_ocpi_response(
        data=CPO_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.put(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse,
)
def update_cpo_credentials(
    credentials: Credentials,
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Update the credentials of an already registered party.
    """

    global registered_cpo_client

    if registered_cpo_client is None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has not been registered yet. "
                "Use POST first."
            ),
        )

    registered_cpo_client = credentials

    return create_ocpi_response(
        data=CPO_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.delete(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse,
)
def delete_cpo_credentials(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Remove the registered remote party.
    """

    global registered_cpo_client

    if registered_cpo_client is None:
        raise HTTPException(
            status_code=405,
            detail="No client is currently registered.",
        )

    registered_cpo_client = None

    return create_ocpi_response(
        data=None,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# =========================================================
# eMSP Credentials
# =========================================================


@router.get(
    "/emsp/2.2.1/credentials",
    response_model=OCPIResponse,
)
def get_emsp_credentials(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Return the eMSP simulator's credentials.
    """

    return create_ocpi_response(
        data=EMSP_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/emsp/2.2.1/credentials",
    response_model=OCPIResponse,
)
def register_emsp_credentials(
    credentials: Credentials,
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Register credentials received from a remote OCPI party.
    """

    global registered_emsp_client

    if registered_emsp_client is not None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has already been registered. "
                "Use PUT to update credentials."
            ),
        )

    registered_emsp_client = credentials

    return create_ocpi_response(
        data=EMSP_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.put(
    "/emsp/2.2.1/credentials",
    response_model=OCPIResponse,
)
def update_emsp_credentials(
    credentials: Credentials,
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Update the credentials of an already registered party.
    """

    global registered_emsp_client

    if registered_emsp_client is None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has not been registered yet. "
                "Use POST first."
            ),
        )

    registered_emsp_client = credentials

    return create_ocpi_response(
        data=EMSP_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.delete(
    "/emsp/2.2.1/credentials",
    response_model=OCPIResponse,
)
def delete_emsp_credentials(
    response: Response,
    x_request_id: str = Header(..., alias="X-Request-ID"),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Remove the registered remote party.
    """

    global registered_emsp_client

    if registered_emsp_client is None:
        raise HTTPException(
            status_code=405,
            detail="No client is currently registered.",
        )

    registered_emsp_client = None

    return create_ocpi_response(
        data=None,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )