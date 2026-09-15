from __future__ import annotations

import json
import os
from base64 import b64encode
from pathlib import Path
from uuid import uuid4

import httpx
from pydantic import HttpUrl

from app.modules.credentials.schemas import (
    BusinessDetails,
    Credentials,
    CredentialsRole,
    Role,
)


# =========================================================
# Numocity CPO configuration
# =========================================================

NUMOCITY_VERSIONS_URL = (
    "https://testhub.numocity.in/ocpi/cpo/versions"
)

EMSP_TOKEN_A: str = os.getenv("EMSP_TOKEN_A", "")

if not EMSP_TOKEN_A:
    raise RuntimeError(
        "EMSP_TOKEN_A environment variable is not set."
    )


# Public URL through which Numocity can reach our eMSP.
EMSP_PUBLIC_VERSIONS_URL = (
    "https://growing-lagged-skittle.ngrok-free.dev"
    "/ocpi/emsp/versions"
)

EMSP_WEBSITE_URL = "http://localhost:8000"


# =========================================================
# Local credential storage
# =========================================================

DATA_DIR = Path("data")
CPO_CREDENTIALS_FILE = DATA_DIR / "numocity_cpo_credentials.json"


# =========================================================
# Runtime handshake state
# =========================================================

remote_cpo_credentials: Credentials | None = None
handshake_completed = False


# =========================================================
# OCPI Authorization
# =========================================================

def build_ocpi_authorization(token: str) -> str:
    """
    Build the OCPI Authorization header.

    Format:
        Authorization: Token <Base64-encoded-token>
    """

    encoded_token = b64encode(
        token.encode("utf-8")
    ).decode("ascii")

    return f"Token {encoded_token}"


# =========================================================
# Request Headers
# =========================================================

def build_headers(
    token: str,
    include_content_type: bool = False,
) -> dict[str, str]:
    """
    Build common OCPI request headers.
    """

    headers = {
        "Authorization": build_ocpi_authorization(token),
        "X-Request-ID": str(uuid4()),
        "X-Correlation-ID": str(uuid4()),
        "Accept": "application/json",
    }

    if include_content_type:
        headers["Content-Type"] = "application/json"

    return headers


# =========================================================
# Build eMSP Credentials
# =========================================================

def build_emsp_credentials() -> Credentials:
    """
    Create the eMSP credentials sent to Numocity
    during the first-time handshake.
    """

    return Credentials(
        token=EMSP_TOKEN_A,
        url=HttpUrl(EMSP_PUBLIC_VERSIONS_URL),
        roles=[
            CredentialsRole(
                role=Role.EMSP,
                business_details=BusinessDetails(
                    name="TejasSP",
                    website=HttpUrl(EMSP_WEBSITE_URL),
                ),
                party_id="TSP",
                country_code="IN",
            )
        ],
    )


# =========================================================
# Save CPO credentials
# =========================================================

def save_cpo_credentials(
    credentials: Credentials,
) -> None:
    """
    Persist Numocity CPO credentials locally.

    The credentials file must not be committed to Git.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CPO_CREDENTIALS_FILE.write_text(
        credentials.model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )
def import_cpo_credentials(
    credentials: Credentials,
) -> Credentials:
    """
    Import CPO credentials that were already issued
    by the remote CPO and persist them locally.

    This is a simulator-management operation and is not
    part of the standard OCPI protocol.
    """

    global remote_cpo_credentials
    global handshake_completed

    # Validate the credentials before storing them.
    validated_credentials = Credentials.model_validate(
        credentials.model_dump(mode="json")
    )

    # Store in memory.
    remote_cpo_credentials = validated_credentials

    # Persist securely in the ignored data/ directory.
    save_cpo_credentials(
        validated_credentials
    )

    # Mark the connection as established.
    handshake_completed = True

    return validated_credentials

# =========================================================
# Load CPO credentials
# =========================================================

def load_cpo_credentials() -> Credentials | None:
    """
    Load previously stored Numocity CPO credentials.
    """

    if not CPO_CREDENTIALS_FILE.exists():
        return None

    try:
        data = json.loads(
            CPO_CREDENTIALS_FILE.read_text(
                encoding="utf-8"
            )
        )

        return Credentials.model_validate(data)

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ):
        return None
def get_connection_status() -> dict[str, object]:
    """
    Return the current eMSP-to-CPO connection status.
    """

    credentials = get_stored_cpo_credentials()

    if credentials is None:
        return {
            "connected": False,
            "role": "EMSP",
            "ocpi_version": "2.2.1",
            "cpo_name": None,
            "cpo_party_id": None,
            "cpo_country_code": None,
        }

    cpo_role = credentials.roles[0] if credentials.roles else None

    return {
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

# =========================================================
# Get existing connection
# =========================================================

def get_stored_cpo_credentials() -> Credentials | None:
    """
    Return stored CPO credentials if available.
    """

    global remote_cpo_credentials
    global handshake_completed

    if remote_cpo_credentials is not None:
        return remote_cpo_credentials

    stored_credentials = load_cpo_credentials()

    if stored_credentials is not None:
        remote_cpo_credentials = stored_credentials
        handshake_completed = True

    return stored_credentials


# =========================================================
# Perform OCPI Credentials Handshake
# =========================================================

async def perform_emsp_handshake() -> Credentials:
    """
    Perform the first-time OCPI Credentials handshake.

    Flow:

        1. Check for an existing stored connection.
        2. GET CPO /versions.
        3. Select OCPI 2.2.1.
        4. GET CPO version details.
        5. Find Credentials RECEIVER endpoint.
        6. POST our eMSP credentials.
        7. Store Numocity CPO credentials.
    """

    global remote_cpo_credentials
    global handshake_completed

    # -----------------------------------------------------
    # Step 0: Reuse existing connection
    # -----------------------------------------------------

    stored_credentials = get_stored_cpo_credentials()

    if stored_credentials is not None:
        return stored_credentials

    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:

        # -------------------------------------------------
        # Step 1: Get supported CPO versions
        # -------------------------------------------------

        versions_response = await client.get(
            NUMOCITY_VERSIONS_URL,
            headers=build_headers(
                EMSP_TOKEN_A
            ),
        )

        versions_response.raise_for_status()

        versions_data = (
            versions_response.json()
        )

        if versions_data.get("status_code") != 1000:
            raise RuntimeError(
                f"Numocity /versions failed: "
                f"{versions_data}"
            )

        versions = (
            versions_data.get("data")
            or []
        )

        # -------------------------------------------------
        # Step 2: Select OCPI 2.2.1
        # -------------------------------------------------

        selected_version = next(
            (
                item
                for item in versions
                if item.get("version")
                == "2.2.1"
            ),
            None,
        )

        if not selected_version:
            raise RuntimeError(
                "Numocity does not advertise "
                "OCPI 2.2.1."
            )

        version_url = (
            selected_version.get("url")
        )

        if not version_url:
            raise RuntimeError(
                "Numocity returned no URL "
                "for OCPI 2.2.1."
            )

        # -------------------------------------------------
        # Step 3: Get CPO version details
        # -------------------------------------------------

        endpoints_response = await client.get(
            str(version_url),
            headers=build_headers(
                EMSP_TOKEN_A
            ),
        )

        endpoints_response.raise_for_status()

        endpoints_data = (
            endpoints_response.json()
        )

        if endpoints_data.get(
            "status_code"
        ) != 1000:
            raise RuntimeError(
                "Numocity version details "
                f"request failed: "
                f"{endpoints_data}"
            )

        version_details = (
            endpoints_data.get("data")
            or {}
        )

        endpoints = (
            version_details.get("endpoints")
            or []
        )

        # -------------------------------------------------
        # Step 4: Find Credentials RECEIVER
        # -------------------------------------------------

        credentials_endpoint = next(
            (
                endpoint
                for endpoint in endpoints
                if endpoint.get("identifier")
                == "credentials"
                and endpoint.get("role")
                == "RECEIVER"
            ),
            None,
        )

        if not credentials_endpoint:
            raise RuntimeError(
                "Numocity CPO does not expose "
                "a Credentials RECEIVER endpoint."
            )

        credentials_url = (
            credentials_endpoint.get("url")
        )

        if not credentials_url:
            raise RuntimeError(
                "Numocity Credentials endpoint "
                "has no URL."
            )

        # -------------------------------------------------
        # Step 5: Build eMSP credentials
        # -------------------------------------------------

        emsp_credentials = (
            build_emsp_credentials()
        )

        # -------------------------------------------------
        # Step 6: First-time POST
        # -------------------------------------------------

        credentials_response = await client.post(
            str(credentials_url),
            headers=build_headers(
                EMSP_TOKEN_A,
                include_content_type=True,
            ),
            json=emsp_credentials.model_dump(
                mode="json"
            ),
        )

        # -------------------------------------------------
        # POST must succeed during first registration.
        #
        # We do NOT retry POST or GET credentials with
        # Token A after an already-used bootstrap token.
        # -------------------------------------------------

        if credentials_response.status_code >= 400:
            raise RuntimeError(
                "Numocity Credentials handshake failed. "
                f"HTTP "
                f"{credentials_response.status_code}: "
                f"{credentials_response.text}"
            )

        credentials_data = (
            credentials_response.json()
        )

        if credentials_data.get(
            "status_code"
        ) != 1000:
            raise RuntimeError(
                "Numocity Credentials handshake failed: "
                f"{credentials_data}"
            )

        returned_credentials = (
            credentials_data.get("data")
        )

        if not returned_credentials:
            raise RuntimeError(
                "Numocity returned no CPO credentials."
            )

        # -------------------------------------------------
        # Step 7: Validate returned credentials
        # -------------------------------------------------

        remote_cpo_credentials = (
            Credentials.model_validate(
                returned_credentials
            )
        )

        # -------------------------------------------------
        # Step 8: Persist returned credentials
        # -------------------------------------------------

        save_cpo_credentials(
            remote_cpo_credentials
        )

        handshake_completed = True

        return remote_cpo_credentials