"""Data models for stored server profiles."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum


class AuthType(str, Enum):
    """How a phpMyAdmin server expects credentials."""

    AUTO = "auto"          # Detect at runtime (cookie form, then HTTP basic).
    COOKIE = "cookie"      # phpMyAdmin cookie login form.
    HTTP_BASIC = "basic"   # HTTP Basic Authentication popup.


class Environment(str, Enum):
    """Environment level used for tab tinting / safety indicators."""

    NONE = "none"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass
class ServerProfile:
    """A saved phpMyAdmin server connection."""

    label: str
    url: str
    username: str
    password: str
    auth_type: AuthType = AuthType.AUTO
    group: str = ""
    environment: Environment = Environment.NONE
    startup_script: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["auth_type"] = self.auth_type.value
        data["environment"] = self.environment.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ServerProfile":
        return cls(
            id=data.get("id", uuid.uuid4().hex),
            label=data["label"],
            url=data["url"],
            username=data["username"],
            password=data["password"],
            auth_type=AuthType(data.get("auth_type", AuthType.AUTO.value)),
            group=data.get("group", ""),
            environment=Environment(data.get("environment", Environment.NONE.value)),
            startup_script=data.get("startup_script", ""),
        )
