from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from mcpbot.shared.auth import Token, create_access_token


router = APIRouter()


@router.post("/token")
async def token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    is_correct_username = form_data.username.endswith("@devoteam.com")
    is_correct_password = form_data.password == "gg"
    authenticated = is_correct_username and is_correct_password

    if not authenticated:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(
        data={"sub": form_data.username, "scopes": form_data.scopes},
    )
    return Token(access_token=access_token, token_type="bearer")
