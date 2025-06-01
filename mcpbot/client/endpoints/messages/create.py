from datetime import datetime, UTC
from typing import AsyncGenerator
from uuid import uuid4

from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore[import-untyped]
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from mcpbot.client.oauth2 import UserAuth
from mcpbot.server.prompts import client_prompt
from mcpbot.shared.config import PORT
from mcpbot.shared.init import config
from mcpbot.shared.services.database_chat import Message


MESSAGE_LIMIT = 6
MESSAGE_MAP: dict[str, type[BaseMessage]] = {
    "human": HumanMessage,
    "ai": AIMessage,
}


class MessagesBody(BaseModel):
    message: str


class CreateMessageResponse(BaseModel):
    human: Message
    ai: Message


router_v1 = APIRouter(prefix="/v1")


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
        chat_streamer(history, conversation_id, user.user_id, user.email),
        media_type="text/event-stream",
    )


async def chat_streamer(
    messages: list[BaseMessage],
    conversation_id: str,
    user_id: str,
    email: str,
) -> AsyncGenerator[str, None]:
    llm = config.models.llm
    full_response: list[str] = []

    # Metadata
    human_message: str = messages[-1].content  # type: ignore[assignment]
    human_message_id = uuid4().hex
    human_created_at = datetime.now(UTC).isoformat()

    ai_message_id = uuid4().hex
    ai_created_at = datetime.now(UTC).isoformat()

    # Response object
    response = CreateMessageResponse(
        human=Message(
            role="human",
            text=human_message,
            id=human_message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            created_at=human_created_at,
        ),
        ai=Message(
            role="ai",
            text="",
            id=ai_message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            created_at=ai_created_at,
        ),
    )

    client = MultiServerMCPClient(
        {
            "mcpbot": {
                "url": f"http://localhost:{PORT}/mcp",
                "transport": "sse",
                "headers": {
                    "user_email": email,
                },
            }
        }
    )

    agent = create_react_agent(
        model=llm,
        tools=await client.get_tools(),
        prompt=client_prompt(),
    )
    stream = agent.astream({"messages": messages}, stream_mode="messages")
    async for chunk, _ in stream:
        if isinstance(chunk, AIMessage):
            full_response.append(chunk.content)  # type: ignore[arg-type]
            response.ai.text = chunk.content  # type: ignore[assignment]
            yield response.model_dump_json()

    response.ai.text = "".join(full_response)

    # Create the message in the database
    db_messages = config.databases.chat["messages"]
    db_conv = config.databases.chat["conversations"]
    db_messages.delete_over_n_messages(conversation_id, MESSAGE_LIMIT)
    db_messages.create_message(**response.human.model_dump())
    db_messages.create_message(**response.ai.model_dump())
    db_conv.update_conversation_timestamp(conversation_id, user_id=user_id)
