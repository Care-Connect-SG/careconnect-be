#!/usr/bin/env python3
"""
Script to run the CareConnect Telegram Bot
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from telegram_bot.main import start_bot
    
    if __name__ == "__main__":
        print("Starting CareConnect Telegram Bot...")
        print("Press Ctrl+C to stop the bot")
        
        try:
            start_bot()
        except KeyboardInterrupt:
            print("\nBot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            print(f"Error running bot: {e}")
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    print(f"Error importing modules: {e}") 