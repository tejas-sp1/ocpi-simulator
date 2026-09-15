from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from secrets import token_hex
import os

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import HttpUrl

from app.core.response import OCPIResponse, create_ocpi_response
from app.modules.credentials.client import perform_emsp_handshake
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
# Bootstrap tokens
# =========================================================
#
# These are the initial tokens used before the first
# successful registration.
#

CPO_BOOTSTRAP_TOKEN = "CPO-SIMULATOR-TOKEN-A"
EMSP_BOOTSTRAP_TOKEN: str = os.getenv("EMSP_TOKEN_A", "")

if not EMSP_BOOTSTRAP_TOKEN:
    raise RuntimeError(
        "EMSP_TOKEN_A environment variable is not set."
    )


# =========================================================
# Registration state
# =========================================================
#
# These variables store credentials received from the
# remote OCPI party.
#

registered_cpo_client: Credentials | None = None
registered_emsp_client: Credentials | None = None


# =========================================================
# Current authorization tokens
# =========================================================
#
# These are the tokens currently accepted in the
# Authorization header.
#

current_cpo_auth_token = CPO_BOOTSTRAP_TOKEN
current_emsp_auth_token = EMSP_BOOTSTRAP_TOKEN


# =========================================================
# Token generation
# =========================================================

def generate_credentials_token() -> str:
    """
    Generate a 64-character hexadecimal token.

    token_hex(32) = 64 hexadecimal characters.
    """
    return token_hex(32)


# =========================================================
# Token rotation
# =========================================================

def rotate_cpo_token() -> str:
    """
    Generate and activate a new CPO authorization token.
    """

    global current_cpo_auth_token

    new_token = generate_credentials_token()

    current_cpo_auth_token = new_token
    CPO_SERVER_CREDENTIALS.token = new_token

    return new_token


def rotate_emsp_token() -> str:
    """
    Generate and activate a new eMSP authorization token.
    """

    global current_emsp_auth_token

    new_token = generate_credentials_token()

    current_emsp_auth_token = new_token
    EMSP_SERVER_CREDENTIALS.token = new_token

    return new_token


# =========================================================
# Authorization encoding helper
# =========================================================

def encode_ocpi_authorization(token: str) -> str:
    """
    Create an OCPI Authorization header value.

    Example:
        Token <Base64-encoded-token>
    """

    encoded_token = b64encode(
        token.encode("utf-8")
    ).decode("ascii")

    return f"Token {encoded_token}"


# =========================================================
# Authorization validation
# =========================================================

def validate_ocpi_authorization(
    authorization: str,
    expected_token: str,
) -> None:
    """
    Validate an OCPI Authorization header.

    Expected format:

        Authorization: Token <Base64-token>
    """

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header.",
        )

    parts = authorization.split(" ", 1)

    if len(parts) != 2:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format.",
        )

    scheme = parts[0]
    encoded_token = parts[1]

    if scheme != "Token":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization scheme.",
        )

    try:
        decoded_token = b64decode(
            encoded_token,
            validate=True,
        ).decode("utf-8")

    except (BinasciiError, UnicodeDecodeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid Base64 credentials token.",
        )

    if decoded_token != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials token.",
        )


# =========================================================
# Server credentials
# =========================================================

CPO_SERVER_CREDENTIALS = Credentials(
    token=CPO_BOOTSTRAP_TOKEN,
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
    token=EMSP_BOOTSTRAP_TOKEN,
    url=HttpUrl(
        "https://growing-lagged-skittle.ngrok-free.dev/ocpi/emsp/versions"
    ),
    roles=[
        CredentialsRole(
            role=Role.EMSP,
            business_details=BusinessDetails(
                name="TejasSP",
                website=HttpUrl(
                    "http://localhost:8000"
                ),
            ),
            party_id="TSP",
            country_code="IN",
        )
    ],
)


# =========================================================
# CPO Credentials
# =========================================================


@router.get(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse[Credentials],
)
def get_cpo_credentials(
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Return this simulator's CPO credentials.
    """

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_cpo_auth_token,
    )

    return create_ocpi_response(
        data=CPO_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse[Credentials],
)
def register_cpo_credentials(
    credentials: Credentials,
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Register credentials received from a remote OCPI party.
    """

    global registered_cpo_client

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_cpo_auth_token,
    )

    if registered_cpo_client is not None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has already been registered. "
                "Use PUT to update credentials."
            ),
        )

    # Store remote party credentials.
    registered_cpo_client = credentials

    # Rotate the server's authorization token.
    rotate_cpo_token()

    # Return the simulator's NEW credentials.
    return create_ocpi_response(
        data=CPO_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.put(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse[Credentials],
)
def update_cpo_credentials(
    credentials: Credentials,
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Update credentials of an already registered remote party.
    """

    global registered_cpo_client

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_cpo_auth_token,
    )

    if registered_cpo_client is None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has not been registered yet. "
                "Use POST first."
            ),
        )

    # Replace stored remote credentials.
    registered_cpo_client = credentials

    # Rotate token again.
    rotate_cpo_token()

    # Return the simulator's NEW credentials.
    return create_ocpi_response(
        data=CPO_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.delete(
    "/cpo/2.2.1/credentials",
    response_model=OCPIResponse[None],
)
def delete_cpo_credentials(
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Remove the registered remote CPO party.
    """

    global registered_cpo_client
    global current_cpo_auth_token

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_cpo_auth_token,
    )

    if registered_cpo_client is None:
        raise HTTPException(
            status_code=405,
            detail="No client is currently registered.",
        )

    registered_cpo_client = None

    # Reset the simulator for another test registration.
    current_cpo_auth_token = CPO_BOOTSTRAP_TOKEN
    CPO_SERVER_CREDENTIALS.token = CPO_BOOTSTRAP_TOKEN

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
    response_model=OCPIResponse[Credentials],
)
def get_emsp_credentials(
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Return this simulator's eMSP credentials.
    """

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_emsp_auth_token,
    )

    return create_ocpi_response(
        data=EMSP_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/emsp/2.2.1/credentials",
    response_model=OCPIResponse[Credentials],
)
def register_emsp_credentials(
    credentials: Credentials,
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Register credentials received from a remote OCPI party.
    """

    global registered_emsp_client

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_emsp_auth_token,
    )

    if registered_emsp_client is not None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has already been registered. "
                "Use PUT to update credentials."
            ),
        )

    # Store remote party credentials.
    registered_emsp_client = credentials

    # Rotate the server's authorization token.
    rotate_emsp_token()

    # Return the simulator's NEW credentials.
    return create_ocpi_response(
        data=EMSP_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.put(
    "/emsp/2.2.1/credentials",
    response_model=OCPIResponse[Credentials],
)
def update_emsp_credentials(
    credentials: Credentials,
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Update credentials of an already registered remote party.
    """

    global registered_emsp_client

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_emsp_auth_token,
    )

    if registered_emsp_client is None:
        raise HTTPException(
            status_code=405,
            detail=(
                "Client has not been registered yet. "
                "Use POST first."
            ),
        )

    # Replace stored remote credentials.
    registered_emsp_client = credentials

    # Rotate token again.
    rotate_emsp_token()

    # Return the simulator's NEW credentials.
    return create_ocpi_response(
        data=EMSP_SERVER_CREDENTIALS,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


@router.delete(
    "/emsp/2.2.1/credentials",
    response_model=OCPIResponse[None],
)
def delete_emsp_credentials(
    response: Response,
    authorization: str = Header(
        ...,
        alias="Authorization",
    ),
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Remove the registered remote eMSP party.
    """

    global registered_emsp_client
    global current_emsp_auth_token

    validate_ocpi_authorization(
        authorization=authorization,
        expected_token=current_emsp_auth_token,
    )

    if registered_emsp_client is None:
        raise HTTPException(
            status_code=405,
            detail="No client is currently registered.",
        )

    registered_emsp_client = None

    # Reset the simulator for another test registration.
    current_emsp_auth_token = EMSP_BOOTSTRAP_TOKEN
    EMSP_SERVER_CREDENTIALS.token = EMSP_BOOTSTRAP_TOKEN

    return create_ocpi_response(
        data=None,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )
# =========================================================
# eMSP - Perform CPO Credentials Handshake
# =========================================================

@router.post(
    "/emsp/handshake",
    response_model=OCPIResponse[Credentials],
)
async def emsp_handshake(
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Start the OCPI Credentials handshake with the
    configured Numocity CPO.
    """

    try:
        cpo_credentials = await perform_emsp_handshake()

        return create_ocpi_response(
            data=cpo_credentials,
            response=response,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

    except Exception as exc:
        raise HTTPException(
        status_code=502,
        detail=f"OCPI handshake failed: {repr(exc)}",
    )