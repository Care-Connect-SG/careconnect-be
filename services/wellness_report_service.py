import datetime

from bson import ObjectId
from fastapi import HTTPException

from models.wellness_report import WellnessReportCreate, WellnessReportResponse


async def create_wellness_report(
    db, resident_id: str, report_data: WellnessReportCreate
):
    try:
        ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    report_dict = report_data.model_dump()
    report_dict["resident_id"] = ObjectId(resident_id)

    if "date" in report_dict and isinstance(report_dict["date"], datetime.date):
        report_dict["date"] = datetime.datetime.combine(
            report_dict["date"], datetime.time.min
        )

    try:
        result = await db["wellness_reports"].insert_one(report_dict)
        new_report = await db["wellness_reports"].find_one({"_id": result.inserted_id})
        return WellnessReportResponse(**new_report)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create wellness report: {str(e)}"
        )


async def get_reports_by_resident(db, resident_id: str):
    try:
        resident_obj_id = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resident ID")

    try:
        reports = []
        cursor = (
            db["wellness_reports"]
            .find({"resident_id": resident_obj_id})
            .sort("report_date", -1)
        )

        async for record in cursor:
            report = WellnessReportResponse(**record)
            reports.append(report)

        return reports
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve wellness reports: {str(e)}"
        )


async def get_wellness_report_by_id(db, resident_id: str, report_id: str):
    try:
        report_obj_id = ObjectId(report_id)
        resident_obj_id = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    try:
        report = await db["wellness_reports"].find_one(
            {"_id": report_obj_id, "resident_id": resident_obj_id}
        )

        if not report:
            raise HTTPException(status_code=404, detail="Wellness report not found")

        return WellnessReportResponse(**report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve wellness report: {str(e)}"
        )


async def update_wellness_report(
    db, resident_id: str, report_id: str, update_data: WellnessReportCreate
):
    try:
        report_obj_id = ObjectId(report_id)
        resident_obj_id = ObjectId(resident_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    update_dict = update_data.model_dump(exclude_unset=True)

    if "resident_id" in update_dict:
        try:
            update_dict["resident_id"] = ObjectId(update_dict["resident_id"])
        except:
            raise HTTPException(
                status_code=400, detail="Invalid resident ID in update data"
            )

    if "date" in update_dict and isinstance(update_dict["date"], datetime.date):
        update_dict["date"] = datetime.datetime.combine(
            update_dict["date"], datetime.time.min
        )

    try:
        result = await db["wellness_reports"].update_one(
            {"_id": report_obj_id, "resident_id": resident_obj_id},
            {"$set": update_dict},
        )

        if result.modified_count == 0:
            existing = await db["wellness_reports"].find_one(
                {"_id": report_obj_id, "resident_id": resident_obj_id}
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Wellness report not found")

        updated = await db["wellness_reports"].find_one({"_id": report_obj_id})
        return WellnessReportResponse(**updated)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update wellness report: {str(e)}"
        )


async def delete_wellness_report(db, resident_id: str, report_id: str):
    try:
        report_obj_id = ObjectId(report_id)
        resident_obj_id = ObjectId(resident_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    try:
        result = await db["wellness_reports"].delete_one(
            {"_id": report_obj_id, "resident_id": resident_obj_id}
        )

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Wellness report not found")

        return {"detail": "Wellness report deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete wellness report: {str(e)}"
        )
