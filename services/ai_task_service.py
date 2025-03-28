"""
AI-driven task suggestion service for CareConnect.
This module uses LangChain and OpenAI to generate task suggestions based on resident data.
"""

import json
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import asyncio
import traceback

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from models.task import TaskCreate, TaskStatus, TaskPriority, TaskCategory
from utils.config import OPENAI_API_KEY


async def get_enhanced_ai_task_suggestion(
    db, resident_id: str, current_user: dict
) -> TaskCreate:
    """
    Generate an AI-enhanced task suggestion for a resident using GPT-4o Mini.
    
    Args:
        db: MongoDB database connection
        resident_id: ID of the resident to create a task for
        current_user: Current user information
        
    Returns:
        TaskCreate: A task object with AI-generated suggestions
    """
    # Set default fallback values that will be used if AI generation fails
    fallback_title = "Personalized Care Check"
    fallback_details = "Check on resident's well-being and provide necessary assistance"
    
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
        
        # Format the data for the LLM
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
        
        # Get available nurses and their workloads for scheduling
        nurses = await db.users.find({"role": "Nurse"}).to_list(length=None)
        
        # Calculate workload for each nurse (number of current tasks)
        now = datetime.now(timezone.utc)
        nurse_workloads = {}
        
        for nurse in nurses:
            nurse_id = str(nurse.get("_id"))
            nurse_name = f"{nurse.get('first_name', '')} {nurse.get('last_name', '')}"
            active_tasks = await db.tasks.count_documents({
                "assigned_to": ObjectId(nurse_id),
                "status": {"$in": [TaskStatus.ASSIGNED]},
                "due_date": {"$gte": now}
            })
            
            # Get upcoming tasks in the next 24 hours
            upcoming_tasks = await db.tasks.count_documents({
                "assigned_to": ObjectId(nurse_id),
                "status": {"$in": [TaskStatus.ASSIGNED]},
                "start_date": {"$gte": now, "$lte": now + timedelta(hours=24)}
            })
            
            nurse_workloads[nurse_id] = {
                "id": nurse_id,
                "name": nurse_name,
                "active_tasks": active_tasks,
                "upcoming_tasks": upcoming_tasks,
                "email": nurse.get("email", ""),
                "total_workload": active_tasks + (2 * upcoming_tasks)  # Weight upcoming tasks higher
            }
        
        # Find nurse with lowest workload
        recommended_nurse = None
        lowest_workload = float('inf')
        for nurse_id, workload_info in nurse_workloads.items():
            if workload_info["total_workload"] < lowest_workload:
                lowest_workload = workload_info["total_workload"]
                recommended_nurse = nurse_id
        
        # Format nurse workload data for the LLM
        nurse_data = "\n".join([
            f"- {details['name']} ({details['email']}): {details['active_tasks']} active tasks, {details['upcoming_tasks']} upcoming tasks in next 24h"
            for nurse_id, details in nurse_workloads.items()
        ])
        
        # Update fallback title with resident name for personalization
        if resident:
            first_name = resident.get('first_name', '')
            if first_name:
                fallback_title = f"Check-in with {first_name}"
                fallback_details = f"Personalized care check for {first_name} based on their care needs"
        
        # Determine optimal start time based on priority and medical history
        now = datetime.now(timezone.utc)
        suggested_start_time = now + timedelta(hours=1)  # Default start time is 1 hour from now
        suggested_due_time = now + timedelta(hours=3)    # Default due time is 3 hours from now
        
        # If there's high risk in medical history, schedule sooner
        has_high_risk = any(record.get("risk_level") == "High" for record in medical_records) if medical_records else False
        if has_high_risk:
            suggested_start_time = now + timedelta(minutes=30)
            suggested_due_time = now + timedelta(hours=2)
        
        # Create a simple prompt template
        template = """
        You are a healthcare assistant AI. Based on the resident information, past tasks, medical history, and nurse workloads,
        suggest a new care task that would be appropriate for the resident and assign it to the most suitable nurse.
        
        Resident Name: {resident_name}
        
        Past Tasks:
        {tasks_info}
        
        Medical History:
        {medical_info}
        
        Available Nurses and Workloads:
        {nurse_data}
        
        Current Time: {current_time}
        
        Please provide a suitable task in the following JSON format:
        {{
            "task_title": "Clear, specific title for the task",
            "task_details": "Detailed instructions for the caregiver",
            "priority": "HIGH, MEDIUM, or LOW",
            "category": "MEALS, MEDICATION, THERAPY, or OUTING",
            "recommended_nurse_id": "ID of the nurse with most suitable availability",
            "is_urgent": true or false,
            "suggested_start_time": "YYYY-MM-DD HH:MM:SS",
            "suggested_due_time": "YYYY-MM-DD HH:MM:SS",
            "reasoning": "Explain why this task is important for this resident and why this nurse and timing was selected"
        }}
        
        Make sure your response is ONLY valid JSON with no extra text before or after. Check that all field values are valid and each field has a value.
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["resident_name", "tasks_info", "medical_info", "nurse_data", "current_time"]
        )
        
        # Set up the LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model="gpt-4o-mini",
            temperature=0.2
        )
        
        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        try:
            # Since LangChain's arun may not be fully compatible with FastAPI's async,
            # we'll use asyncio to run the chain in a separate thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: chain.invoke({
                    "resident_name": resident_name,
                    "tasks_info": tasks_info,
                    "medical_info": medical_info,
                    "nurse_data": nurse_data,
                    "current_time": now.strftime("%Y-%m-%d %H:%M:%S")
                })
            )
            
            # Extract just the generated text from the response and print for debugging
            suggestion_text = response["text"].strip()
            print(f"OpenAI response: {suggestion_text}")
            
            # Try to clean up response by removing any markdown code blocks
            if suggestion_text.startswith("```json"):
                suggestion_text = suggestion_text.replace("```json", "", 1)
                if suggestion_text.endswith("```"):
                    suggestion_text = suggestion_text[:-3].strip()
            elif suggestion_text.startswith("```"):
                suggestion_text = suggestion_text.replace("```", "", 1)
                if suggestion_text.endswith("```"):
                    suggestion_text = suggestion_text[:-3].strip()
            
            # Parse the JSON response
            suggestion = json.loads(suggestion_text)
            
            # Validate that we got necessary fields
            if not suggestion.get("task_title") or not suggestion.get("task_details"):
                print("Missing required fields in AI response")
                raise KeyError("Response missing required fields")
            
            # Map the category string to TaskCategory enum
            category_mapping = {
                "MEALS": TaskCategory.MEALS,
                "MEDICATION": TaskCategory.MEDICATION,
                "THERAPY": TaskCategory.THERAPY,
                "OUTING": TaskCategory.OUTING
            }
            category = category_mapping.get(
                suggestion.get("category", "MEALS"), 
                TaskCategory.MEALS
            )
            
            # Map the priority string to TaskPriority enum
            priority_mapping = {
                "HIGH": TaskPriority.HIGH,
                "MEDIUM": TaskPriority.MEDIUM,
                "LOW": TaskPriority.LOW
            }
            priority = priority_mapping.get(
                suggestion.get("priority", "MEDIUM"), 
                TaskPriority.MEDIUM
            )
            
            # Parse suggested times or use defaults
            try:
                start_time = datetime.strptime(suggestion.get("suggested_start_time"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                start_time = suggested_start_time
                
            try:
                due_time = datetime.strptime(suggestion.get("suggested_due_time"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                due_time = suggested_due_time
            
            # Get recommended nurse ID or use current user
            recommended_nurse_id = suggestion.get("recommended_nurse_id", recommended_nurse)
            if not recommended_nurse_id or recommended_nurse_id not in nurse_workloads:
                recommended_nurse_id = str(current_user["id"])
                
            # Create task suggestion
            task_create = TaskCreate(
                task_title=suggestion.get("task_title", fallback_title),
                task_details=suggestion.get("task_details", fallback_details),
                status=TaskStatus.ASSIGNED,
                priority=priority,
                category=category,
                residents=[ObjectId(resident_id)],
                start_date=start_time,
                due_date=due_time,
                is_ai_generated=True,
                assigned_to=ObjectId(recommended_nurse_id),
                ai_recommendation_reason=suggestion.get("reasoning", "AI-generated task based on resident history")
            )
            
            # Return the task with the recommended nurse ID for the frontend
            result = task_create.dict()
            result["recommended_nurse_id"] = recommended_nurse_id
            
            return TaskCreate(**result)
            
        except (json.JSONDecodeError, KeyError) as e:
            # Print the error and traceback for debugging
            print(f"Error parsing AI response: {e}")
            print(f"Response was: {response['text'] if 'text' in response else 'No text in response'}")
            print(traceback.format_exc())
            
            # Get medical condition to personalize fallback task if possible
            condition = None
            if medical_records and len(medical_records) > 0:
                condition = medical_records[0].get('condition')
            
            # Create a personalized fallback task
            personalized_title = fallback_title
            personalized_details = fallback_details
            
            if condition:
                personalized_title = f"Health check related to {condition}"
                personalized_details = f"Check on resident's condition ({condition}) and provide appropriate care"
            
            # Fallback to basic task suggestion with personalization
            task_create = TaskCreate(
                task_title=personalized_title,
                task_details=personalized_details,
                status=TaskStatus.ASSIGNED,
                priority=TaskPriority.MEDIUM,
                category=TaskCategory.MEALS,
                residents=[ObjectId(resident_id)],
                start_date=suggested_start_time,
                due_date=suggested_due_time,
                is_ai_generated=True,
                assigned_to=ObjectId(recommended_nurse or current_user["id"]),
                ai_recommendation_reason="Based on resident's care history and general wellbeing needs"
            )
            
            # Return the task with the recommended nurse ID for the frontend
            result = task_create.dict()
            result["recommended_nurse_id"] = recommended_nurse or str(current_user["id"])
            
            return TaskCreate(**result)
    
    except Exception as e:
        # Print the error and traceback for debugging
        print(f"Error in AI task suggestion: {e}")
        print(traceback.format_exc())
        
        # Use resident name if available to personalize fallback
        personalized_fallback = fallback_title
        personalized_details = fallback_details
        
        # Return a better fallback task in case of any errors
        now = datetime.now(timezone.utc)
        task_create = TaskCreate(
            task_title=personalized_fallback,
            task_details=personalized_details,
            status=TaskStatus.ASSIGNED,
            priority=TaskPriority.MEDIUM,
            category=TaskCategory.MEALS,
            residents=[ObjectId(resident_id)],
            start_date=now + timedelta(hours=1),
            due_date=now + timedelta(hours=3),
            is_ai_generated=True,
            assigned_to=ObjectId(current_user["id"]),
            ai_recommendation_reason="Created as a general care task for this resident"
        )
        
        # Return the task with just the current user as recommended nurse
        result = task_create.dict()
        result["recommended_nurse_id"] = str(current_user["id"])
        
        return TaskCreate(**result) 