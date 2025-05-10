from fastapi import APIRouter

from mcpbot.shared.auth import UserAuth
from mcpbot.shared.init import config
from mcpbot.shared.services.database_chat import Message, OrderBy


router_v1 = APIRouter(prefix="/v1")


@router_v1.get("/conversations/{conversation_id}/messages")
async def messages_list(
    user: UserAuth,
    conversation_id: str,
    order_by: OrderBy = "ASC",
) -> list[Message]:
    """Lists all messages of a conversation."""
    db = config.databases.chat["messages"]
    return db.list_messages(conversation_id, order_by)
