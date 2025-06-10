import random
from typing import Optional
from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.joan_api.common.api import JoanAPI, Reservation
from mcpbot.server.tools.joan_api.common.config import (
    TimeslotType,
    Timeslots,
)


def book_parking(
    context: Context,  # type: ignore[type-arg]
    date: str,
    timeslot: TimeslotType = "all_day",
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
) -> str:
    """Create a parking reservation for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        timeslot: The time slot for the reservation (Optional. Default: "all_day").
        time_from: The start time of the reservation in the format "HH:MM" (Optional. Default: None).
        time_to: The end time of the reservation in the format "HH:MM" (Optional. Default: None).
    """
    # Get email from context
    user_email = get_meta_context_value(context, "user_email")
    if not user_email:
        return "User not identified."

    # Timeslot handling
    joan_timeslot = Timeslots[timeslot.upper()].value
    if not time_from and not time_to:
        time_from = joan_timeslot.time_from
        time_to = joan_timeslot.time_to
    elif not time_from:
        time_from = Timeslots.ALL_DAY.value.time_from
    elif not time_to:
        time_to = Timeslots.ALL_DAY.value.time_to

    # Reserve parking
    api = JoanAPI()
    parking = api.get_available_parkings(user_email, date, time_from, time_to)
    if parking == Reservation.FULLY_BOOKED:
        return f"No parking spot available on {date}."
    elif parking == Reservation.RESERVATION_FOUND:
        return f"You already have a parking spot booked on {date}."
    else:
        parking_id = random.choice(parking)
        api.reserve_parking(
            email=user_email,
            parking_id=parking_id,
            date=date,
            time_from=time_from,
            time_to=time_to,
        )
        return "\n".join(
            [
                f"I have succesfully booked a parking:"
                f"- Time: {time_from} - {time_to}, {date}"
            ]
        )
