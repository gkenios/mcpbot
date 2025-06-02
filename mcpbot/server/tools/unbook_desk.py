from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.common.joan_api import JoanAPI


def unbook_desk(context: Context, date: str) -> str:  # type: ignore[type-arg]
    """Delete a desk reservation (or multiple) for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
    """
    # Context
    user_email = get_meta_context_value(context, "user_email")
    if not user_email:
        return "User not identified."

    api = JoanAPI()
    user_id, _ = api.get_user_id(user_email)
    if not user_id:
        return "User not found."

    api.delete_desk_reservation(user_id, date)
    return f"Desk reservation(s) deleted for {date}."
