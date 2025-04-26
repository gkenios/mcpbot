from fastapi import APIRouter

from .create import messages_create, MessagesBody
from .delete import messages_delete
from mcpbot.shared.auth import UserAuth


router_v1 = APIRouter(prefix="/v1")



@router_v1.patch("conversations/{conversation_id}/messages/{message_id}")
async def messages_patch(
    user: UserAuth,
    conversation_id: str,
    message_id: str,
    body: MessagesBody,
):
    await messages_delete(
        user=user,
        conversation_id=conversation_id,
        message_id=message_id,
    )
    return messages_create(user, conversation_id, body)
