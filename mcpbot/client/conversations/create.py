from fastapi import APIRouter

from mcpbot.shared.auth import UserAuth
from mcpbot.shared.init import config
from mcpbot.shared.services.database_chat import Conversation


router_v1 = APIRouter(prefix="/v1")


@router_v1.post("/conversations")
async def conversations_create(
    user: UserAuth,
    conversation_id: str | None = None,
) -> Conversation:
    """Creates a new conversation.
    
    It returns:
    - id: The ID of the conversation.
    - user_id: The ID of the user who created the conversation.
    - created_at: The timestamp when the conversation was created.
    - last_updated_at: The timestamp when the conversation was last updated.
    """
    # In this implementation, we want 1 conversation per user.
    if not conversation_id:
        conversation_id = user.user_id
    
    db = config.databases.chat["conversations"]
    if existing_conv := db.get_conversation(conversation_id, user.user_id):
        return existing_conv
    return db.create_conversation(user.user_id, conversation_id=conversation_id)
