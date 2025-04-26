from typing import AsyncGenerator

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


MESSAGE_LIMIT = 6
MESSAGE_MAP: dict[str, type[BaseMessage]] = {
    "human": HumanMessage,
    "ai": AIMessage,
}

router_v1 = APIRouter(prefix="/v1")


class MessagesBody(BaseModel):
    message: str


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
        media_type="text/event-stream",
    )


async def chat_streamer(
    messages: list[BaseMessage], conversation_id: str, user_id: str
) -> AsyncGenerator[str, None]:
    llm = config.models.llm
    full_response = ""
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
                chunck_content: str = chunk.content  # type: ignore
                full_response += chunck_content
                yield chunck_content

    # Create the message in the database
    message: str = messages[-1].content  # type: ignore
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
        text=message,
    )
    db_messages.create_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="ai",
        text=full_response,
    )
    db_conv.update_conversation_timestamp(conversation_id, user_id=user_id)
