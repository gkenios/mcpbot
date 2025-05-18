from datetime import datetime, UTC
import json
from typing import AsyncGenerator, Literal
from uuid import uuid4

from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore[import-untyped]
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from mcpbot.server.prompts import client_prompt
from mcpbot.shared.auth import UserAuth
from mcpbot.shared.config import PORT
from mcpbot.shared.init import config
from mcpbot.shared.services.database_chat import Role


MESSAGE_LIMIT = 6
MESSAGE_MAP: dict[str, type[BaseMessage]] = {
    "human": HumanMessage,
    "ai": AIMessage,
}

router_v1 = APIRouter(prefix="/v1")


class MessagesBody(BaseModel):
    message: str


class CreateMessageResponse(BaseModel):
    response_type: Literal["partial", "full"] = "partial"
    text: str
    id: str
    conversation_id: str
    user_id: str
    role: Role
    created_at: str


@router_v1.post("/conversations/{conversation_id}/messages")
async def messages_create(
    user: UserAuth,
    conversation_id: str,
    body: MessagesBody,
) -> StreamingResponse:
    """Creates a new message in the conversation. The answer is streamed."""
    db_messages = config.databases.chat["messages"]
    history = [
        MESSAGE_MAP[entry.role](content=entry.text)
        for entry in db_messages.list_messages(conversation_id)
    ]
    history.append(HumanMessage(content=body.message))
    return StreamingResponse(
        chat_streamer(history, conversation_id, user.user_id),
        media_type="application/x-ndjson",
    )


async def chat_streamer(
    messages: list[BaseMessage], conversation_id: str, user_id: str
) -> AsyncGenerator[str, None]:
    llm = config.models.llm
    full_response: list[str] = []

    human_message: str = messages[-1].content  # type: ignore[assignment]
    human_message_id = uuid4().hex
    human_created_at = datetime.now(UTC).isoformat()

    ai_message_id = uuid4().hex
    ai_created_at = datetime.now(UTC).isoformat()

    human_message_item = CreateMessageResponse(
        id=human_message_id,
        conversation_id=conversation_id,
        user_id=user_id,
        role="human",
        text=human_message,
        created_at=human_created_at,
    )
    ai_message_item = CreateMessageResponse(
        id=ai_message_id,
        conversation_id=conversation_id,
        user_id=user_id,
        role="ai",
        text="",
        created_at=ai_created_at,
    )

    human_message_item_dict = human_message_item.model_dump()

    async with MultiServerMCPClient(
        {
            "mcpbot": {
                "url": f"http://localhost:{PORT}/mcp",
                "transport": "sse",
                "headers": {
                    "user_email": user_id,
                },
            }
        }
    ) as client:
        agent = create_react_agent(
            model=llm,
            tools=client.get_tools(),
            prompt=client_prompt(),
            version="v2",
        )
        stream = agent.astream({"messages": messages}, stream_mode="messages")
        async for chunk, _ in stream:
            if isinstance(chunk, AIMessage):
                full_response.append(chunk.content)  # type: ignore[arg-type]
                ai_message_item.text = chunk.content  # type: ignore[arg-type]
                yield json.dumps(
                    [
                        human_message_item_dict,
                        ai_message_item.model_dump(),
                    ]
                )

    # Update response objects
    ai_message = "".join(full_response)
    ai_message_item.text = ai_message
    human_message_item.response_type = "full"
    ai_message_item.response_type = "full"

    # Create the message in the database
    db_messages = config.databases.chat["messages"]
    db_conv = config.databases.chat["conversations"]

    db_messages.delete_over_n_messages(
        conversation_id=conversation_id,
        n_messages=MESSAGE_LIMIT,
    )
    db_messages.create_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="human",
        text=human_message,
        id=human_message_id,
        created_at=human_created_at,
    )
    db_messages.create_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="ai",
        text=ai_message,
        id=ai_message_id,
        created_at=ai_created_at,
    )
    db_conv.update_conversation_timestamp(conversation_id, user_id=user_id)

    yield json.dumps(
        [human_message_item.model_dump(), ai_message_item.model_dump()]
    )
