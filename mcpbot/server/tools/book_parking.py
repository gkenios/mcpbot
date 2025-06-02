from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.common.joan_api import JoanAPI, Reservation


def book_parking(
    context: Context,  # type: ignore[type-arg]
    date: str,
    start_time: str = "09:00",
    end_time: str = "17:00",
) -> str:
    """Create a parking reservation for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        start_time: The start time of the reservation in the format "HH:MM". The
            default value is 09:00.
        end_time: The end time of the reservation in the format "HH:MM". The
            default value is 17:00.
    """
    # Context
    user_email = get_meta_context_value(context, "user_email")

    api = JoanAPI()
    parking = api.get_free_parking_spot(user_email, date, start_time, end_time)
    if parking == Reservation.FULLY_BOOKED:
        return f"No parking spot available on {date}."
    elif parking == Reservation.RESERVATION_FOUND:
        return f"You already have a parking spot booked on {date}."
    else:
        api.create_parking_reservation(
            email=user_email,
            parking_spot_id=parking,
            date=date,
            start_time=start_time,
            end_time=end_time,
        )
        return f"Parking spot reserved for on {date} from {start_time} to {end_time}."
