import json
from types import ModuleType

from mcp.server import FastMCP
from mcp.server.fastmcp.prompts import Prompt
from starlette.requests import Request


async def inject_meta_context(
    request: Request,
    context: dict[str, str],
) -> Request:
    """Injects meta context to the request.
    
    Args:
        request: The request object.
        context: The context to add to the params['_meta'] of the request.

    Returns:
        The request body with the added context, json encoded.
    """
    body = await request.body()
    if not body:
        return request

    # Get the request body and decode it
    json_data = json.loads(body)
    params = json_data.get("params", {})
    meta = params.get("_meta", {})

    # Add the context to the meta in params
    params["_meta"] = meta | context
    json_data["params"] = params
    request._body = json.dumps(json_data).encode("utf-8")

    return request


def add_prompts_from_module(server: FastMCP, module: ModuleType) -> None:
    """Adds all prompts from a module to the server."""
    for prompt in dir(module):
        if not prompt.startswith("__") or not prompt.endswith("__"):
            attribute = getattr(module, prompt)
            if callable(attribute):
                server.add_prompt(Prompt.from_function(attribute))


def add_tools_from_module(server: FastMCP, module: ModuleType):
    """Adds all tools from a module to the server."""
    for tool in dir(module):
        if not tool.startswith("__") or not tool.endswith("__"):
            attribute = getattr(module, tool)
            if callable(attribute):
                server.add_tool(attribute)
