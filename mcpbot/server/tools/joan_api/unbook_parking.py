from typing import Optional

from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.joan_api.common.api import JoanAPI, Reservation
from mcpbot.server.tools.joan_api.common.config import (
    TimeslotType,
    Timeslots,
)


def unbook_parking(
    context: Context,  # type: ignore[type-arg]
    date: str,
    timeslot: TimeslotType = "all_day",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> str:
    """Delete a parking reservation for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        timeslot: The time slot for the reservation (Optional. Default: "all_day").
        start_time: The start time of the reservation in the format "HH:MM" (Optional. Default: None).
        end_time: The end time of the reservation in the format "HH:MM" (Optional. Default: None).
    """
    # Context
    user_email = get_meta_context_value(context, "user_email")
    if not user_email:
        return "User not identified."

    # Timeslot handling
    joan_timeslot = Timeslots[timeslot.upper()].value
    if not start_time and not end_time:
        start_time = joan_timeslot.time_from
        end_time = joan_timeslot.time_to
    elif not start_time:
        start_time = Timeslots.ALL_DAY.value.time_from
    elif not end_time:
        end_time = Timeslots.ALL_DAY.value.time_to

    # Get parking reservation
    api = JoanAPI()
    parking_id = api.get_own_parking(user_email, date, start_time, end_time)

    # Delete parking reservation if it exists
    if parking_id == Reservation.RESERVATION_NOT_FOUND:
        return f"No parking reservation found for {date}: {start_time} - {end_time}."
    else:
        print("Parking ID", parking_id)
        api.delete_parking(user_email, parking_id)
        return f"Parking reservation deleted for {date}."
