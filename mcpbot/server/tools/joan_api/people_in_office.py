from typing import Optional

from mcpbot.server.tools.joan_api.common.api import JoanAPI
from mcpbot.server.tools.joan_api.common.config import (
    Building,
    BuildingType,
    LOCATIONS,
)


def people_in_office(
    date: str,
    name: Optional[str] = None,
    building: Optional[BuildingType] = None,
) -> str:
    """Find which people will be in the office on a given date. If a specific
    name is provided, only return information about that person. Even if one
    person is matched, mention ALWAYS the full name of the person.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        name: The name of the person to check (Optional. Default: None).
        building: The building to check (Optional. Default: None).
    """
    if building:
        building = Building(building)
        for city_data in LOCATIONS.values():
            for building_key, building_data in city_data["buildings"].items():
                if building == building_key:
                    building_id = building_data["building_id"]
    else:
        building_id = None

    api = JoanAPI()
    people = api.get_people_in_the_office(date, name, building_id)

    if name:
        if not people:
            return f"{people} is not in the office on {date}."
        else:
            return f"{people} is in the office on {date}."
    else:
        if not people:
            return f"No one is in the office on {date}."
        else:
            return f"People in the office on {date}: {people}."
