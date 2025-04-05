import json
from datetime import datetime, timezone
from bson import ObjectId
import asyncio
import traceback
from fastapi import HTTPException, status

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from models.wellness_report import WellnessReportCreate
from utils.config import OPENAI_API_KEY


async def get_ai_wellness_report_suggestion(
    db, resident_id: str, current_user: dict, context: str = ""
) -> WellnessReportCreate:
    try:
        resident_db = db.client.get_database("resident")
        resident = await resident_db.resident_info.find_one(
            {"_id": ObjectId(resident_id)}
        )
        if not resident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found"
            )

        resident_name = (
            f"{resident.get('first_name', '')} {resident.get('last_name', '')}"
            if resident
            else "Unknown Resident"
        )

        medical_records = (
            await resident_db.medical_history.find(
                {"resident_id": ObjectId(resident_id)}
            )
            .sort("created_at", -1)
            .limit(5)
            .to_list(length=5)
        )

        medical_info = (
            "\n".join(
                [
                    f"- Condition: {record.get('condition', 'Unknown')}, Risk Level: {record.get('risk_level', 'Unknown')}, "
                    f"Notes: {record.get('notes', 'No notes')}"
                    for record in medical_records
                ]
            )
            if medical_records
            else "No medical history available."
        )

        vital_signs = (
            await resident_db.vital_signs.find({"resident_id": ObjectId(resident_id)})
            .sort("created_at", -1)
            .limit(5)
            .to_list(length=5)
        )

        vital_signs_info = (
            "\n".join(
                [
                    f"- Date: {record.get('created_at', 'Unknown')}, "
                    f"Blood Pressure: {record.get('blood_pressure', 'N/A')}, "
                    f"Heart Rate: {record.get('heart_rate', 'N/A')}, "
                    f"Temperature: {record.get('temperature', 'N/A')}, "
                    f"Oxygen Saturation: {record.get('oxygen_saturation', 'N/A')}"
                    for record in vital_signs
                ]
            )
            if vital_signs
            else "No vital signs data available."
        )

        past_reports = (
            await resident_db.wellness_reports.find(
                {"resident_id": ObjectId(resident_id)}
            )
            .sort("created_at", -1)
            .limit(3)
            .to_list(length=3)
        )

        past_reports_info = (
            "\n".join(
                [
                    f"Report Date: {report.get('date', 'Unknown')}\n"
                    f"Summary: {report.get('summary', 'No summary')}\n"
                    f"Medical Summary: {report.get('medical_summary', 'No medical summary')}\n"
                    f"Medication Update: {report.get('medication_update', 'No medication update')}\n"
                    f"Nutrition & Hydration: {report.get('nutrition_hydration', 'No nutrition info')}\n"
                    f"Mobility: {report.get('mobility_physical', 'No mobility info')}\n"
                    f"Cognitive & Emotional: {report.get('cognitive_emotional', 'No cognitive info')}\n"
                    f"Social Engagement: {report.get('social_engagement', 'No social info')}\n"
                    f"Recommendations: {', '.join(report.get('ai_recommendations', []) if isinstance(report.get('ai_recommendations'), list) else [])}\n"
                    for report in past_reports
                ]
            )
            if past_reports
            else "No previous wellness reports available."
        )

        additional_context = (
            context if context.strip() else "No additional context provided."
        )

        template = """
        You are a healthcare AI assistant. Based on the resident's medical history, vital signs, previous wellness reports, and any additional context provided,
        generate a comprehensive wellness report that includes:
        1. Summary of overall health and care
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

        Additional Context Provided by Staff:
        {additional_context}

        Current Time: {current_time}

        Please provide the report in the following JSON format:
        {{
            "summary": "A comprehensive summary of the resident's health and care for the month, including trends from previous reports",
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

        Focus especially on any new information provided in the Additional Context section.
        """

        prompt = PromptTemplate(
            template=template,
            input_variables=[
                "resident_name",
                "medical_info",
                "vital_signs_info",
                "past_reports_info",
                "additional_context",
                "current_time",
            ],
        )

        llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4", temperature=0.2)
        chain = LLMChain(llm=llm, prompt=prompt)

        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: chain.invoke(
                    {
                        "resident_name": resident_name,
                        "medical_info": medical_info,
                        "vital_signs_info": vital_signs_info,
                        "past_reports_info": past_reports_info,
                        "additional_context": additional_context,
                        "current_time": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                ),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI model service unavailable: {str(e)}",
            )

        report_text = response["text"].strip()

        if report_text.startswith("```json"):
            report_text = report_text.replace("```json", "", 1)
            if report_text.endswith("```"):
                report_text = report_text[:-3].strip()
        elif report_text.startswith("```"):
            report_text = report_text.replace("```", "", 1)
            if report_text.endswith("```"):
                report_text = report_text[:-3].strip()

        try:
            suggestion = json.loads(report_text)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse AI response: {str(e)}",
            )

        if not suggestion.get("summary") or not suggestion.get("medical_summary"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI response missing required fields",
            )

        try:
            report_create = WellnessReportCreate(
                date=datetime.strptime(suggestion.get("date"), "%Y-%m-%d").date(),
                summary=suggestion.get("summary"),
                medical_summary=suggestion.get("medical_summary"),
                medication_update=suggestion.get("medication_update"),
                nutrition_hydration=suggestion.get("nutrition_hydration"),
                mobility_physical=suggestion.get("mobility_physical"),
                cognitive_emotional=suggestion.get("cognitive_emotional"),
                social_engagement=suggestion.get("social_engagement"),
                is_ai_generated=True,
                ai_confidence_score=suggestion.get("confidence_score", 0.5),
                ai_recommendations=suggestion.get("recommendations", []),
            )
            return report_create
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating wellness report: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error generating wellness report: {str(e)}",
        )
