from typing import Any

from fastapi import APIRouter

from mcpbot.shared.init import UserAuth, config


router_v1 = APIRouter(prefix="/v1")


@router_v1.delete("/conversations/{conversation_id}/messages/{message_id}")
async def messages_delete(
    user: UserAuth,
    conversation_id: str,
    message_id: str,
) -> dict[str, Any]:
    """Deletes a message and all messages after it in the conversation."""
    db = config.databases.chat["messages"]
    ordered_messages = db.list_messages(conversation_id, order_by="DESC")
    if message_id not in [message.id for message in ordered_messages]:
        return {}

    # Delete all messages after the message_id inclusive
    for i, message in enumerate(ordered_messages):
        db.delete_message(message.id, conversation_id)
        if message.id == message_id:
            if message.role == "ai":
                db.delete_message(ordered_messages[i + 1].id, conversation_id)
            break
    return {}
