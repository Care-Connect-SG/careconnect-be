from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb+srv://<username>:<password>@<dbname>/"


settings = Settings()