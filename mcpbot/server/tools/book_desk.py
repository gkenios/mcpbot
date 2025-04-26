import re
from typing import Any, TypedDict

import httpx
from mcp.server.fastmcp import Context

from mcpbot.server.context import get_meta_context_value
from mcpbot.shared.init import config


def book_desk(
    context: Context[Any, Any],
    date: str,
    people: int = 1,
    city: str = "Amsterdam",
    floor: int | None = None,
    desk_name: str | None = None,
) -> str:
    """Creates a desk reservation (or multiple) for a user on a given date.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        people: The number of people to book desks for.
        city: The city where the office is located.
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

    # Secrets
    secrets = config.secrets
    client_id = secrets["joan_client_id"]
    client_secret = secrets["joan_client_secret"]
    company_id = secrets["joan_company_id"]

    if not user_email:
        return "User not identified."

    token = get_token(client_id, client_secret)
    user_id, is_admin = get_user_id(token, company_id, user_email)
    if not user_id:
        return "User not found."
    if not is_admin:
        people = 1
        if get_desk_reservation(token, company_id, user_id, date):
            return "You already have a desk booked for this date."

    building_id, floor_id = get_location(token, company_id, city, floor)
    number_of_seats = get_number_of_free_seats(
        token, building_id, floor_id, date, desk_name
    )
    if number_of_seats < people:
        return f"You requested desks for {people} people, but only {number_of_seats} are available."

    excluded_seats: list[str] = []
    for i in range(people):
        seat_id = get_seat_id(
            token,
            building_id,
            floor_id,
            date,
            desk_name,
            excluded_seats=excluded_seats,
        )
        if not seat_id:
            return f"While booking, someone else booked a desk and there are not enough desks. I booked {i} desks."
        create_desk_reservation(token, company_id, user_id, seat_id, date)
        excluded_seats.append(seat_id)
    return f"Desk(s) booked for {people} people on {date}."


# JOAN API functions
def get_token(client_id: str, client_secret: str) -> str:
    response = httpx.post(
        "https://portal.getjoan.com/api/token/",
        data={"grant_type": "client_credentials", "scope": "read write"},
        auth=(client_id, client_secret),
    ).json()
    if not response:
        raise ValueError("Invalid client_id or client_secret")
    token = response.get("access_token")
    if not isinstance(token, str):
        raise ValueError("Invalid client_id or client_secret")
    return token


def get_user_id(
    token: str, company_id: str, email: str
) -> tuple[str | None, bool]:
    response = httpx.get(
        f"https://portal.getjoan.com/api/2.0/desk/company/{company_id}/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    for user in response.json():
        if user["email"] == email:
            user_id = user["id"]
            is_admin = user["groups"] != ["portal_user"]
            return (user_id, is_admin)
    return None, False


class JoanLocation(TypedDict):
    building_id: str
    floor_id: str
    floor: int
    city: str


def get_locations(token: str, company_id: str) -> list[JoanLocation]:
    response = httpx.get(
        f"https://portal.getjoan.com/api/2.0/desk/company/{company_id}/desk",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    buildings: list[JoanLocation] = []
    # Used [:-1] to exclude G Cloud building
    for building in response["locations"][:-1]:
        for floor in building["maps"]:
            try:
                level = int(re.search(r"\d+", floor["name"]).group())  # type: ignore
            except AttributeError:
                level = 0
            building_data = JoanLocation(
                building_id=building["id"],
                floor_id=floor["id"],
                floor=level,
                # Weird data quality for the city name
                city=building["address"]["street"].lower(),
            )
            buildings.append(building_data)
    return buildings


def get_location(
    token: str,
    company_id: str,
    city: str | None = None,
    floor: int | None = None,
) -> tuple[str, str]:
    all_locations = get_locations(token, company_id)
    if city:
        city = city.lower()

    for location in all_locations:
        if city and city in location["city"]:
            if floor is not None and floor != location["floor"]:
                continue
            else:
                return location["building_id"], location["floor_id"]
    return all_locations[0]["building_id"], all_locations[0]["floor_id"]


def create_desk_reservation(
    token: str,
    company_id: str,
    user_id: str,
    seat_id: str,
    date: str,
    from_time: str = "09:00",
    to_time: str = "17:00",
) -> None:
    httpx.post(
        f"https://portal.getjoan.com/api/2.0/desk/v2/company/{company_id}/reservation",
        json={
            "date": date,
            "from": from_time,
            "to": to_time,
            "tz": "Europe/Amsterdam",
            "seat_id": seat_id,
            "user_id": user_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return None


def get_number_of_free_seats(
    token: str,
    building_id: str,
    floor_id: str,
    date: str,
    desk_name: str | None = None,
    time_from: str = "09:00",
    time_to: str = "17:00",
) -> int:
    response = httpx.get(
        "https://portal.getjoan.com/api/2.0/portal/desks/",
        params={
            "date": date,
            "from": time_from,
            "to": time_to,
            "tz": "Europe/Amsterdam",
            "building_id": building_id,
            "floor_id": floor_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    results = response["results"]

    # Only count the desks that match the desk_name
    if desk_name:
        desk_name = desk_name.lower()
        results = [
            desk for desk in results if desk_name in desk["name"].lower()
        ]
    return len(results)


class JoanSeat(TypedDict):
    id: str
    name: str


def get_seat_id(
    token: str,
    building_id: str,
    floor_id: str,
    date: str,
    desk_name: str | None = None,
    time_from: str = "09:00",
    time_to: str = "17:00",
    excluded_seats: list[str] | None = None,
) -> str | None:
    response = httpx.get(
        "https://portal.getjoan.com/api/2.0/portal/desks/",
        params={
            "date": date,
            "from": time_from,
            "to": time_to,
            "tz": "Europe/Amsterdam",
            "building_id": building_id,
            "floor_id": floor_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    if not response:
        return None
    results: list[JoanSeat] | None = response.get("results")

    # No available desks
    if not isinstance(results, list) or not results:
        return None

    # If desk_name is not provided, get the first available desk
    if not desk_name:
        if excluded_seats:
            for desk in results:
                if desk["id"] not in excluded_seats:
                    return desk["id"]
        return results[0]["id"]

    # If desk_name is provided, get the first available desk that matches
    desk_name = desk_name.lower()
    for desk in results:
        if desk_name in desk["name"].lower():
            if excluded_seats:
                desk_id = desk["id"]
                if desk_id not in excluded_seats:
                    return desk_id
            else:
                return desk["id"]

    # If no desk_name was matched, then get the first available desk
    if excluded_seats:
        for desk in results:
            if desk["id"] not in excluded_seats:
                return desk["id"]
    return results[0]["id"]


def get_desk_reservation(
    token: str,
    company_id: str,
    user_id: str,
    date: str,
) -> list[str] | None:
    response = httpx.get(
        f"https://portal.getjoan.com/api/2.0/desk/v2/company/{company_id}/reservation",
        params={
            "from": f"{date} 00:00:00",
            "to": f"{date} 23:59:59",
            "tz": "Europe/Amsterdam",
            "user_id": user_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    if response:
        return [desk["id"] for desk in response]
    return None
