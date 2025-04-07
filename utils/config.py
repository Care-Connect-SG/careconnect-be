import os

import cloudinary
from dotenv import load_dotenv

load_dotenv()

FE_URL = os.getenv("FE_URL")
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_TOKEN = os.getenv("BE_API_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_BOT_TOKEN = os.getenv("ASSISTANT_BOT_TOKEN")
REMINDERS_BOT_TOKEN = os.getenv("REMINDERS_BOT_TOKEN")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)
