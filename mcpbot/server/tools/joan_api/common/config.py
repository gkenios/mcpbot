from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Literal


TIMEZONE = "Europe/Amsterdam"


# Desks (Values are repeated for readability of the typehints in the MCP server)
DeskType = Literal[
    "Single Monitor",
    "Single Monitor XL",
    "Dual Monitor",
    "Ultra Wide Monitor",
    "Table",
    "High table",
    "Bar table",
    "Lounge",
]


class Desk(StrEnum):
    SINGLE_MONITOR = "Single Monitor"
    SINGLE_MONITOR_XL = "Single Monitor XL"
    DUAL_MONITOR = "Dual Monitor"
    ULTRA_WIDE_MONITOR = "Ultra Wide Monitor"
    TABLE = "Table"
    HIGH_TABLE = "High table"
    BAR_TABLE = "Bar table"
    LOUNGE = "Lounge"


# Timeslots
TimeslotType = Literal["all_day", "morning", "afternoon"]


@dataclass
class Timeslot:
    time_from: str
    time_to: str
    id: str


class Timeslots(Enum):
    ALL_DAY = Timeslot("09:00", "17:00", "bd51b541-3e74-4532-949d-2348dbb509e4")
    MORNING = Timeslot("09:00", "13:00", "171c74cf-c6dc-4931-b3bc-dff0644fb242")
    AFTERNOON = Timeslot(
        "13:00", "17:00", "9970914c-fc3f-4969-b28d-e5b28badef74"
    )


TIMESLOT_BY_ID = {
    Timeslots.ALL_DAY.value.id: Timeslots.ALL_DAY.name.capitalize(),
    Timeslots.MORNING.value.id: Timeslots.MORNING.name.capitalize(),
    Timeslots.AFTERNOON.value.id: Timeslots.AFTERNOON.name.capitalize(),
}


# Locations
CityType = Literal["amsterdam", "the_hague"]
BuildingType = Literal["keyness", "vinoly_g_cloud", "de_rode_olifant"]


class City(StrEnum):
    AMSTERDAM = "amsterdam"
    THE_HAGUE = "the_hague"


class Building(StrEnum):
    KEYNESS = "keyness"
    VINOLY_G_CLOUD = "vinoly_g_cloud"
    DE_RODE_OLIFANT = "de_rode_olifant"


LOCATIONS = {
    City.AMSTERDAM: {
        "default_building": Building.KEYNESS,
        "buildings": {
            Building.KEYNESS: {
                "name": "Keynes Building",
                "building_id": "1a3ed651-601c-4f53-b137-12af88f03df7",
                "default_floor": 3,
                "floors": {
                    0: {
                        "floor_id": "a5b8c4e5-3649-45f6-bb1f-708a13db3245",
                        "default_desk_type": Desk.ULTRA_WIDE_MONITOR,
                    },
                    3: {
                        "floor_id": "b32795b0-cf99-48de-a59e-2b4f28e4d866",
                        "default_desk_type": Desk.DUAL_MONITOR,
                    },
                },
            },
            Building.VINOLY_G_CLOUD: {
                "name": "Viñoly Building (G Cloud)",
                "building_id": "b4a0d73a-aea7-46c3-8961-73ba21e3cac0",
                "default_floor": 3,
                "floors": {
                    3: {
                        "floor_id": "f007f399-db40-444f-9cce-5a44a10013c8",
                        "default_desk_type": "",
                    },
                },
            },
        },
    },
    City.THE_HAGUE: {
        "default_building": Building.DE_RODE_OLIFANT,
        "buildings": {
            Building.DE_RODE_OLIFANT: {
                "name": "Spaces De Rode Olifant",
                "building_id": "aa0c282c-a6f3-452c-9de9-5bea79e9a95f",
                "default_floor": 1,
                "floors": {
                    1: {
                        "floor_id": "27f0866a-b8aa-4408-965c-d6f92e3d8f8c",
                        "default_desk_type": "Desk",
                    },
                },
            },
        },
    },
}
