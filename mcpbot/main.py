from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.middleware.base import RequestResponseEndpoint

from mcpbot.client.endpoints.auth.token import router as auth_router
from mcpbot.client.endpoints.conversations import (
    conversations_create,
    conversations_delete,
    conversations_list,
)
from mcpbot.client.endpoints.messages import (
    messages_create,
    messages_delete,
    messages_list,
    messages_patch,
)
from mcpbot.client.oauth2 import validate_access_token
from mcpbot.server import prompts, tools
from mcpbot.server.common import add_prompts_from_module, add_tools_from_module
from mcpbot.server.context import MetaContext, inject_meta_context
from mcpbot.shared.config import CORS_ORIGINS


TITLE = "MCP Client & Server"
MCP_MESSAGES_ENDPOINT = "/mcp/messages/"


# FastAPI
app = FastAPI(
    title=TITLE,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    docs_url="/",
)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=CORS_ORIGINS,
)

app.include_router(auth_router, tags=["Auth"])
app.include_router(conversations_create.router_v1, tags=["Conversations"])
app.include_router(conversations_delete.router_v1, tags=["Conversations"])
app.include_router(conversations_list.router_v1, tags=["Conversations"])
app.include_router(messages_create.router_v1, tags=["Messages"])
app.include_router(messages_delete.router_v1, tags=["Messages"])
app.include_router(messages_list.router_v1, tags=["Messages"])
app.include_router(messages_patch.router_v1, tags=["Messages"])

# MCP Server
sse = SseServerTransport(MCP_MESSAGES_ENDPOINT)
mcp = FastMCP(name=TITLE)
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
async def add_process_time_header(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    is_mcp_call = request.url.path.lower().startswith("/mcp")
    if not request.client:
        is_local_call = False
    else:
        is_local_call = request.client.host == "127.0.0.1"

    # If it's client call, proceed with the request
    if not is_mcp_call:
        return await call_next(request)
    # If it's an MCP Server request but it is local, skip authentication
    elif is_mcp_call and is_local_call:
        email = request.headers.get("user_email")
        if not email:
            raise ValueError("Missing user_email header in local MCP request.")
    # If it's an external MCP Server request, authenticate the user
    else:
        token = request.headers.get("Authorization")
        if not token:
            raise ValueError("Missing Authorization header in MCP request.")
        try:
            token = token.split(" ", 1)[1]
        except Exception as error:
            raise ValueError("Invalid Authorization header format") from error
        user = validate_access_token(token)
        email = user.email

    # Inject the user email into the meta context
    meta_context = MetaContext(user_email=email)
    request = await inject_meta_context(request, meta_context)
    return await call_next(request)
