from typing import Literal

from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.common.joan_api import (
    JOAN_TIMESLOTS,
    JoanAPI,
    Timeslot,
)


def book_desk(
    context: Context,  # type: ignore[type-arg]
    date: str,
    people: int = 1,
    city: str = "Amsterdam",
    timeslot: Literal["morning", "afternoon", "all_day"] = "all_day",
    floor: int | None = None,
    desk_name: str | None = None,
) -> str:
    """Creates a desk reservation (or multiple) for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        people: The number of people to book desks for.
        city: The city where the office is located.
        timeslot: The time slot for the reservation. It can be in:
          - morning
          - afternoon
          - all_day
          The default value is all_day.
        floor: The floor number where the desk is located.
        desk_name: The name of the desk to book. It can be in:
          - dual monitor
          - single monitor
          - bar
          - lounge
          - round table
          The default value is single monitor.
    """
    # Context
    user_email = get_meta_context_value(context, "user_email")
    joan_timeslot: Timeslot = getattr(JOAN_TIMESLOTS, timeslot)

    if not user_email:
        return "User not identified."

    # Default office (Amsterdam, 3rd floor)
    if city.lower() == "amsterdam" and floor is None:
        floor = 3

    api = JoanAPI()
    user_id, is_admin = api.get_user_id(user_email)

    # Check if user exists
    if not user_id:
        return "User not found."

    # If the user is not an admin, they can only book one desk per day
    elif not is_admin:
        people = 1
        if api.get_desk_reservation(
            user_id=user_id,
            date=date,
            time_from=joan_timeslot.time_from,
            time_to=joan_timeslot.time_to,
        ):
            return "You already have a desk booked for this date. You cannot make more than one reservation."

    building_id, floor_id = api.get_location(city, floor)
    number_of_seats = api.get_number_of_free_seats(
        building_id=building_id,
        floor_id=floor_id,
        date=date,
        desk_name=desk_name,
        time_from=joan_timeslot.time_from,
        time_to=joan_timeslot.time_to,
    )
    # Check if enough seats are available for the requested number of people
    if number_of_seats < people:
        return f"You requested desks for {people} people, but only {number_of_seats} are available."

    excluded_seats: list[str] = []
    for i in range(people):
        seat_id = api.get_seat_id(
            building_id,
            floor_id,
            date,
            desk_name,
            excluded_seats=excluded_seats,
            time_from=joan_timeslot.time_from,
            time_to=joan_timeslot.time_to,
        )
        if not seat_id:
            return f"While booking, someone else booked a desk and there are not enough desks. I booked {i} desks."

        api.create_desk_reservation(
            email=user_email,
            seat_id=seat_id,
            date=date,
            time_from=joan_timeslot.time_from,
            time_to=joan_timeslot.time_to,
        )
        excluded_seats.append(seat_id)
    return f"Desk(s) booked for {people} people on {date}."
