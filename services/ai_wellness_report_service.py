import json
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import asyncio
import traceback

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from models.wellness_report import WellnessReportCreate
from utils.config import OPENAI_API_KEY


async def get_ai_wellness_report_suggestion(
    db, resident_id: str, current_user: dict
) -> WellnessReportCreate:
    """
    Generate an AI-enhanced wellness report suggestion for a resident using GPT-4.
    
    Args:
        db: MongoDB database connection
        resident_id: ID of the resident to generate report for
        current_user: Current user information
        
    Returns:
        WellnessReportCreate: A wellness report object with AI-generated suggestions
    """
    try:
        # Get resident information
        resident_db = db.client.get_database("resident")
        print(f"Looking for resident with ID: {resident_id}")  # Debug log
        resident = await resident_db.resident_info.find_one({"_id": ObjectId(resident_id)})
        if not resident:
            print(f"Resident not found with ID: {resident_id}")
            raise ValueError("Resident not found")
            
        resident_name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}" if resident else "Unknown Resident"
        print(f"Generating report for resident: {resident_name}")
        
        # Get medical history
        print("Fetching medical history...")  # Debug log
        medical_records = await resident_db.medical_history.find({
            "resident_id": ObjectId(resident_id)
        }).sort("created_at", -1).limit(5).to_list(length=5)
        
        print(f"Found {len(medical_records)} medical records")
        medical_info = "\n".join([
            f"- Condition: {record.get('condition', 'Unknown')}, Risk Level: {record.get('risk_level', 'Unknown')}, "
            f"Notes: {record.get('notes', 'No notes')}"
            for record in medical_records
        ]) if medical_records else "No medical history available."
        
        # Get vital signs if available
        print("Fetching vital signs...")  # Debug log
        vital_signs = await resident_db.vital_signs.find({
            "resident_id": ObjectId(resident_id)
        }).sort("created_at", -1).limit(5).to_list(length=5)
        
        print(f"Found {len(vital_signs)} vital signs records")
        vital_signs_info = "\n".join([
            f"- Date: {record.get('created_at', 'Unknown')}, "
            f"Blood Pressure: {record.get('blood_pressure', 'N/A')}, "
            f"Heart Rate: {record.get('heart_rate', 'N/A')}, "
            f"Temperature: {record.get('temperature', 'N/A')}, "
            f"Oxygen Saturation: {record.get('oxygen_saturation', 'N/A')}"
            for record in vital_signs
        ]) if vital_signs else "No vital signs data available."

        # Get past wellness reports (most recent 3)
        print("Fetching past wellness reports...")  # Debug log
        past_reports = await resident_db.wellness_reports.find({
            "resident_id": ObjectId(resident_id)
        }).sort("created_at", -1).limit(3).to_list(length=3)

        print(f"Found {len(past_reports)} past wellness reports")
        # Format past reports for analysis
        past_reports_info = "\n".join([
            f"Report Date: {report.get('date', 'Unknown')}\n"
            f"Monthly Summary: {report.get('monthly_summary', 'No summary')}\n"
            f"Medical Summary: {report.get('medical_summary', 'No medical summary')}\n"
            f"Medication Update: {report.get('medication_update', 'No medication update')}\n"
            f"Nutrition & Hydration: {report.get('nutrition_hydration', 'No nutrition info')}\n"
            f"Mobility: {report.get('mobility_physical', 'No mobility info')}\n"
            f"Cognitive & Emotional: {report.get('cognitive_emotional', 'No cognitive info')}\n"
            f"Social Engagement: {report.get('social_engagement', 'No social info')}\n"
            f"Recommendations: {', '.join(report.get('ai_recommendations', []) if isinstance(report.get('ai_recommendations'), list) else [])}\n"
            for report in past_reports
        ]) if past_reports else "No previous wellness reports available."
        
        # Create a prompt template for wellness report generation
        template = """
        You are a healthcare AI assistant. Based on the resident's medical history, vital signs, and previous wellness reports,
        generate a comprehensive wellness report that includes:
        1. Monthly summary of overall health and care
        2. Medical condition updates and changes
        3. Medication adherence and updates
        4. Nutrition and hydration status
        5. Physical mobility assessment
        6. Cognitive and emotional wellbeing
        7. Social engagement levels
        
        Resident Name: {resident_name}
        
        Medical History:
        {medical_info}
        
        Vital Signs:
        {vital_signs_info}
        
        Previous Wellness Reports:
        {past_reports_info}
        
        Current Time: {current_time}
        
        Please provide the report in the following JSON format:
        {{
            "monthly_summary": "A comprehensive summary of the resident's health and care for the month, including trends from previous reports",
            "medical_summary": "Detailed analysis of medical conditions and changes, comparing with previous reports",
            "medication_update": "Analysis of medication adherence and any concerns, noting any changes from previous reports",
            "nutrition_hydration": "Assessment of nutrition and hydration status, tracking changes over time",
            "mobility_physical": "Evaluation of physical mobility and activity levels, comparing with previous reports",
            "cognitive_emotional": "Analysis of cognitive function and emotional wellbeing, noting any trends",
            "social_engagement": "Assessment of social interaction and engagement levels, tracking changes",
            "date": "YYYY-MM-DD",
            "confidence_score": 0.0 to 1.0,
            "recommendations": [
                "List of specific recommendations based on the analysis and historical trends"
            ]
        }}
        
        Make sure your response is ONLY valid JSON with no extra text before or after. Check that all field values are valid and each field has a value.
        The confidence score should reflect how confident you are in the accuracy of your analysis based on the available data.
        Pay special attention to trends and changes over time from the previous wellness reports.
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["resident_name", "medical_info", "vital_signs_info", "past_reports_info", "current_time"]
        )
        
        # Set up the LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model="gpt-4",
            temperature=0.2
        )
        
        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        try:
            print("Invoking LLM chain...")
            # Run the chain in a separate thread
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: chain.invoke({
                        "resident_name": resident_name,
                        "medical_info": medical_info,
                        "vital_signs_info": vital_signs_info,
                        "past_reports_info": past_reports_info,
                        "current_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    })
                )
                print("LLM chain executed successfully")
            except Exception as e:
                print(f"Error during LLM chain execution: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                raise
            
            print("Received response from LLM")
            # Extract and clean up the response
            report_text = response["text"].strip()
            print(f"Raw response: {report_text}")
            
            # Clean up response by removing any markdown code blocks
            if report_text.startswith("```json"):
                report_text = report_text.replace("```json", "", 1)
                if report_text.endswith("```"):
                    report_text = report_text[:-3].strip()
            elif report_text.startswith("```"):
                report_text = report_text.replace("```", "", 1)
                if report_text.endswith("```"):
                    report_text = report_text[:-3].strip()
            
            print(f"Cleaned response: {report_text}")
            
            try:
                # Parse the JSON response
                suggestion = json.loads(report_text)
                print(f"Successfully parsed JSON: {json.dumps(suggestion, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {str(e)}")
                print(f"Response that failed to parse: {report_text}")
                raise
            
            # Validate that we got necessary fields
            if not suggestion.get("monthly_summary") or not suggestion.get("medical_summary"):
                print("Missing required fields in AI response")
                print(f"Available fields: {list(suggestion.keys())}")
                raise KeyError("Response missing required fields")
            
            try:
                # Create wellness report suggestion
                report_create = WellnessReportCreate(
                    date=datetime.strptime(suggestion.get("date"), "%Y-%m-%d").date(),
                    monthly_summary=suggestion.get("monthly_summary"),
                    medical_summary=suggestion.get("medical_summary"),
                    medication_update=suggestion.get("medication_update"),
                    nutrition_hydration=suggestion.get("nutrition_hydration"),
                    mobility_physical=suggestion.get("mobility_physical"),
                    cognitive_emotional=suggestion.get("cognitive_emotional"),
                    social_engagement=suggestion.get("social_engagement"),
                    is_ai_generated=True,
                    ai_confidence_score=suggestion.get("confidence_score", 0.5),
                    ai_recommendations=suggestion.get("recommendations", [])
                )
                print("Successfully created wellness report")
                return report_create
            except Exception as e:
                print(f"Error creating WellnessReportCreate: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                raise
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing AI response: {e}")
            print(f"Response was: {response['text'] if 'text' in response else 'No text in response'}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise  # Re-raise the exception to be caught by the outer try-except
    
    except Exception as e:
        print(f"Error generating wellness report: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return a basic fallback report
        now = datetime.now(timezone.utc)
        fallback_report = WellnessReportCreate(
            date=now.date(),
            monthly_summary="Monthly health and care summary based on available data",
            medical_summary="Medical condition analysis and updates",
            medication_update="Medication adherence and management status",
            nutrition_hydration="Nutrition and hydration assessment",
            mobility_physical="Physical mobility and activity evaluation",
            cognitive_emotional="Cognitive and emotional wellbeing analysis",
            social_engagement="Social interaction and engagement assessment",
            is_ai_generated=True,
            ai_confidence_score=0.3,
            ai_recommendations=["Review available data for more accurate assessment"]
        )
        
        return fallback_report