import time
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from mcp.shared.auth import OAuthToken
from pydantic import BaseModel

from mcpbot.shared.config import HOST_URL
from mcpbot.shared.init import config
from mcpbot.shared.services.auth import CommonTokenParams


ACCESS_TOKEN_EXPIRES_IN = 3600  # 1 hour
REFRESH_TOKEN_EXPIRES_IN = 3600 * 24  # 1 Day


class TokenParams(CommonTokenParams):
    iat: int
    exp: int
    iss: str


class User(BaseModel):
    user_id: str
    email: str


DefinedTokenParams = dict[str, Any] | CommonTokenParams

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_token(
    data: DefinedTokenParams,
    expires_in: int,
    encryption_key: str,
) -> OAuthToken:
    issued_at = int(time.time())

    if isinstance(data, BaseModel):
        data = data.model_dump()

    token_data = TokenParams(
        **data,
        iss=HOST_URL,
        iat=issued_at,
        exp=issued_at + expires_in,
    )

    return jwt.encode(
        payload=token_data.model_dump(),
        key=encryption_key,
        algorithm="HS256",
    )


def create_access_token_from_password(data: DefinedTokenParams) -> OAuthToken:
    access_token = create_token(
        data=data,
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        encryption_key=config.secrets["access_token_key"],
    )
    refresh_token = create_token(
        data=data,
        expires_in=REFRESH_TOKEN_EXPIRES_IN,
        encryption_key=config.secrets["refresh_token_key"],
    )
    return OAuthToken(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        scope=None,
    )


def create_access_token_from_refresh(refresh_token: str) -> OAuthToken:
    data = validate_refresh_token(refresh_token)
    access_token = create_token(
        data=data,
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        encryption_key=config.secrets["access_token_key"],
    )
    return OAuthToken(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        scope=None,
    )


def validate_token(
    token: str,
    encryption_key: str,
) -> CommonTokenParams:
    try:
        payload = jwt.decode(
            token,
            key=encryption_key,
            algorithms=["HS256"],
            options={"verify_iat": True, "verify_exp": True},
            issuer=HOST_URL,
        )
        return CommonTokenParams(**payload)
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")


def validate_access_token(token: str) -> CommonTokenParams:
    return validate_token(token, config.secrets["access_token_key"])


def validate_refresh_token(token: str) -> CommonTokenParams:
    return validate_token(token, config.secrets["refresh_token_key"])


async def validate_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    Validate the user based on the provided token.

    Args:
        token: The access token to validate.

    Returns:
        The User object containing user_id and email.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        token_data = validate_access_token(token)
        return User(user_id=token_data.sub, email=token_data.email)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )


UserAuth = Annotated[User, Depends(validate_user)]
