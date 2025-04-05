import asyncio
import re
import os
import ssl
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

import certifi
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from utils.config import MONGO_URI, TELEGRAM_TOKEN

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set SSL certificate environment variable
os.environ["SSL_CERT_FILE"] = certifi.where()

# Database connection
mongo_client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
db = mongo_client["caregiver"]
resident_db = mongo_client["resident"]
resident_collection = resident_db["resident_info"]

# Helper function to truncate responses to avoid Telegram message length limit
def truncate_response(text, max_length=4000):
    """Truncate long messages to avoid Telegram message size limits"""
    if len(text) <= max_length:
        return text
    
    # Basic truncation method
    truncated_text = text[:max_length-100]
    # Try to find a reasonable place to break
    last_newline = truncated_text.rfind('\n')
    if last_newline > max_length - 200:
        truncated_text = truncated_text[:last_newline]
    
    return truncated_text + "\n\n...(message truncated due to length)"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "Welcome to CareConnect Bot! 🤖\n\n"
            "I can help you query information about residents, tasks, and activities.\n\n"
            "Try asking me things like:\n"
            "• What tasks are due today?\n"
            "• What happened to [resident name] in the last 3 hours?\n"
            "• Show me overdue tasks\n"
            "• List activities scheduled for tomorrow\n\n"
            "Type /help for more information on what I can do."
        )
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text("I encountered an error. Please try again later.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        help_text = (
            "🤖 *CareConnect Bot Help* 🤖\n\n"
            "*Available Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/residents - List all residents\n"
            "/tasks - List today's tasks\n\n"
            
            "*Natural Language Queries:*\n"
            "You can ask me about tasks, residents, and activities in natural language. For example:\n\n"
            
            "*Tasks:*\n"
            "• What tasks are due today?\n"
            "• Show me all high priority tasks\n"
            "• Any overdue tasks?\n"
            "• List pending tasks for [nurse name]\n\n"
            
            "*Residents:*\n"
            "• How is [resident name] doing?\n"
            "• What happened to [resident name] today?\n"
            "• Show tasks for [resident name]\n\n"
            
            "*Activities:*\n"
            "• What activities are scheduled today?\n"
            "• Show me activities for this week\n"
            "• Any activities in [location]?\n\n"
            
            "*Time Ranges:*\n"
            "• last 3 hours\n"
            "• yesterday\n"
            "• this week\n"
            "• tomorrow\n"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in help command: {str(e)}")
        await update.message.reply_text("I encountered an error displaying help. Please try again later.")


async def list_residents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        residents_cursor = resident_collection.find({}, {"full_name": 1, "room_number": 1})
        residents = await residents_cursor.to_list(length=50)

        if not residents:
            await update.message.reply_text("No residents found.")
            return

        response = "👵👴 *Resident List:*\n\n"
        for idx, resident in enumerate(residents, start=1):
            name = resident.get("full_name", "Unnamed")
            room = resident.get("room_number", "No room")
            response += f"{idx}. {name} (Room: {room})\n"

        # Truncate long messages
        response = truncate_response(response)
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error listing residents: {str(e)}")
        await update.message.reply_text(f"Sorry, I encountered an error when listing residents. Please try again later.")


async def get_tasks_by_filter(filters: Dict[str, Any] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Helper function to get tasks by filter"""
    try:
        query = filters or {}
        tasks = await db.tasks.find(query).sort("start_date", -1).limit(limit).to_list(length=limit)
        
        # Enrich tasks with names
        for task in tasks:
            if "assigned_to" in task and task["assigned_to"]:
                user = await db.users.find_one({"_id": task["assigned_to"]}, {"full_name": 1})
                if user:
                    task["assigned_to_name"] = user.get("full_name", "Unknown")
            
            if "assigned_for" in task and task["assigned_for"]:
                try:
                    resident = await resident_collection.find_one(
                        {"_id": ObjectId(task["assigned_for"])}, {"full_name": 1}
                    )
                    if resident:
                        task["assigned_for_name"] = resident.get("full_name", "Unknown")
                except:
                    task["assigned_for_name"] = "Unknown"
        
        return tasks
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        raise Exception(f"Error fetching tasks: {str(e)}")


async def get_activities_by_filter(filters: Dict[str, Any] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Helper function to get activities by filter"""
    try:
        query = filters or {}
        activities = await db.activities.find(query).sort("start_time", -1).limit(limit).to_list(length=limit)
        
        # Enrich activities with creator names
        for activity in activities:
            if "created_by" in activity and activity["created_by"]:
                try:
                    user = await db.users.find_one({"_id": ObjectId(activity["created_by"])}, {"full_name": 1})
                    if user:
                        activity["created_by_name"] = user.get("full_name", "Unknown")
                except:
                    activity["created_by_name"] = "Unknown"
        
        return activities
    except Exception as e:
        logger.error(f"Error getting activities: {str(e)}")
        raise Exception(f"Error fetching activities: {str(e)}")


async def get_resident_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Helper function to find a resident by name (partial match)"""
    try:
        # Clean up the name by removing extra spaces
        name = ' '.join(name.split())
        
        # Try exact match first (case insensitive)
        query = {"full_name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
        resident = await resident_collection.find_one(query)
        
        if resident:
            logger.info(f"Found resident with exact match: {resident.get('full_name')}")
            return resident
        
        # Try partial match with word boundaries
        query = {"full_name": {"$regex": f"\\b{re.escape(name)}\\b", "$options": "i"}}
        resident = await resident_collection.find_one(query)
        
        if resident:
            logger.info(f"Found resident with word boundary match: {resident.get('full_name')}")
            return resident
        
        # Try more flexible partial match
        query = {"full_name": {"$regex": re.escape(name), "$options": "i"}}
        resident = await resident_collection.find_one(query)
        
        if resident:
            logger.info(f"Found resident with partial match: {resident.get('full_name')}")
            return resident
        
        # Try individual name parts (first name, last name)
        name_parts = name.split()
        if len(name_parts) > 1:
            # Try matching just the first name
            first_name = name_parts[0]
            query = {"full_name": {"$regex": f"^{re.escape(first_name)}\\b", "$options": "i"}}
            resident = await resident_collection.find_one(query)
            
            if resident:
                logger.info(f"Found resident with first name match: {resident.get('full_name')}")
                return resident
            
            # Try matching just the last name
            last_name = name_parts[-1]
            query = {"full_name": {"$regex": f"\\b{re.escape(last_name)}$", "$options": "i"}}
            resident = await resident_collection.find_one(query)
            
            if resident:
                logger.info(f"Found resident with last name match: {resident.get('full_name')}")
                return resident
        
        # If nothing found, try a fuzzy search by listing possible residents
        residents = await resident_collection.find({}).limit(10).to_list(length=10)
        logger.info(f"No match found for '{name}'. Available residents: {[r.get('full_name') for r in residents]}")
        
        return None
    except Exception as e:
        logger.error(f"Error finding resident: {str(e)}")
        return None


async def parse_query_with_ai(message_text: str) -> Tuple[str, Dict[str, Any]]:
    """Use AI to parse the query and extract intent and parameters"""
    try:
        # Define a system prompt for better query understanding
        system_prompt = """
        You are a healthcare assistant bot that helps nurses and caregivers query a database.
        Extract the following information from the user's query:
        1. INTENT: One of [task_query, activity_query, resident_query, general_question]
        2. TIME_RANGE: Extract time information (today, yesterday, last X hours, this week, tomorrow, upcoming, etc.)
        3. FILTERS: Extract any filters like status, priority, location, category, resident name, etc.
        
        Format your response as a JSON object with these keys. Do not include explanations outside the JSON.
        """
        
        # Create a mock AI response for now - in a real implementation this would call OpenAI API
        intent = "general_question"
        time_range = {}
        filters = {}
        
        # Check for task-related queries
        if re.search(r'\btasks?\b', message_text, re.IGNORECASE):
            intent = "task_query"
            
            # Time-based filters
            if re.search(r'\btoday\b', message_text, re.IGNORECASE):
                now = datetime.now(timezone.utc)
                time_range = {
                    "start_time": now.replace(hour=0, minute=0, second=0, microsecond=0),
                    "end_time": now.replace(hour=23, minute=59, second=59, microsecond=999999)
                }
            elif re.search(r'\btomorrow\b', message_text, re.IGNORECASE):
                now = datetime.now(timezone.utc)
                time_range = {
                    "start_time": (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                    "end_time": (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
                }
            elif re.search(r'\byesterday\b', message_text, re.IGNORECASE):
                now = datetime.now(timezone.utc)
                time_range = {
                    "start_time": (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                    "end_time": (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
                }
            elif re.search(r'\bweek\b', message_text, re.IGNORECASE):
                now = datetime.now(timezone.utc)
                start_of_week = now - timedelta(days=now.weekday())
                time_range = {
                    "start_time": start_of_week.replace(hour=0, minute=0, second=0, microsecond=0),
                    "end_time": now
                }
            elif re.search(r'last (\d+) hours?', message_text, re.IGNORECASE):
                match = re.search(r'last (\d+) hours?', message_text, re.IGNORECASE)
                if match:
                    hours = int(match.group(1))
                    now = datetime.now(timezone.utc)
                    time_range = {
                        "start_time": now - timedelta(hours=hours),
                        "end_time": now
                    }
            
            # Status filters
            if re.search(r'\boverdue\b', message_text, re.IGNORECASE):
                filters["status"] = "Overdue"
            elif re.search(r'\bpending\b', message_text, re.IGNORECASE):
                filters["status"] = "Pending"
            elif re.search(r'\bcompleted\b', message_text, re.IGNORECASE):
                filters["status"] = "Completed"
            
            # Priority filters
            if re.search(r'\bhigh priority\b', message_text, re.IGNORECASE):
                filters["priority"] = "High"
            elif re.search(r'\bmedium priority\b', message_text, re.IGNORECASE):
                filters["priority"] = "Medium"
            elif re.search(r'\blow priority\b', message_text, re.IGNORECASE):
                filters["priority"] = "Low"
            
            # Resident filters
            resident_match = re.search(r'for\s+([A-Za-z\s]+?)(?=\sin|\s?$)', message_text, re.IGNORECASE)
            if resident_match:
                filters["resident_name"] = resident_match.group(1).strip()
        
        # Check for activity-related queries
        elif re.search(r'\bactivit(y|ies)\b|\bupcoming\b|\bscheduled\b', message_text, re.IGNORECASE):
            intent = "activity_query"
            
            # Time range similar to tasks
            if re.search(r'\btoday\b', message_text, re.IGNORECASE):
                now = datetime.now(timezone.utc)
                time_range = {
                    "start_time": now.replace(hour=0, minute=0, second=0, microsecond=0),
                    "end_time": now.replace(hour=23, minute=59, second=59, microsecond=999999)
                }
            elif re.search(r'\bupcoming\b|\bscheduled\b', message_text, re.IGNORECASE):
                now = datetime.now(timezone.utc)
                time_range = {
                    "start_time": now,
                    "end_time": now + timedelta(days=7)
                }
            
            # Location filters
            location_match = re.search(r'in\s+([A-Za-z\s]+)(room|hall|area)?', message_text, re.IGNORECASE)
            if location_match:
                filters["location"] = location_match.group(1).strip()
            
            # Category filters
            for category in ["Medication", "Exercise", "Social", "Entertainment", "Education"]:
                if re.search(rf'\b{category}\b', message_text, re.IGNORECASE):
                    filters["category"] = category
                    break
        
        # Check for resident-related queries
        elif re.search(r'(resident|patient)?\s?([A-Za-z\s]+?)(?=\sin the last|\s?$|\s(doing|today))', message_text, re.IGNORECASE):
            intent = "resident_query"
            resident_match = re.search(r'(resident|patient)?\s?([A-Za-z\s]+?)(?=\sin the last|\s?$|\s(doing|today))', message_text, re.IGNORECASE)
            potential_name = resident_match.group(2).strip()
            if len(potential_name) > 3:  # Avoid matching on small words
                filters["resident_name"] = potential_name
            
            # Time range similar to other queries
            if re.search(r'last (\d+) hours?', message_text, re.IGNORECASE):
                match = re.search(r'last (\d+) hours?', message_text, re.IGNORECASE)
                if match:
                    hours = int(match.group(1))
                    now = datetime.now(timezone.utc)
                    time_range = {
                        "start_time": now - timedelta(hours=hours),
                        "end_time": now
                    }
        
        return intent, {"time_range": time_range, "filters": filters}
    
    except Exception as e:
        logger.error(f"Error parsing query with AI: {str(e)}")
        return "general_question", {"time_range": {}, "filters": {}}


async def format_task_response(tasks: List[Dict[str, Any]]) -> str:
    """Format tasks for the response"""
    if not tasks:
        return "No tasks found matching your criteria."
    
    response = f"📋 *Found {len(tasks)} tasks:*\n\n"
    
    for idx, task in enumerate(tasks[:10], start=1):
        title = task.get("task_title", "Untitled Task")
        status = task.get("status", "Unknown")
        priority = task.get("priority", "")
        assigned_to = task.get("assigned_to_name", "Unassigned")
        assigned_for = task.get("assigned_for_name", "Not specified")
        
        start_date = task.get("start_date")
        due_date = task.get("due_date")
        
        date_str = ""
        if start_date:
            date_str = f"{start_date.strftime('%Y-%m-%d %H:%M')}"
        if due_date:
            date_str += f" to {due_date.strftime('%Y-%m-%d %H:%M')}"
        
        response += (
            f"{idx}. *{title}*\n"
            f"   Status: {status} | Priority: {priority}\n"
            f"   For: {assigned_for} | By: {assigned_to}\n"
            f"   Time: {date_str}\n\n"
        )
    
    if len(tasks) > 10:
        response += f"...and {len(tasks) - 10} more tasks (showing first 10 only)."
    
    return response


async def format_activity_response(activities: List[Dict[str, Any]]) -> str:
    """Format activities for the response"""
    if not activities:
        return "No activities found matching your criteria."
    
    response = f"🗓️ *Found {len(activities)} activities:*\n\n"
    
    for idx, activity in enumerate(activities[:10], start=1):
        title = activity.get("title", "Untitled Activity")
        location = activity.get("location", "No location")
        category = activity.get("category", "Uncategorized")
        created_by = activity.get("created_by_name", "Unknown")
        
        start_time = activity.get("start_time")
        end_time = activity.get("end_time")
        
        time_str = ""
        if start_time:
            time_str = f"{start_time.strftime('%Y-%m-%d %H:%M')}"
        if end_time:
            time_str += f" to {end_time.strftime('%Y-%m-%d %H:%M')}"
        
        response += (
            f"{idx}. *{title}*\n"
            f"   Category: {category} | Location: {location}\n"
            f"   Created by: {created_by}\n"
            f"   Time: {time_str}\n\n"
        )
    
    if len(activities) > 10:
        response += f"...and {len(activities) - 10} more activities (showing first 10 only)."
    
    return response


async def format_resident_response(resident: Dict[str, Any], tasks: List[Dict[str, Any]], is_general_query: bool) -> str:
    """Format resident info for the response"""
    if not resident:
        return "Sorry, I couldn't find that resident."
    
    full_name = resident.get("full_name", "Unknown")
    room_number = resident.get("room_number", "Unknown")
    
    response = f"👤 *Resident: {full_name}*\n"
    response += f"Room: {room_number}\n\n"
    
    # General status or specific task list
    if is_general_query:
        response += f"*Recent tasks for {full_name}:*\n\n"
        
        if tasks:
            for idx, task in enumerate(tasks[:5], start=1):
                title = task.get("task_title", "Untitled Task")
                status = task.get("status", "Unknown")
                assigned_to = task.get("assigned_to_name", "Unassigned")
                
                response += (
                    f"{idx}. {title}\n"
                    f"   Status: {status} | Assigned to: {assigned_to}\n"
                )
            
            if len(tasks) > 5:
                response += f"\n...and {len(tasks) - 5} more tasks."
        else:
            response += "No recent tasks found for this resident."
    else:
        # Return detailed task list
        time_range = {}
        # This would come from the AI parser in a real implementation
        
        response += f"*Tasks for {full_name}:*\n\n"
        
        if tasks:
            for idx, task in enumerate(tasks[:10], start=1):
                title = task.get("task_title", "Untitled Task")
                status = task.get("status", "Unknown")
                priority = task.get("priority", "")
                assigned_to = task.get("assigned_to_name", "Unassigned")
                
                start_date = task.get("start_date")
                due_date = task.get("due_date")
                
                date_str = ""
                if start_date:
                    date_str = f"{start_date.strftime('%Y-%m-%d %H:%M')}"
                if due_date:
                    date_str += f" to {due_date.strftime('%Y-%m-%d %H:%M')}"
                
                response += (
                    f"{idx}. *{title}*\n"
                    f"   Status: {status} | Priority: {priority}\n"
                    f"   Assigned to: {assigned_to}\n"
                    f"   Time: {date_str}\n\n"
                )
            
            if len(tasks) > 10:
                response += f"...and {len(tasks) - 10} more tasks (showing first 10 only)."
        else:
            response += "No tasks found for this resident in the specified time period."
    
    return response


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages with enhanced NLP and error handling"""
    try:
        message_text = update.message.text.strip()
        
        # Send typing action to indicate the bot is processing
        await update.message.chat.send_action(action="typing")
        
        # Use AI parsing to determine intent and extract parameters
        intent, params = await parse_query_with_ai(message_text)
        time_range = params.get("time_range", {})
        filters = params.get("filters", {})
        
        # More accurate resident name extraction
        is_resident_query = False
        resident_name = None
        
        # Check for patterns like "How is [name] doing" or "What happened to [name]"
        how_is_pattern = re.match(r'how\s+is\s+([A-Za-z\s]+?)(?:\s+doing)?$', message_text, re.IGNORECASE)
        what_happened_pattern = re.match(r'what\s+happened\s+to\s+([A-Za-z\s]+?)(?:\s+today|\s+yesterday|\s+this\s+week)?$', message_text, re.IGNORECASE)
        
        if how_is_pattern:
            is_resident_query = True
            resident_name = how_is_pattern.group(1).strip()
            intent = "resident_query"
        elif what_happened_pattern:
            is_resident_query = True
            resident_name = what_happened_pattern.group(1).strip()
            intent = "resident_query"
        
        # Handle based on intent
        if intent == "task_query":
            # Prepare MongoDB query
            query_filters = {}
            
            # Time-based filters
            if time_range and "start_time" in time_range and "end_time" in time_range:
                query_filters["start_date"] = {"$gte": time_range["start_time"], "$lte": time_range["end_time"]}
            
            # Status filters
            if filters.get("status"):
                query_filters["status"] = filters["status"]
            
            # Priority filters
            if filters.get("priority"):
                query_filters["priority"] = filters["priority"]
            
            # Resident name filter
            if filters.get("resident_name"):
                resident = await get_resident_by_name(filters["resident_name"])
                if resident:
                    query_filters["assigned_for"] = resident["_id"]
            
            # Get tasks based on filters
            tasks = await get_tasks_by_filter(query_filters)
            
            # Format and send response
            response = await format_task_response(tasks)
            response = truncate_response(response)
            await update.message.reply_text(response, parse_mode="Markdown")
        
        elif intent == "activity_query":
            # Prepare MongoDB query
            query_filters = {}
            
            # Time-based filters
            if time_range and "start_time" in time_range and "end_time" in time_range:
                query_filters["$or"] = [
                    {"start_time": {"$gte": time_range["start_time"], "$lte": time_range["end_time"]}},
                    {"end_time": {"$gte": time_range["start_time"], "$lte": time_range["end_time"]}},
                ]
            
            # Location filters
            if filters.get("location"):
                query_filters["location"] = {"$regex": filters["location"], "$options": "i"}
            
            # Category filters
            if filters.get("category"):
                query_filters["category"] = filters["category"]
            
            # Get activities based on filters
            activities = await get_activities_by_filter(query_filters)
            
            # Format and send response
            response = await format_activity_response(activities)
            response = truncate_response(response)
            await update.message.reply_text(response, parse_mode="Markdown")
        
        elif intent == "resident_query" or is_resident_query:
            # Get resident by name
            resident_name = resident_name or filters.get("resident_name", "")
            if not resident_name:
                await update.message.reply_text("Please specify a resident name.")
                return
            
            logger.info(f"Searching for resident with name: '{resident_name}'")
            resident = await get_resident_by_name(resident_name)
            if not resident:
                await update.message.reply_text(f"Sorry, I couldn't find a resident named '{resident_name}'.")
                return
            
            # Get tasks for this resident
            task_filters = {"assigned_for": resident["_id"]}
            if time_range and "start_time" in time_range and "end_time" in time_range:
                task_filters["start_date"] = {"$gte": time_range["start_time"], "$lte": time_range["end_time"]}
            
            tasks = await get_tasks_by_filter(task_filters, 15)
            
            # Check if looking for general status (how is X doing)
            is_general_query = how_is_pattern is not None
            
            # Format and send response
            response = await format_resident_response(resident, tasks, is_general_query)
            response = truncate_response(response)
            await update.message.reply_text(response, parse_mode="Markdown")
        
        else:
            # General question/fallback
            await update.message.reply_text(
                "I'm not sure how to help with that. You can ask me about tasks, residents, or activities. For example:\n"
                "• What tasks are due today?\n"
                "• How is [resident name] doing?\n"
                "• Show activities for this week\n\n"
                "Type /help for more information."
            )
    
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await update.message.reply_text(
            "I'm sorry, I encountered an error while processing your request. "
            "Please try again or use one of my commands like /tasks or /residents."
        )


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to list today's tasks"""
    try:
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        filters = {"start_date": {"$gte": start_of_day, "$lte": end_of_day}}
        tasks = await get_tasks_by_filter(filters)
        
        response = await format_task_response(tasks)
        response = truncate_response(response)
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        await update.message.reply_text("Sorry, I encountered an error when retrieving tasks. Please try again later.")


def start_bot():
    """Non-async entry point for starting the bot"""
    try:
        # Configure application
        app = (
            Application.builder()
            .token(TELEGRAM_TOKEN)
            .build()
        )
        
        # Register command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("residents", list_residents))
        app.add_handler(CommandHandler("tasks", list_tasks))
        
        # Register message handler for natural language queries
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        print("Bot is polling... 🎯")
        app.run_polling()
    except Exception as e:
        logger.error(f"Fatal error starting bot: {str(e)}")
        print(f"Error starting bot: {str(e)}")


if __name__ == "__main__":
    start_bot()
