"""Credential-reference based local agent authentication."""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from typing import Any

from testflight_workflows import WorkflowPrincipal


@dataclass(frozen=True, slots=True)
class PrincipalDeclaration:
    id: str
    roles: tuple[str, ...]
    token_env: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> PrincipalDeclaration:
        return cls(
            id=str(value["id"]),
            roles=tuple(str(role) for role in value.get("roles", [])),
            token_env=str(value["token_env"]),
        )


class EnvironmentTokenAuthenticator:
    def __init__(self, credentials: tuple[tuple[str, WorkflowPrincipal], ...]) -> None:
        if not credentials:
            raise ValueError("at least one workflow principal credential is required")
        self._credentials = credentials

    @classmethod
    def from_declarations(
        cls, declarations: tuple[PrincipalDeclaration, ...]
    ) -> EnvironmentTokenAuthenticator:
        credentials: list[tuple[str, WorkflowPrincipal]] = []
        for declaration in declarations:
            token = os.environ.get(declaration.token_env)
            if not token:
                raise ValueError(f"credential environment is missing: {declaration.token_env}")
            credentials.append(
                (token, WorkflowPrincipal(id=declaration.id, roles=declaration.roles))
            )
        return cls(tuple(credentials))

    def authenticate(self, authorization: str | None) -> WorkflowPrincipal | None:
        if not authorization or not authorization.startswith("Bearer "):
            return None
        candidate = authorization.removeprefix("Bearer ")
        matched: WorkflowPrincipal | None = None
        for token, principal in self._credentials:
            if hmac.compare_digest(candidate, token):
                matched = principal
        return matched


__all__ = ["EnvironmentTokenAuthenticator", "PrincipalDeclaration"]
