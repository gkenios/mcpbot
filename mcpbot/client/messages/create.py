from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


from mcpbot.server.prompts import client_prompt
from mcpbot.shared.auth import UserAuth
from mcpbot.shared.config import PORT
from mcpbot.shared.init import config


router_v1 = APIRouter(prefix="/v1")


@router_v1.post("/{conversation_id}/messages")
async def messages_create(
    message: str,
    conversation_id: str,
    user: UserAuth,
) -> str:
    return StreamingResponse(
        chat_streamer(message, user.user_id),
        media_type="text/event-stream",
    )


async def chat_streamer(message, user_id):
    llm = config.models.llm
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
        stream = agent.astream({"messages": message}, stream_mode="messages")
        async for chunk, _ in stream:
            if isinstance(chunk, AIMessage):
                yield chunk.content


    #db = db_chat["messages"]
    # # Create the message in the database
    # human_message = db.create_message(
    #     conversation_id=conversation_id,
    #     user_id=user.user_id,
    #     role="human",
    #     text=message,
    # )
    # ai_message = db.create_message(
    #     conversation_id=conversation_id,
    #     user_id=user.user_id,
    #     role="ai",
    #     text=response,
    # )
    # return response