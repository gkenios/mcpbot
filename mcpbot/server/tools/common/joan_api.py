from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import re
from typing import Any, Literal, TypedDict

import httpx
from pytz import timezone

from mcpbot.shared.init import config


TIMEZONE = "Europe/Amsterdam"


class JoanLocation(TypedDict):
    building_id: str
    floor_id: str
    floor: int
    city: str


class JoanSeat(TypedDict):
    id: str
    name: str


class Reservation(StrEnum):
    FREE = "free"
    FULLY_BOOKED = "fully_booked"
    RESERVATION_FOUND = "reservation_found"
    RESERVATION_NOT_FOUND = "reservation_not_found"


@dataclass
class Timeslot:
    time_from: str
    time_to: str


@dataclass
class JoanTimeslots:
    morning: Timeslot
    afternoon: Timeslot
    all_day: Timeslot


class JoanAPI:
    def __init__(self) -> None:
        self.base_url = "https://portal.getjoan.com/api"
        self.api_version = "2.0"
        self.company_id = config.secrets["joan_company_id"]
        self.token = self.get_token(
            config.secrets["joan_client_id"],
            config.secrets["joan_client_secret"],
        )

    def send_request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        url: str,
        params: dict[str, Any] | None = None,
        return_json: bool = True,
    ) -> Any:
        """Send a request to the Joan API."""
        response = httpx.request(
            method=method,
            url=f"{self.base_url}/{self.api_version}{url}",
            headers={"Authorization": f"Bearer {self.token}"},
            params=params if method == "GET" else None,
            json=params if method != "GET" else None,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            print(response.text)
            raise error
        if return_json:
            return response.json()

    def get_token(self, client_id: str, client_secret: str) -> str:
        """Get the access token for the Joan API using client credentials."""
        response = httpx.post(
            f"{self.base_url}/token/",
            data={"grant_type": "client_credentials", "scope": "read write"},
            auth=(client_id, client_secret),
        ).json()
        if not response:
            raise ValueError("Invalid client_id or client_secret")
        token = response.get("access_token")
        if not isinstance(token, str):
            raise ValueError("Invalid client_id or client_secret")
        return token

    def get_user_id(self, email: str) -> tuple[str | None, bool]:
        """Get the user ID and admin status for a given email in a company."""
        response = self.send_request(
            method="GET",
            url=f"/desk/company/{self.company_id}/users",
        )
        for user in response:
            if user["email"] == email:
                user_id = user["id"]
                is_admin = user["groups"] != ["portal_user"]
                return (user_id, is_admin)
        return None, False

    def get_locations(self) -> list[JoanLocation]:
        """Get all locations (buildings and floors) for a given company."""
        response = self.send_request(
            method="GET",
            url=f"/desk/company/{self.company_id}/desk",
        )

        buildings: list[JoanLocation] = []
        for building in response["locations"]:
            for floor in building["maps"]:
                try:
                    level = int(re.search(r"\d+", floor["name"]).group())  # type: ignore[union-attr]
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

        # Workaround to avoid the G Cloud building. It is put last in the list
        buildings.sort(key=lambda x: x["building_id"])
        return buildings

    def get_location(
        self,
        city: str | None = None,
        floor: int | None = None,
    ) -> tuple[str, str]:
        """Get the building and floor IDs for a given city and floor."""
        all_locations = self.get_locations()
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
        self,
        email: str,
        seat_id: str,
        date: str,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> None:
        """Create a desk reservation for a user."""
        self.send_request(
            method="POST",
            url=f"/desk/v2/company/{self.company_id}/reservation",
            params={
                "date": date,
                "from": time_from,
                "to": time_to,
                "tz": TIMEZONE,
                "seat_id": seat_id,
                "user_email": email,
            },
        )
        return None

    def get_number_of_free_seats(
        self,
        building_id: str,
        floor_id: str,
        date: str,
        desk_name: str | None = None,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> int:
        """Get the number of free desks for a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/desks/",
            params={
                "date": date,
                "from": time_from,
                "to": time_to,
                "tz": TIMEZONE,
                "building_id": building_id,
                "floor_id": floor_id,
            },
        )
        results = response["results"]

        # Only count the desks that match the desk_name
        if desk_name:
            desk_name = desk_name.lower()
            results = [
                desk for desk in results if desk_name in desk["name"].lower()
            ]
        return len(results)

    def get_seat_id(
        self,
        building_id: str,
        floor_id: str,
        date: str,
        desk_name: str | None = None,
        time_from: str = "09:00",
        time_to: str = "17:00",
        excluded_seats: list[str] | None = None,
    ) -> str | None:
        """Get the first available desk ID for a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/desks/",
            params={
                "date": date,
                "from": time_from,
                "to": time_to,
                "tz": TIMEZONE,
                "building_id": building_id,
                "floor_id": floor_id,
            },
        )
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
        self,
        user_id: str,
        date: str,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> list[str] | None:
        """Get the IDs of reservations within the given date and time range."""
        hour_from = int(time_from.split(":", 1)[0])
        hour_to = int(time_to.split(":", 1)[0])

        response = self.send_request(
            method="GET",
            url=f"/desk/v2/company/{self.company_id}/reservation",
            params={
                "from": f"{date} {time_from}:00",
                "to": f"{date} {time_to}:00",
                "tz": TIMEZONE,
                "user_id": user_id,
            },
        )
        response = [
            element for element in response if element["user"]["id"] == user_id
        ]
        if response:
            ids = []
            for reservation in response:
                reservation_hour_from = int(
                    reservation["from"].split(":", 1)[0]
                )
                reservation_hour_to = int(reservation["to"].split(":", 1)[0])

                if not (
                    hour_from >= reservation_hour_to
                    or hour_to <= reservation_hour_from
                ):
                    ids.append(reservation["id"])
            return ids
        return None

    def get_desk_reservation_by_day(
        self,
        user_id: str,
        date: str,
    ) -> list[str] | None:
        """Get the IDs of reservations for a specific day."""
        response = self.send_request(
            method="GET",
            url=f"/desk/v2/company/{self.company_id}/reservation",
            params={
                "from": f"{date} 00:00:00",
                "to": f"{date} 23:59:59",
                "tz": TIMEZONE,
                "user_id": user_id,
            },
        )
        response = [
            element for element in response if element["user"]["id"] == user_id
        ]
        if response:
            return [desk["id"] for desk in response]
        return None

    def get_people_in_the_office(
        self,
        date: str,
        name: str | None = None,
    ) -> list[str]:
        """Get the names of people who have a desk reservation on a given date.

        If a specific name is provided, only return people whose names
        match the provided name (case-insensitive).
        """
        response = self.send_request(
            method="GET",
            url=f"/desk/v2/company/{self.company_id}/reservation",
            params={
                "from": f"{date} 00:00:00",
                "to": f"{date} 23:59:59",
                "tz": TIMEZONE,
            },
        )
        people = [
            f"{element['user']['first_name']} {element['user']['last_name']}"
            for element in response
        ]
        # If name is provided, filter to matche it
        if name:
            lower_name = name.lower()
            people = [
                person for person in people if lower_name in person.lower()
            ]
        return people

    def delete_desk_reservation(
        self,
        user_id: str,
        date: str,
    ) -> str | None:
        """Delete all desk reservations for a user on a given date."""
        reservation_ids = self.get_desk_reservation_by_day(user_id, date)
        if not reservation_ids:
            return None

        for reservation_id in reservation_ids:
            self.send_request(
                method="DELETE",
                url=f"/desk/v2/reservation/{reservation_id}",
                return_json=False,
            )
        return "Reservations deleted"

    def get_free_parking_spot(
        self,
        email: str,
        date: str,
        start_time: str = "09:00",
        end_time: str = "17:00",
    ) -> str | Reservation:
        """Get an available parking spot for a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/assets/schedule/",
            params={
                "start": zone_to_utc_timestamp(f"{date}T{start_time}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{end_time}:00.00Z"),
                "tz": TIMEZONE,
            },
        )

        free_spots: list[str] = []
        for parking_spot in response["results"]:
            booked_spots = parking_spot["schedule"]
            if not booked_spots:
                free_spots.append(parking_spot["id"])
            else:
                for reservation in booked_spots[0]["reservations"]:
                    if reservation["user"]["email"] == email:
                        return Reservation.RESERVATION_FOUND
        if not free_spots:
            return Reservation.FULLY_BOOKED
        return free_spots[0]

    def get_user_parking_spot(
        self,
        email: str,
        date: str,
        start_time: str = "09:00",
        end_time: str = "17:00",
    ) -> str | Reservation:
        """Get the parking spot ID for a user on a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/assets/reservations/",
            params={
                "user_email": email,
                "start": zone_to_utc_timestamp(f"{date}T{start_time}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{end_time}:00.00Z"),
                "tz": TIMEZONE,
            },
        )
        for reservation in response["results"]:
            return reservation["id"]  # type: ignore[no-any-return]
        return Reservation.RESERVATION_NOT_FOUND

    def create_parking_reservation(
        self,
        email: str,
        parking_spot_id: str,
        date: str,
        start_time: str = "09:00",
        end_time: str = "17:00",
    ) -> None:
        """Book a parking spot for a given date and time range."""
        self.send_request(
            method="POST",
            url="/portal/assets/reservations/",
            params={
                "asset_id": parking_spot_id,
                "user_email": email,
                "start": zone_to_utc_timestamp(f"{date}T{start_time}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{end_time}:00.00Z"),
                "tz": TIMEZONE,
            },
        )

    def delete_parking_reservation(self, reservation_id: str) -> None:
        """Delete a parking reservation by its ID."""
        self.send_request(
            method="DELETE",
            url=f"/portal/assets/reservations/{reservation_id}/",
            return_json=False,
        )


def zone_to_utc_timestamp(timestamp: str, time_zone: str = TIMEZONE) -> str:
    """Convert a timestamp from a specific timezone to UTC."""
    naive_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    return (
        timezone(time_zone)
        .localize(naive_dt)
        .astimezone(timezone("UTC"))
        .strftime("%Y-%m-%dT%H:%M:%S.00Z")
    )


JOAN_TIMESLOTS = JoanTimeslots(
    morning=Timeslot(time_from="09:00", time_to="13:00"),
    afternoon=Timeslot(time_from="13:00", time_to="17:00"),
    all_day=Timeslot(time_from="09:00", time_to="17:00"),
)
