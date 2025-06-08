from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.joan_api.common.api import JoanAPI


def unbook_desk(context: Context, date: str) -> str:  # type: ignore[type-arg]
    """Delete a desk reservation (or multiple) for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
    """
    # Get email from context
    user_email = get_meta_context_value(context, "user_email")
    if not user_email:
        return "User not identified."

    # Check if the user exists in Joan
    api = JoanAPI()
    status = api.get_admin_status(user_email)
    if status is None:
        return "User not found."

    # Delete desk reservation(s)
    api.delete_desk(user_email, date)
    return f"Desk reservation(s) deleted for {date}."
