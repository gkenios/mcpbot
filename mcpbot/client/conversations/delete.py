from fastapi import APIRouter

from mcpbot.shared.auth import UserAuth
from mcpbot.shared.init import config


router_v1 = APIRouter(prefix="/v1")


@router_v1.delete("/conversations/{conversation_id}")
async def conversations_delete(conversation_id: str, user: UserAuth) -> None:
    """Deletes a conversation by its ID."""
    db = config.databases.chat["conversations"]
    return db.delete_conversation(conversation_id, user.user_id)
