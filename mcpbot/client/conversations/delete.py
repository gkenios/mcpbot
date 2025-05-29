from typing import Any
from fastapi import APIRouter

from mcpbot.shared.init import UserAuth, config


router_v1 = APIRouter(prefix="/v1")


@router_v1.delete("/conversations/{conversation_id}")
async def conversations_delete(
    conversation_id: str,
    user: UserAuth,
) -> dict[str, Any]:
    """Deletes a conversation by its ID."""
    db = config.databases.chat["conversations"]
    db_messages = config.databases.chat["messages"]

    db.delete_conversation(conversation_id, user.user_id)
    db_messages.delete_all_messages(conversation_id)
    return {}
