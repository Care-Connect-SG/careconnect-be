from bson import ObjectId

class PyObjectId(str):
    """Custom validator to handle MongoDB's ObjectId."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        return {"type": "string"}

class BaseConfig:
    """Pydantic configuration for MongoDB serialization."""
    populate_by_name = True
    json_encoders = {ObjectId: str}
