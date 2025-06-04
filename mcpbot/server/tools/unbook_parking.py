from typing import Literal

from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.common.joan_api import (
    JoanAPI,
    JOAN_TIMESLOTS,
    Reservation,
    Timeslot,
)


def unbook_parking(
    context: Context,  # type: ignore[type-arg]
    date: str,
    start_time: str | None = None,
    end_time: str | None = None,
    timeslot: Literal["morning", "afternoon", "all_day"] = "all_day",
) -> str:
    """Delete a parking reservation for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        start_time: The start time of the reservation in the format "HH:MM".
          This is optional.
        end_time: The end time of the reservation in the format "HH:MM".
          This is optional.
        timeslot: The time slot for the reservation. It can be in:
          - morning
          - afternoon
          - all_day
        The default value is all_day.
    """
    # Context
    user_email = get_meta_context_value(context, "user_email")
    if not user_email:
        return "User not identified."

    # Timeslot handling
    joan_timeslot: Timeslot = getattr(JOAN_TIMESLOTS, timeslot)
    if not start_time and not end_time:
        start_time = joan_timeslot.time_from
        end_time = joan_timeslot.time_to
    elif not start_time:
        start_time = JOAN_TIMESLOTS.all_day.time_from
    elif not end_time:
        end_time = JOAN_TIMESLOTS.all_day.time_to

    api = JoanAPI()
    parking = api.get_user_parking_spot(user_email, date, start_time, end_time)
    if parking == Reservation.RESERVATION_NOT_FOUND:
        return f"No parking reservation found for {date}: {start_time} - {end_time}."
    else:
        api.delete_parking_reservation(parking)
        return f"Parking reservation deleted for {date}."
