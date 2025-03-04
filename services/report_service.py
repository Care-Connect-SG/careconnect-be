from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from models.report import ReportCreate


async def create_report(report: ReportCreate, db):
    report_data = report.model_dump()
    report_data["created_date"] = datetime.now()
    result = await db["reports"].insert_one(report_data)
    return str(result.inserted_id)


async def get_reports(status: str, db):
    query = {}
    if status:
        query["status"] = status
    cursor = db["reports"].find(query)
    reports = []
    async for report in cursor:
        report["id"] = str(report["_id"])
        reports.append(report)
    return reports


async def get_report_by_id(report_id: str, db):
    try:
        object_id = ObjectId(report_id) 
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID format")

    report = await db["reports"].find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report["_id"] = str(report["_id"])
    return report


async def update_report(report_id: str, report: ReportCreate, db):
    try:
        object_id = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")
    
    report_data = await db["report"].find_one({"_id": object_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")

    if report_data.get("status") == "Published":
        raise HTTPException(status_code=400, detail="Cannot modify a published report")
    
    update_data = report.model_dump(exclude_unset=True)
    await db["reports"].update_one({"_id": object_id}, {"$set": update_data})
    return report_id


async def remove_report(report_id: str, db):
    try:
        result = await db["reports"].delete_one({"_id": ObjectId(report_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")



