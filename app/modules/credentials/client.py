from __future__ import annotations

import os
from base64 import b64encode
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

# Token A is provided through the environment.
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

# Business website for the simulator.
EMSP_WEBSITE_URL = "http://localhost:8000"


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
    Create the Credentials object that our eMSP sends
    to the Numocity CPO during the handshake.
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
# Perform OCPI Credentials Handshake
# =========================================================

async def perform_emsp_handshake() -> Credentials:
    """
    Perform the complete OCPI Credentials handshake
    between our eMSP simulator and the Numocity CPO.

    Flow:

        1. GET CPO /versions
        2. Select OCPI 2.2.1
        3. GET CPO 2.2.1 endpoints
        4. Find Credentials RECEIVER endpoint
        5. POST our eMSP credentials
        6. Store returned CPO credentials
    """

    global remote_cpo_credentials
    global handshake_completed

    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:

        # -------------------------------------------------
        # Step 1: GET CPO versions
        # -------------------------------------------------

        versions_response = await client.get(
            NUMOCITY_VERSIONS_URL,
            headers=build_headers(EMSP_TOKEN_A),
        )

        versions_response.raise_for_status()

        versions_data = versions_response.json()

        if versions_data.get("status_code") != 1000:
            raise RuntimeError(
                f"Numocity /versions failed: "
                f"{versions_data}"
            )

        versions = versions_data.get("data") or []

        # -------------------------------------------------
        # Step 2: Select OCPI 2.2.1
        # -------------------------------------------------

        selected_version = next(
            (
                item
                for item in versions
                if item.get("version") == "2.2.1"
            ),
            None,
        )

        if not selected_version:
            raise RuntimeError(
                "Numocity does not advertise OCPI 2.2.1."
            )

        version_url = selected_version.get("url")

        if not version_url:
            raise RuntimeError(
                "Numocity returned no URL for OCPI 2.2.1."
            )

        # -------------------------------------------------
        # Step 3: GET CPO version details
        # -------------------------------------------------

        endpoints_response = await client.get(
            str(version_url),
            headers=build_headers(EMSP_TOKEN_A),
        )

        endpoints_response.raise_for_status()

        endpoints_data = endpoints_response.json()

        if endpoints_data.get("status_code") != 1000:
            raise RuntimeError(
                "Numocity version details request failed: "
                f"{endpoints_data}"
            )

        version_details = endpoints_data.get(
            "data"
        ) or {}

        endpoints = version_details.get(
            "endpoints"
        ) or []

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
                "Numocity CPO does not expose a "
                "Credentials RECEIVER endpoint."
            )

        credentials_url = credentials_endpoint.get(
            "url"
        )

        if not credentials_url:
            raise RuntimeError(
                "Numocity Credentials endpoint has no URL."
            )

        # -------------------------------------------------
        # Step 5: Build our eMSP credentials
        # -------------------------------------------------

        emsp_credentials = build_emsp_credentials()

        # -------------------------------------------------
        # Step 6: POST our credentials to Numocity
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
        # If already registered, retrieve existing
        # server credentials using GET.
        # -------------------------------------------------

        if credentials_response.status_code == 405:
            existing_credentials_response = await client.get(
                str(credentials_url),
                headers=build_headers(EMSP_TOKEN_A),
            )

            if existing_credentials_response.status_code != 200:
                raise RuntimeError(
                    "eMSP is already registered with Numocity, "
                    "but existing credentials could not be retrieved. "
                    f"HTTP "
                    f"{existing_credentials_response.status_code}: "
                    f"{existing_credentials_response.text}"
                )

            credentials_data = existing_credentials_response.json()

        else:
            # -------------------------------------------------
            # Normal first-time registration
            # -------------------------------------------------

            if credentials_response.status_code >= 400:
                raise RuntimeError(
                    "Numocity Credentials request failed. "
                    f"HTTP "
                    f"{credentials_response.status_code}: "
                    f"{credentials_response.text}"
                )

            credentials_data = credentials_response.json()

        # -------------------------------------------------
        # Validate OCPI response
        # -------------------------------------------------

        if credentials_data.get("status_code") != 1000:
            raise RuntimeError(
                "Numocity Credentials handshake failed: "
                f"{credentials_data}"
            )

        returned_credentials = credentials_data.get("data")

        if not returned_credentials:
            raise RuntimeError(
                "Numocity returned no credentials."
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
        # Step 8: Mark handshake as completed
        # -------------------------------------------------

        handshake_completed = True

        return remote_cpo_credentials