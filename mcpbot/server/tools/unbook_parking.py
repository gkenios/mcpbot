from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.common.joan_api import JoanAPI, Reservation


def unbook_parking(
    context: Context,  # type: ignore[type-arg]
    date: str,
    start_time: str = "09:00",
    end_time: str = "17:00",
) -> str:
    """Delete a parking reservation for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        start_time: The start time of the reservation in the format "HH:MM". The
            default value is 09:00.
        end_time: The end time of the reservation in the format "HH:MM". The
            default value is 17:00.
    """
    # Context
    user_email = get_meta_context_value(context, "user_email")
    if not user_email:
        return "User not identified."

    api = JoanAPI()
    parking = api.get_user_parking_spot(user_email, date, start_time, end_time)
    if parking == Reservation.RESERVATION_NOT_FOUND:
        return f"No parking reservation found for {date}: {start_time} - {end_time}."
    else:
        api.delete_parking_reservation(parking)
        return f"Parking reservation deleted for {date}."
