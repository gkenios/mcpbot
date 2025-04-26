from fastapi import APIRouter

from mcpbot.shared.auth import UserAuth
from mcpbot.shared.init import config


router_v1 = APIRouter(prefix="/v1")


@router_v1.get("/conversations")
async def conversations_list(user: UserAuth) -> list[str]:
    """Lists all conversations for the authenticated user."""
    db = config.databases.chat["conversations"]
    return db.list_conversations(user.user_id)
