"""
AI-driven task suggestion service for CareConnect.
This module uses OpenAI to generate task suggestions based on resident data.
"""

import json
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import Optional
import httpx

from models.task import TaskCreate, TaskStatus, TaskPriority, TaskCategory
from utils.config import OPENAI_API_KEY
from openai import AsyncOpenAI

# Create a custom HTTPX client with SSL verification disabled
http_client = httpx.AsyncClient(verify=False)
client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    http_client=http_client
)

async def get_ai_task_suggestion(
    db, resident_id: str, current_user: dict
) -> Optional[TaskCreate]:
    """
    Generate an AI task suggestion for a resident using GPT-4.
    
    Args:
        db: MongoDB database connection
        resident_id: ID of the resident to create a task for
        current_user: Current user information
        
    Returns:
        Optional[TaskCreate]: A task object with AI-generated suggestions, or None if generation fails
    """
    try:
        # Get resident information
        resident_db = db.client.get_database("resident")
        resident = await resident_db.residents.find_one({"_id": ObjectId(resident_id)})
        resident_name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}" if resident else "Unknown Resident"
        
        # Get resident's past tasks (most recent 5 completed tasks)
        past_tasks = await db.tasks.find({
            "resident": ObjectId(resident_id),
            "status": TaskStatus.COMPLETED
        }).sort("created_at", -1).limit(5).to_list(length=5)
        
        # Format past tasks for context
        tasks_info = "\n".join([
            f"- {task.get('task_title', 'Unknown Task')}: {task.get('task_details', 'No details')} "
            f"(Category: {task.get('category', 'Unknown')}, Priority: {task.get('priority', 'Unknown')})"
            for task in past_tasks
        ])
        
        if not tasks_info:
            tasks_info = "No previous tasks found for this resident."
        
        # Get medical history if available
        medical_info = "No medical history available."
        medical_records = await resident_db.medical_history.find({
            "resident_id": ObjectId(resident_id)
        }).sort("created_at", -1).limit(3).to_list(length=3)
        
        if medical_records:
            medical_info = "\n".join([
                f"- Condition: {record.get('condition', 'Unknown')}, Risk Level: {record.get('risk_level', 'Unknown')}"
                for record in medical_records
            ])
        
        # Get available nurses for scheduling
        nurses = await db.users.find({"role": "Nurse"}).to_list(length=None)
        nurse_info = "\n".join([
            f"- {nurse.get('first_name', '')} {nurse.get('last_name', '')}"
            for nurse in nurses
        ])

        # Create the prompt for GPT
        prompt = f"""As a healthcare assistant AI, suggest a unique and specific care task for the resident based on the following information:

Resident: {resident_name}

Past Tasks:
{tasks_info}

Medical History:
{medical_info}

Available Nurses:
{nurse_info}

Current Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}

Generate a creative and unique task that is different from the past tasks but still relevant to the resident's needs.
Be specific and detailed in both the title and description.

Provide a task suggestion in this exact JSON format:
{{
    "task_title": "Clear, specific, and unique title",
    "task_details": "Detailed and specific instructions with clear steps",
    "priority": "HIGH/MEDIUM/LOW",
    "category": "MEALS/MEDICATION/THERAPY/OUTING",
    "is_urgent": true/false,
    "reasoning": "Why this task is important and how it differs from past tasks"
}}

Ensure the response is ONLY valid JSON with no extra text."""

        # Call GPT-4 with higher temperature for more variety
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative healthcare assistant AI that generates unique and varied care tasks. Avoid repetitive suggestions and ensure each task is specific to the current situation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,  # Increased temperature for more variety
            max_tokens=500,
            presence_penalty=0.6,  # Add presence penalty to reduce repetition
            frequency_penalty=0.6  # Add frequency penalty to encourage unique words
        )

        # Extract and parse the response
        suggestion_text = response.choices[0].message.content.strip()
        
        # Clean up response if it contains markdown
        if suggestion_text.startswith("```json"):
            suggestion_text = suggestion_text.replace("```json", "", 1)
            if suggestion_text.endswith("```"):
                suggestion_text = suggestion_text[:-3].strip()
        elif suggestion_text.startswith("```"):
            suggestion_text = suggestion_text.replace("```", "", 1)
            if suggestion_text.endswith("```"):
                suggestion_text = suggestion_text[:-3].strip()

        # Parse the suggestion
        suggestion = json.loads(suggestion_text)

        # Map the category string to TaskCategory enum
        category_mapping = {
            "MEALS": TaskCategory.MEALS,
            "MEDICATION": TaskCategory.MEDICATION,
            "THERAPY": TaskCategory.THERAPY,
            "OUTING": TaskCategory.OUTING
        }
        category = category_mapping.get(suggestion.get("category", "THERAPY"), TaskCategory.THERAPY)

        # Map the priority string to TaskPriority enum
        priority_mapping = {
            "HIGH": TaskPriority.HIGH,
            "MEDIUM": TaskPriority.MEDIUM,
            "LOW": TaskPriority.LOW
        }
        priority = priority_mapping.get(suggestion.get("priority", "MEDIUM"), TaskPriority.MEDIUM)

        # Create start and due times
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(hours=1)  # Default start time is 1 hour from now
        due_time = now + timedelta(hours=3)    # Default due time is 3 hours from now

        # If task is urgent, schedule it sooner
        if suggestion.get("is_urgent", False):
            start_time = now + timedelta(minutes=30)
            due_time = now + timedelta(hours=2)

        # Create the task suggestion
        task_suggestion = {
            "task_title": suggestion["task_title"],
            "task_details": f"{suggestion['task_details']}\n\nReasoning: {suggestion['reasoning']}",
            "category": category,
            "priority": priority,
            "residents": [resident_id],
            "start_date": start_time.isoformat(),
            "due_date": due_time.isoformat(),
            "is_ai_generated": True,
            "assigned_to": str(nurses[0]["_id"]) if nurses else None,
            "status": TaskStatus.ASSIGNED
        }

        return task_suggestion

    except Exception as e:
        print(f"Error generating AI task suggestion: {str(e)}")
        return None 