from typing import Annotated, Literal

from fastapi import APIRouter, Form
from mcp.shared.auth import OAuthToken

from mcpbot.client.oauth2 import (
    create_access_token_from_password,
    create_access_token_from_refresh,
)
from mcpbot.shared.init import config


router = APIRouter()


@router.post("/token")
async def token(
    token: Annotated[str, Form()],
    grant_type: Annotated[
        Literal["authorization_code", "refresh_token"],
        Form(),
    ] = "authorization_code",
) -> OAuthToken:
    """Generates an access token based on the provided grant type.
    - `authorization_code`: Uses the provided token to exchange for an access token.
    - `refresh_token`: Uses the provided token to refresh the access token.

    When refreshing a token, the refresh token will not be refreshed, but only
    the access token. In order to get a new refresh token, the user must
    re-authenticate using the authorization code flow.
    """
    if grant_type == "authorization_code":
        exchange_token = config.auth(token)
        return create_access_token_from_password(exchange_token)
    elif grant_type == "refresh_token":
        return create_access_token_from_refresh(token)
