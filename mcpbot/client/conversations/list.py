from fastapi import APIRouter

from mcpbot.shared.auth import UserAuth
from mcpbot.shared.init import config
from mcpbot.shared.services.database_chat import Conversation, OrderBy


router_v1 = APIRouter(prefix="/v1")


@router_v1.get("/conversations")
async def conversations_list(
    user: UserAuth, order_by: OrderBy = "DESC"
) -> list[Conversation]:
    """Lists all conversations for the authenticated user."""
    db = config.databases.chat["conversations"]
    return db.list_conversations(user.user_id, order_by)
