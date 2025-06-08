from collections import defaultdict
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, TypedDict

import httpx
from pytz import timezone

from mcpbot.shared.init import config
from mcpbot.server.tools.joan_api.common.config import (
    Desk,
    TIMESLOT_BY_ID,
    Timeslot,
    Timeslots,
    TIMEZONE,
)


class Reservation(StrEnum):
    FREE = "free"
    FULLY_BOOKED = "fully_booked"
    RESERVATION_FOUND = "reservation_found"
    RESERVATION_NOT_FOUND = "reservation_not_found"


class JoanDesk(TypedDict):
    id: str
    name: str


class PeopleInOffice(TypedDict):
    full_name: str
    place: str


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

    def get_admin_status(self, email: str) -> bool | None:
        """Get admin status for user or null if the user is not found."""
        response = self.send_request(
            method="GET",
            url="/portal/users/",
            params={"limit": 1000},
        )
        for user in response["results"]:
            if user["email"] == email:
                is_admin = user["groups"] != ["portal_user"]
                return is_admin
        return None

    def get_available_desks(
        self,
        building_id: str,
        floor_id: str,
        date: str,
        desk_type: Desk | None = None,
        desk_number_id: int | None = None,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> list[JoanDesk]:
        """Get the number of free desks for a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/desks/schedule/",
            params={
                "building_id": building_id,
                "floor_id": floor_id,
                "start": zone_to_utc_timestamp(f"{date}T{time_from}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{time_to}:00.00Z"),
                "tz": TIMEZONE,
                "limit": 1000,
            },
        )
        free_seats = [
            JoanDesk(id=desk["id"], name=desk["name"])
            for desk in response["results"]
            if not desk.get("schedule")
        ]

        # If no desk type is given, return all free seats
        if desk_type is None:
            return free_seats
        # If desk type is given, filter the free seats based on the desk type
        elif desk_type in [
            Desk.SINGLE_MONITOR,
            Desk.SINGLE_MONITOR_XL,
            Desk.DUAL_MONITOR,
            Desk.ULTRA_WIDE_MONITOR,
        ]:
            matched_seats = [
                desk for desk in free_seats if desk["name"].endswith(desk_type)
            ]
        else:
            matched_seats = [
                desk
                for desk in free_seats
                if desk["name"].startswith(desk_type)
            ]

        # If no desk number ID is given, return all matched seats
        if not desk_number_id:
            return matched_seats
        # If desk number ID is given, filter the matched seats
        else:
            return [
                desk
                for desk in matched_seats
                if desk["name"].endswith(f"#{desk_number_id}")
                or f"#{desk_number_id} " in desk["name"]
            ]

    def get_own_desks(
        self,
        email: str,
        date: str,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> list[str]:
        """Get the number of free desks for a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/desks/schedule/",
            params={
                "start": zone_to_utc_timestamp(f"{date}T{time_from}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{time_to}:00.00Z"),
                "tz": TIMEZONE,
                "limit": 1000,
            },
        )

        reservation_ids: list[str] = []
        for desk in response["results"]:
            if desk.get("schedule"):
                for reservation in desk["schedule"][0]["reservations"]:
                    if reservation["user"]["email"] == email:
                        print("Id:", reservation["id"], "Name:", desk["name"])
                        reservation_ids.append(reservation["id"])
        return reservation_ids

    def reserve_desk(
        self,
        email: str,
        desk_id: str,
        date: str,
        timeslot: Timeslot,
    ) -> None:
        """Create a desk reservation for a user."""
        time_from = timeslot.time_from
        time_to = timeslot.time_to
        self.send_request(
            method="POST",
            url="/portal/desks/reservations/",
            params={
                "desk_id": desk_id,
                "timeslot_id": timeslot.id,
                "start": zone_to_utc_timestamp(f"{date}T{time_from}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{time_to}:00.00Z"),
                "tz": TIMEZONE,
                "user_email": email,
            },
        )
        return None

    def delete_desk(
        self,
        email: str,
        date: str,
    ) -> str | None:
        """Delete all desk reservations for a user on a given date."""
        reservation_ids = self.get_own_desks(email, date)
        if not reservation_ids:
            return None

        for reservation_id in reservation_ids:
            self.send_request(
                method="DELETE",
                url=f"/portal/desks/reservations/{reservation_id}/",
                params={"user_email": email},
                return_json=False,
            )
        return "Reservations deleted"

    def get_people_in_the_office(
        self,
        date: str,
        name: str | None = None,
        building_id: str | None = None,
    ) -> list[str]:
        """Get the names of people who have a desk reservation on a given date.

        If a specific name is provided, only return people whose names
        match the provided name (case-insensitive).
        """
        name = name.lower() if name else name

        response = self.send_request(
            method="GET",
            url="/portal/desks/reservations/",
            params={
                "start": zone_to_utc_timestamp(f"{date}T00:00:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T23:59:59.00Z"),
                "limit": 10000,
            },
        )

        # people_by_building is a nested dictionary in the format:
        # {
        #     "floor name": {
        #         "morning": [list of names],
        #         "afternoon": [list of names],
        #         "all_day": [list of names]
        #     },
        #     ...
        # }
        people_in_office: dict[dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for reservation in response["results"]:
            # Get the user's full name
            user: dict[str, str] = reservation["user"]
            full_name = f"{user['first_name']} {user['last_name']}"

            if name and (name not in full_name.lower()):
                continue
            if building_id and (building_id != reservation["building"]["id"]):
                continue

            # Timeslot ID can be None
            timeslot_id = (
                reservation["timeslot_id"] or Timeslots.ALL_DAY.value.id
            )

            # Append the value in the nested dictionary
            (
                people_in_office[reservation["floor"]["name"]][
                    TIMESLOT_BY_ID[timeslot_id]
                ]
            ).append(full_name)
        return people_in_office

    def get_available_parkings(
        self,
        email: str,
        date: str,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> list[str] | Reservation:
        """Get an available parking spot for a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/assets/schedule/",
            params={
                "start": zone_to_utc_timestamp(f"{date}T{time_from}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{time_to}:00.00Z"),
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
        return free_spots

    def get_own_parking(
        self,
        email: str,
        date: str,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> str | Reservation:
        """Get the parking spot ID for a user on a given date and time range."""
        response = self.send_request(
            method="GET",
            url="/portal/assets/reservations/",
            params={
                "start": zone_to_utc_timestamp(f"{date}T{time_from}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{time_to}:00.00Z"),
                "tz": TIMEZONE,
            },
        )

        for reservation in response["results"]:
            if reservation["user"]["email"] == email:
                return reservation["id"]  # type: ignore[no-any-return]
        return Reservation.RESERVATION_NOT_FOUND

    def reserve_parking(
        self,
        email: str,
        parking_id: str,
        date: str,
        time_from: str = "09:00",
        time_to: str = "17:00",
    ) -> None:
        """Book a parking spot for a given date and time range."""
        self.send_request(
            method="POST",
            url="/portal/assets/reservations/",
            params={
                "asset_id": parking_id,
                "user_email": email,
                "start": zone_to_utc_timestamp(f"{date}T{time_from}:00.00Z"),
                "end": zone_to_utc_timestamp(f"{date}T{time_to}:00.00Z"),
                "tz": TIMEZONE,
            },
        )

    def delete_parking(self, email: str, reservation_id: str) -> None:
        """Delete a parking reservation by its ID."""
        self.send_request(
            method="DELETE",
            url=f"/portal/assets/reservations/{reservation_id}/",
            params={"user_email": email},
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


if __name__ == "__main__":
    # Example usage
    api = JoanAPI()
    print(api.get_admin_status("georgios.gkenios@devoteam.com"))
