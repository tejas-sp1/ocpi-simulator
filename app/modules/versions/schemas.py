from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class InterfaceRole(str, Enum):
    SENDER = "SENDER"
    RECEIVER = "RECEIVER"


class ModuleID(str, Enum):
    CDRS = "cdrs"
    CHARGINGPROFILES = "chargingprofiles"
    COMMANDS = "commands"
    CREDENTIALS = "credentials"
    HUBCLIENTINFO = "hubclientinfo"
    LOCATIONS = "locations"
    SESSIONS = "sessions"
    TARIFFS = "tariffs"
    TOKENS = "tokens"


class Version(BaseModel):
    version: str
    url: HttpUrl

    model_config = {
        "json_schema_extra": {
            "example": {
                "version": "2.2.1",
                "url": "http://localhost:8000/ocpi/cpo/2.2.1",
            }
        }
    }


class Endpoint(BaseModel):
    identifier: ModuleID
    role: InterfaceRole
    url: HttpUrl

    model_config = {
        "json_schema_extra": {
            "example": {
                "identifier": "credentials",
                "role": "SENDER",
                "url": (
                    "http://localhost:8000/ocpi/cpo/"
                    "2.2.1/credentials"
                ),
            }
        }
    }


class VersionDetails(BaseModel):
    version: str
    endpoints: list[Endpoint] = Field(min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "version": "2.2.1",
                "endpoints": [
                    {
                        "identifier": "credentials",
                        "role": "SENDER",
                        "url": (
                            "http://localhost:8000/ocpi/cpo/"
                            "2.2.1/credentials"
                        ),
                    }
                ],
            }
        }
    }