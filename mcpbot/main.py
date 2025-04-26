from fastapi import FastAPI, HTTPException, Request, Response, status
from mcp.server import FastMCP
from mcp.server.sse import SseServerTransport

from mcpbot.client.conversations import (
    conversations_create,
    conversations_delete,
    conversations_list, 
)
from mcpbot.client.messages import (
    messages_create,
)
from mcpbot.server import (
    prompts,
    tools,
    add_prompts_from_module,
    add_tools_from_module,
    inject_meta_context,
)
from mcpbot.shared.auth import validate_user
from mcpbot.shared import token


TITLE = "MCP Client & Server"
MCP_MESSAGES_ENDPOINT = "/mcp/messages/"


# FastAPI
app = FastAPI(
    title=TITLE,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    docs_url="/",
)
app.include_router(token.router, tags=["Auth"])
app.include_router(conversations_create.router_v1, tags=["Conversations"])
app.include_router(conversations_delete.router_v1, tags=["Conversations"])
app.include_router(conversations_list.router_v1, tags=["Conversations"])
app.include_router(messages_create.router_v1, tags=["Messages"])

# MCP Server
sse=SseServerTransport(MCP_MESSAGES_ENDPOINT)
mcp=FastMCP(name=TITLE)
add_prompts_from_module(mcp, prompts)
add_tools_from_module(mcp, tools)


# MCP Server Routers
@app.get("/mcp", tags=["MCP"])
async def sse_endpoint(request: Request) -> Response:
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as (reader, writer):
        await mcp._mcp_server.run(
            reader,
            writer,
            mcp._mcp_server.create_initialization_options(),
        )
    return Response(status_code=200)


@app.post(MCP_MESSAGES_ENDPOINT, tags=["MCP"])
async def post_endpoint(request: Request) -> None:
    return await sse.handle_post_message(
        request.scope, request.receive, request._send
    )


# Middleware for Authentication
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    is_local_call = request.client.host == "127.0.0.1"
    is_mcp_call = request.url.path.lower().startswith("/mcp")

    # If it's client call, proceed with the request
    if not is_mcp_call:
        return await call_next(request)
    # If it's an MCP Server request but it is local, skip authentication
    elif is_mcp_call and is_local_call:
        email = request.headers.get("client_id")
    # If it's an external MCP Server request, authenticate the user
    else:
        token = request.headers.get("Authorization")
        try:
            token = token.split(" ", 1)[1]
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        user = await validate_user(token)
        email = user.user_id

    # Inject the user email into the meta context
    meta_context = {"client_id": email}
    request = await inject_meta_context(request, meta_context)
    return await call_next(request)
