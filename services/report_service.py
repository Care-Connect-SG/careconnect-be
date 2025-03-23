from datetime import datetime, timezone
from typing import List
from bson import ObjectId
from fastapi import HTTPException
from models.report import ReportCreate, ReportResponse
from utils.object_converter import convert_nested_ids_to_objectid


async def create_report(report: ReportCreate, db) -> str:
    report_data = report.model_dump()

    report_data = convert_nested_ids_to_objectid(report_data)

    report_data["created_date"] = datetime.now(timezone.utc)

    result = await db["reports"].insert_one(report_data)
    return str(result.inserted_id)


async def get_reports(status: str, db) -> List[ReportResponse]:
    query = {}
    if status:
        query["status"] = status

    cursor = db["reports"].find(query)
    reports = []
    async for report in cursor:
        reports.append(report)

    return [ReportResponse(**report) for report in reports]


async def get_report_by_id(report_id: str, db) -> ReportResponse:
    try:
        object_id = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID format")

    report_data = await db["reports"].find_one({"_id": object_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(**report_data)


async def update_report(report_id: str, report: ReportCreate, db) -> str:
    try:
        object_id = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    report_data = await db["reports"].find_one({"_id": object_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")

    if report_data.get("status") == "Published":
        raise HTTPException(status_code=400, detail="Cannot modify a published report")

    update_data = report.model_dump(exclude_unset=True)
    update_data = convert_nested_ids_to_objectid(update_data)

    await db["reports"].update_one({"_id": object_id}, {"$set": update_data})
    return report_id


async def remove_report(report_id: str, db):
    try:
        result = await db["reports"].delete_one({"_id": ObjectId(report_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")
