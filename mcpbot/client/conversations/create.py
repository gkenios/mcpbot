from fastapi import APIRouter

from mcpbot.shared.auth import UserAuth
from mcpbot.shared.init import config
from mcpbot.shared.services.database_chat import Conversation


router_v1 = APIRouter(prefix="/v1")


@router_v1.post("/conversations")
async def conversations_create(user: UserAuth) -> Conversation:
    """Creates a new conversation.
    
    It returns:
    - id: The ID of the conversation.
    - user_id: The ID of the user who created the conversation.
    - created_at: The timestamp when the conversation was created.
    - last_updated_at: The timestamp when the conversation was last updated.
    """
    db = config.databases.chat["conversations"]
    return db.create_conversation(user.user_id)
