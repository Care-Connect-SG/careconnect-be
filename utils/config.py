import os
from dotenv import load_dotenv

load_dotenv()

FE_URL = os.getenv("FE_URL")
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_TOKEN = os.getenv("BE_API_SECRET")
