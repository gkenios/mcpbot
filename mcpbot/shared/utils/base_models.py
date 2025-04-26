from pydantic import BaseModel, ConfigDict


class ArbitaryTypesModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
