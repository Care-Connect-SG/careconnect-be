import os
from dotenv import load_dotenv

load_dotenv()

FE_URL = os.getenv("FE_URL")
MONGO_URI = os.getenv("MONGO_URI")
