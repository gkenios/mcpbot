import random
from typing import Optional

from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.server.tools.joan_api.common.api import JoanAPI
from mcpbot.server.tools.joan_api.common.config import (
    Building,
    BuildingType,
    City,
    CityType,
    Desk,
    DeskType,
    LOCATIONS,
    TimeslotType,
    Timeslots,
)


def book_desk(
    context: Context,  # type: ignore[type-arg]
    date: str,
    timeslot: Optional[TimeslotType] = "all_day",
    city: Optional[CityType] = "amsterdam",
    building: Optional[BuildingType] = None,
    floor: Optional[int] = None,
    desk_type: Optional[DeskType] = None,
    desk_number_id: Optional[int] = None,
    people: Optional[int] = 1,
) -> str:
    """Creates a desk reservation (or multiple) for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        timeslot: The time slot for the reservation.
        city: The city where the office is located as Enum.
        building: The name of the building to book.
        floor: The floor number where the desk is located.
        desk_type: The name of the desk to book.
        desk_number_id: The ID of the desk to book.
        people: The number of people to book desks for.
    """
    # Get email from context
    user_email = get_meta_context_value(context, "user_email")
    if not user_email:
        return "User not identified."

    # Check if the user exists in Joan
    api = JoanAPI()
    is_admin = api.get_admin_status(user_email)
    if is_admin is None:
        return "User not found."

    # If the user is not an admin, they can only book one desk per day
    joan_timeslot = Timeslots[timeslot.upper()].value
    if not is_admin:
        people = 1
        if api.get_own_desks(
            email=user_email,
            date=date,
            time_from=joan_timeslot.time_from,
            time_to=joan_timeslot.time_to,
        ):
            return "You already have a desk booked for this date. You cannot make more than one reservation."

    # Get the building and floor IDs
    city = City(city)
    print("Building:", building)
    building = (
        Building(building) if building else LOCATIONS[city]["default_building"]
    )
    floor = (
        floor
        if floor is not None
        else LOCATIONS[city]["buildings"][building]["default_floor"]
    )
    desk_type = (
        Desk(desk_type)
        if desk_type and building == Building.KEYNESS
        else LOCATIONS[city]["buildings"][building]["floors"][floor][
            "default_desk_type"
        ]
    )
    building_name = LOCATIONS[city]["buildings"][building]["name"]
    building_id = LOCATIONS[city]["buildings"][building]["building_id"]
    floor_id = LOCATIONS[city]["buildings"][building]["floors"][floor][
        "floor_id"
    ]

    # Get the available desks
    free_desks = api.get_available_desks(
        building_id=building_id,
        floor_id=floor_id,
        date=date,
        desk_type=desk_type,
        desk_number_id=desk_number_id,
        time_from=joan_timeslot.time_from,
        time_to=joan_timeslot.time_to,
    )

    # Check if enough seats are available for the requested number of people
    if len(free_desks) < people:
        if people == 1:
            all_free_desks = api.get_available_desks(
                building_id=building_id,
                floor_id=floor_id,
                date=date,
                desk_type=None,
                desk_number_id=None,
                time_from=joan_timeslot.time_from,
                time_to=joan_timeslot.time_to,
            )
            if not all_free_desks:
                return "No desks available for this date."
            else:
                return f"No desks of the requested type available for {date}. Available desks: {', '.join(seat.name for seat in all_free_desks)}"
        else:
            return f"You requested desks for {people} people, but only {len(free_desks)} are available."

    # Make the reservations
    for _ in range(people):
        desk_index = random.randint(0, len(free_desks) - 1)
        desk_id = free_desks[desk_index]["id"]

        api.reserve_desk(
            email=user_email,
            desk_id=desk_id,
            date=date,
            timeslot=joan_timeslot,
        )
        last_desk = free_desks.pop(desk_index)

    if people == 1:
        return "\n".join(
            [
                f"I have succesfully booked a desk:"
                f"- Time: {joan_timeslot.time_from} - {joan_timeslot}, {date}"
                f"- Desk: {last_desk['name']}"
                f"- Office: {building_name}, floor {floor}"
            ]
        )
    else:
        return f"Desk(s) booked for {people} people on {date}."
