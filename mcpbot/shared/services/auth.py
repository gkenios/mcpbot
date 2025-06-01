from enum import StrEnum
import os
from typing import Callable

from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.exceptions import GoogleAuthError
from pydantic import BaseModel

from mcpbot.shared.config import COMPANY


class AuthProvider(StrEnum):
    local = "local"
    azure = "azure"
    gcp = "gcp"


class CommonTokenParams(BaseModel):
    sub: str
    hd: str
    email: str


def validate_local_token(token: str) -> CommonTokenParams:
    """Skip local authentication. Return user based on environment variable."""
    email = os.getenv("USER_EMAIL")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="'USER_EMAIL' not found in environment variables.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CommonTokenParams(
        sub="1",
        hd=f"{COMPANY.lower()}.com",
        email=email,
    )


def validate_azure_token(token: str) -> CommonTokenParams:
    raise NotImplementedError("Azure token validation is not implemented yet.")


def validate_gcp_token(token: str) -> CommonTokenParams:
    """
    Validate a Google authentication token and return the user information.

    :param token: The Google authentication token to validate.
    :return: User information if the token is valid.
    :raises HTTPException: If the token is invalid or does not match the
        expected domain.
    """
    try:
        request = requests.Request()  # type: ignore[no-untyped-call]
        payload = id_token.verify_oauth2_token(token, request, audience=None)  # type: ignore[no-untyped-call]
    except GoogleAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Validating google oauth2 token failed.",
        ) from error

    if payload.get("hd") != f"{COMPANY.lower()}.com":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: Domain mismatch.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not payload.get("email"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: User email not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CommonTokenParams(**payload)


def get_auth_method(
    provider: AuthProvider,
) -> Callable[[str], CommonTokenParams]:
    """
    Get the authentication provider based on the specified provider type.

    :param provider: The authentication provider type (e.g., Google, Azure).
    :return: An instance of the corresponding authentication provider.
    """
    if provider == AuthProvider.local:
        return validate_local_token
    elif provider == AuthProvider.azure:
        return validate_azure_token
    elif provider == AuthProvider.gcp:
        return validate_gcp_token
    else:
        raise ValueError(f"Unsupported authentication provider: {provider}")
