from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from utils.config import REMINDERS_BOT_TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! How can I help you today? 🤖")


async def start_reminders_bot():
    app = Application.builder().token(REMINDERS_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Bot is polling... 🎯")
    await app.run_polling()
