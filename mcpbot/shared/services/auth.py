from enum import StrEnum
import os
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.exceptions import GoogleAuthError
from pydantic import BaseModel

from mcpbot.shared.config import COMPANY


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthProvider(StrEnum):
    local = "local"
    azure = "azure"
    gcp = "gcp"


class User(BaseModel):
    user_id: str


def validate_local_token() -> User:
    """Skip local authentication. Return user based on environment variable."""
    return User(user_id=os.getenv("USER_EMAIL"))


async def validate_azure_token(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    raise NotImplementedError("Azure token validation is not implemented yet.")


async def validate_gcp_token(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """
    Validate a Google authentication token and return the user information.

    :param token: The Google authentication token to validate.
    :return: User information if the token is valid.
    :raises HTTPException: If the token is invalid or does not match the
        expected domain.
    """
    try:
        request = requests.Request()
        payload = id_token.verify_oauth2_token(token, request, audience=None)
    except GoogleAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from error

    if hd := payload.get("hd"):
        if hd != f"{COMPANY}.com":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: Domain mismatch.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    if email := payload.get("email"):
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: User identity not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return User(user_id=email)


def get_auth_method(provider: AuthProvider) -> Callable[[str], User]:
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
