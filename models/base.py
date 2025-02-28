from bson import ObjectId
from typing import Annotated
from pydantic import BeforeValidator, BaseModel, ConfigDict

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class ModelConfig(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )
