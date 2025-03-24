from bson import ObjectId
from typing import Annotated
from pydantic import BeforeValidator, BaseModel, ConfigDict

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(lambda x: str(x))]


class ModelConfig(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={"example": {"_id": "ObjectId"}},
    )
