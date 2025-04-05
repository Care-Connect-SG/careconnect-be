import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB setup — connect to resident_info under "resident" database
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["resident"]
resident_collection = db["resident_info"]

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! How can I help you today? 🤖")

# /residents command
async def list_residents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    residents_cursor = resident_collection.find({}, {"full_name": 1})
    residents = await residents_cursor.to_list(length=50)  # You can adjust the length

    if not residents:
        await update.message.reply_text("No residents found.")
        return

    response = "👵👴 *Resident List:*\n\n"
    for idx, resident in enumerate(residents, start=1):
        name = resident.get("full_name", "Unnamed")
        response += f"{idx}. {name}\n"

    await update.message.reply_text(response)

# Main bot runner
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("residents", list_residents))

    print("Bot is polling... 🎯")
    await app.run_polling()

# Run bot with nested loop support
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    asyncio.run(main())
