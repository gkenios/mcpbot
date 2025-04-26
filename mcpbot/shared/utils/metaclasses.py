# mypy: ignore-errors
from pydantic import BaseModel, ConfigDict


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ArbitaryTypesModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
