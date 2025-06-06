from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from mcpbot.client.oauth2 import UserAuth
from .create import messages_create, MessagesBody
from .delete import messages_delete


router_v1 = APIRouter(prefix="/v1")


@router_v1.patch("/conversations/{conversation_id}/messages/{message_id}")
async def messages_patch(
    user: UserAuth,
    conversation_id: str,
    message_id: str,
    body: MessagesBody,
) -> StreamingResponse:
    """Updates a message in the conversation. First, it deletes the message
    and all messages after it in the conversation. Then, it creates a new
    message with the new content.
    """
    await messages_delete(
        user=user,
        conversation_id=conversation_id,
        message_id=message_id,
    )
    return await messages_create(user, conversation_id, body)
