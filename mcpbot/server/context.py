import json

from mcp.server.fastmcp import Context
from pydantic import BaseModel
from starlette.requests import Request


class MetaContext(BaseModel):
    user_email: str


def get_meta_context_value(context: Context, key: str) -> str | None:
    return (
        getattr(context.request_context.meta, key, None)
        if context.request_context.meta is not None
        else None
    )


async def inject_meta_context(
    request: Request,
    context: dict[str, str] | BaseModel,
) -> Request:
    """Injects meta context to the request.
    
    Args:
        request: The request object.
        context: The context to add to the params['_meta'] of the request.

    Returns:
        The request body with the added context, json encoded.
    """
    if isinstance(context, BaseModel):
        context = context.model_dump()

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
