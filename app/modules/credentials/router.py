from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from secrets import token_hex
import os

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import HttpUrl

from app.core.response import OCPIResponse, create_ocpi_response
from app.modules.credentials.client import (
    get_connection_status,
    get_stored_cpo_credentials,
    import_cpo_credentials,
    perform_emsp_handshake,
)
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
# Bootstrap Tokens
# =========================================================

# Initial CPO simulator token.
# This is only for the simulator's own CPO role.
CPO_BOOTSTRAP_TOKEN = "CPO-SIMULATOR-TOKEN-A"

# Initial eMSP bootstrap token is loaded from the environment.
EMSP_BOOTSTRAP_TOKEN: str = os.getenv(
    "EMSP_TOKEN_A",
    "",
)

if not EMSP_BOOTSTRAP_TOKEN:
    raise RuntimeError(
        "EMSP_TOKEN_A environment variable is not set."
    )


# =========================================================
# Registration State
# =========================================================

# These variables store credentials received from
# remote OCPI parties.

registered_cpo_client: Credentials | None = None
registered_emsp_client: Credentials | None = None


# =========================================================
# Current Authorization Tokens
# =========================================================

# These are the tokens currently accepted in the
# Authorization header.

current_cpo_auth_token = CPO_BOOTSTRAP_TOKEN
current_emsp_auth_token = EMSP_BOOTSTRAP_TOKEN


# =========================================================
# Token Generation
# =========================================================

def generate_credentials_token() -> str:
    """
    Generate a 64-character hexadecimal credentials token.

    token_hex(32) produces 64 hexadecimal characters.
    """

    return token_hex(32)


# =========================================================
# Token Rotation - CPO
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


# =========================================================
# Token Rotation - eMSP
# =========================================================

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
# Authorization Encoding Helper
# =========================================================

def encode_ocpi_authorization(token: str) -> str:
    """
    Create an OCPI Authorization header value.

    Format:
        Token <Base64-encoded-token>
    """

    encoded_token = b64encode(
        token.encode("utf-8")
    ).decode("ascii")

    return f"Token {encoded_token}"


# =========================================================
# Authorization Validation
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

    except (
        BinasciiError,
        UnicodeDecodeError,
    ):
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
# Server Credentials - CPO
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


# =========================================================
# Server Credentials - eMSP
# =========================================================

EMSP_SERVER_CREDENTIALS = Credentials(
    token=EMSP_BOOTSTRAP_TOKEN,
    url=HttpUrl(
        "https://growing-lagged-skittle.ngrok-free.dev"
        "/ocpi/emsp/versions"
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

    registered_cpo_client = credentials

    rotate_cpo_token()

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

    registered_cpo_client = credentials

    rotate_cpo_token()

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

    registered_emsp_client = credentials

    rotate_emsp_token()

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

    registered_emsp_client = credentials

    rotate_emsp_token()

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
    Start or reuse the OCPI Credentials connection.

    If Numocity CPO credentials are already stored locally,
    they are returned without attempting another bootstrap
    registration.

    Otherwise, a first-time handshake is performed.
    """

    try:

        # -------------------------------------------------
        # Step 1: Check for an existing connection
        # -------------------------------------------------

        stored_credentials = (
            get_stored_cpo_credentials()
        )

        if stored_credentials is not None:
            return create_ocpi_response(
                data=stored_credentials,
                response=response,
                request_id=x_request_id,
                correlation_id=x_correlation_id,
            )

        # -------------------------------------------------
        # Step 2: First-time handshake
        # -------------------------------------------------

        cpo_credentials = (
            await perform_emsp_handshake()
        )

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


# =========================================================
# eMSP - Connection Status
# =========================================================

@router.get(
    "/emsp/connection",
)
def emsp_connection_status():
    """
    Return the current eMSP-to-CPO connection status.

    Authentication tokens are intentionally not returned.
    """

    return get_connection_status()
# =========================================================
# Simulator - Import Existing CPO Credentials
# =========================================================

@router.post(
    "/simulator/emsp/credentials/import",
    response_model=dict[str, object],
)
def import_existing_cpo_credentials(
    credentials: Credentials,
):
    """
    Import CPO credentials that were already issued
    by the remote CPO.

    This endpoint is for simulator administration/testing
    and is not an OCPI protocol endpoint.

    The authentication token is intentionally not returned
    in the response.
    """

    try:
        imported_credentials = import_cpo_credentials(
            credentials
        )

        cpo_role = (
            imported_credentials.roles[0]
            if imported_credentials.roles
            else None
        )

        return {
            "success": True,
            "message": "CPO credentials imported successfully.",
            "connected": True,
            "role": "EMSP",
            "ocpi_version": "2.2.1",
            "cpo_name": (
                cpo_role.business_details.name
                if cpo_role
                else None
            ),
            "cpo_party_id": (
                cpo_role.party_id
                if cpo_role
                else None
            ),
            "cpo_country_code": (
                cpo_role.country_code
                if cpo_role
                else None
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to import CPO credentials: {repr(exc)}",
        )