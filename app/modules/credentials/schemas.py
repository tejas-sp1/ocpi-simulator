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


class CredentialsRole(BaseModel):
    role: Role
    business_details: BusinessDetails
    party_id: str = Field(min_length=3, max_length=3)
    country_code: str = Field(min_length=2, max_length=2)


class Credentials(BaseModel):
    token: str = Field(min_length=1, max_length=64)
    url: HttpUrl
    roles: list[CredentialsRole] = Field(min_length=1)