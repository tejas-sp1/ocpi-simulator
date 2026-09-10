from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class Role(str, Enum):
    CPO = "CPO"
    EMSP = "EMSP"
    HUB = "HUB"
    NAP = "NAP"
    NSP = "NSP"
    OTHER = "OTHER"
    SCSP = "SCSP"


class BusinessDetails(BaseModel):
    name: str = Field(max_length=100)
    website: HttpUrl | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Test eMSP",
                "website": "http://localhost:8000",
            }
        }
    }


class CredentialsRole(BaseModel):
    role: Role
    business_details: BusinessDetails
    party_id: str = Field(min_length=3, max_length=3)
    country_code: str = Field(min_length=2, max_length=2)

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "EMSP",
                "business_details": {
                    "name": "Test eMSP",
                    "website": "http://localhost:8000",
                },
                "party_id": "TST",
                "country_code": "IN",
            }
        }
    }


class Credentials(BaseModel):
    token: str = Field(min_length=1, max_length=64)
    url: HttpUrl
    roles: list[CredentialsRole] = Field(min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "test-client-token-12345",
                "url": "http://localhost:8000/ocpi/emsp/versions",
                "roles": [
                    {
                        "role": "EMSP",
                        "business_details": {
                            "name": "Test eMSP",
                            "website": "http://localhost:8000",
                        },
                        "party_id": "TST",
                        "country_code": "IN",
                    }
                ],
            }
        }
    }