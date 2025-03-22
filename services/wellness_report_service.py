import datetime
from bson import ObjectId
from fastapi import HTTPException
from models.wellness_report import WellnessReportCreate, WellnessReportResponse


async def create_wellness_report(
    db, resident_id: str, report_data: WellnessReportCreate
):
    try:
        resident_oid = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    report_dict = report_data.dict()
    report_dict["resident_id"] = resident_id

    if "date" in report_dict and isinstance(report_dict["date"], datetime.date):
        report_dict["date"] = datetime.datetime.combine(
            report_dict["date"], datetime.time.min
        )

    result = await db["wellness_reports"].insert_one(report_dict)
    new_report = await db["wellness_reports"].find_one({"_id": result.inserted_id})

    return WellnessReportResponse(**new_report)


async def get_reports_by_resident(db, resident_id: str):
    try:
        resident_oid = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    reports = []
    cursor = (
        db["wellness_reports"]
        .find({"resident_id": resident_id})
        .sort("report_date", -1)
    )

    async for record in cursor:
        reports.append(WellnessReportResponse(**record))

    return reports


async def get_wellness_report_by_id(db, resident_id: str, report_id: str):
    try:
        report_oid = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    report = await db["wellness_reports"].find_one({"_id": report_oid})
    if not report:
        raise HTTPException(status_code=404, detail="Wellness report not found")

    return WellnessReportResponse(**report)


async def update_wellness_report(
    db, resident_id: str, report_id: str, update_data: WellnessReportCreate
):
    try:
        report_oid = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    update_dict = update_data.dict(exclude_unset=True)

    if "date" in update_dict and isinstance(update_dict["date"], datetime.date):
        update_dict["date"] = datetime.datetime.combine(
            update_dict["date"], datetime.time.min
        )

    result = await db["wellness_reports"].update_one(
        {"_id": report_oid}, {"$set": update_dict}
    )

    if result.modified_count == 0:
        existing = await db["wellness_reports"].find_one({"_id": report_oid})
        if not existing:
            raise HTTPException(status_code=404, detail="Wellness report not found")

    updated = await db["wellness_reports"].find_one({"_id": report_oid})
    return WellnessReportResponse(**updated)


async def delete_wellness_report(db, resident_id: str, report_id: str):
    try:
        report_oid = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    result = await db["wellness_reports"].delete_one({"_id": report_oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Wellness report not found")

    return {"detail": "Wellness report deleted successfully"}
