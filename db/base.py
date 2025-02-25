from bson import ObjectId

class PyObjectId(str):
    """Custom validator to handle MongoDB's ObjectId."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class BaseConfig:
    """Pydantic configuration for MongoDB serialization."""
    population_by_name = True  # Allows using "_id" instead of "id"
    json_encoders = {ObjectId: str}  # Ensures ObjectId is serialized as a string
    orm_mode = True  # Allows Pydantic to work with ORM models
    use_enum_values = True  # Ensures Enum values are serialized as strings