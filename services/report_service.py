from datetime import datetime, timezone
from typing import List, Dict, Any
from bson import ObjectId
from fastapi import HTTPException
from models.report import ReportCreate, ReportResponse, ReportReview, ReportReviewCreate, ReportReviewStatus, ReportStatus


def convert_string_ids_to_objectid(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert string IDs to ObjectId in nested dictionaries and lists"""
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if (
            (key == "id" or key.endswith("_id"))
            and isinstance(value, str)
            and ObjectId.is_valid(value)
        ):
            result[key] = ObjectId(value)
        elif isinstance(value, dict):
            result[key] = convert_string_ids_to_objectid(value)
        elif isinstance(value, list):
            result[key] = [
                (
                    convert_string_ids_to_objectid(item)
                    if isinstance(item, dict)
                    else (
                        ObjectId(item)
                        if (isinstance(item, str) and ObjectId.is_valid(item))
                        else item
                    )
                )
                for item in value
            ]
        else:
            result[key] = value
    return result


async def create_report(report: ReportCreate, db) -> str:
    report_data = report.model_dump()

    if report_data.get("primary_resident") and isinstance(
        report_data["primary_resident"], dict
    ):
        resident = report_data["primary_resident"]
        if (
            "id" in resident
            and isinstance(resident["id"], str)
            and ObjectId.is_valid(resident["id"])
        ):
            resident["id"] = ObjectId(resident["id"])

    if "involved_residents" in report_data and isinstance(
        report_data["involved_residents"], list
    ):
        for i, resident in enumerate(report_data["involved_residents"]):
            if (
                isinstance(resident, dict)
                and "id" in resident
                and isinstance(resident["id"], str)
                and ObjectId.is_valid(resident["id"])
            ):
                report_data["involved_residents"][i]["id"] = ObjectId(resident["id"])

    if "involved_caregivers" in report_data and isinstance(
        report_data["involved_caregivers"], list
    ):
        for i, caregiver in enumerate(report_data["involved_caregivers"]):
            if (
                isinstance(caregiver, dict)
                and "id" in caregiver
                and isinstance(caregiver["id"], str)
                and ObjectId.is_valid(caregiver["id"])
            ):
                report_data["involved_caregivers"][i]["id"] = ObjectId(caregiver["id"])

    if report_data.get("reporter") and isinstance(report_data["reporter"], dict):
        reporter = report_data["reporter"]
        if (
            "id" in reporter
            and isinstance(reporter["id"], str)
            and ObjectId.is_valid(reporter["id"])
        ):
            reporter["id"] = ObjectId(reporter["id"])

    if (
        "reference_report_id" in report_data
        and isinstance(report_data["reference_report_id"], str)
        and ObjectId.is_valid(report_data["reference_report_id"])
    ):
        report_data["reference_report_id"] = ObjectId(
            report_data["reference_report_id"]
        )

    if (
        "form_id" in report_data
        and isinstance(report_data["form_id"], str)
        and ObjectId.is_valid(report_data["form_id"])
    ):
        report_data["form_id"] = ObjectId(report_data["form_id"])

    report_data["created_at"] = datetime.now(timezone.utc)
    report_data["last_updated_at"] = datetime.now(timezone.utc)

    if report_data.get("status") == "Submitted":
        report_data["submitted_at"] = datetime.now(timezone.utc)

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

    if report_data.get("status") == "Published" or report_data.get("status") == "Submitted":
        raise HTTPException(status_code=400, detail="Cannot modify a submitted or published report")

    update_data = report.model_dump(exclude_unset=True)

    if update_data.get("primary_resident") and isinstance(
        update_data["primary_resident"], dict
    ):
        resident = update_data["primary_resident"]
        if (
            "id" in resident
            and isinstance(resident["id"], str)
            and ObjectId.is_valid(resident["id"])
        ):
            resident["id"] = ObjectId(resident["id"])

    if "involved_residents" in update_data and isinstance(
        update_data["involved_residents"], list
    ):
        for i, resident in enumerate(update_data["involved_residents"]):
            if (
                isinstance(resident, dict)
                and "id" in resident
                and isinstance(resident["id"], str)
                and ObjectId.is_valid(resident["id"])
            ):
                update_data["involved_residents"][i]["id"] = ObjectId(resident["id"])

    if "involved_caregivers" in update_data and isinstance(
        update_data["involved_caregivers"], list
    ):
        for i, caregiver in enumerate(update_data["involved_caregivers"]):
            if (
                isinstance(caregiver, dict)
                and "id" in caregiver
                and isinstance(caregiver["id"], str)
                and ObjectId.is_valid(caregiver["id"])
            ):
                update_data["involved_caregivers"][i]["id"] = ObjectId(caregiver["id"])

    if update_data.get("reporter") and isinstance(update_data["reporter"], dict):
        reporter = update_data["reporter"]
        if (
            "id" in reporter
            and isinstance(reporter["id"], str)
            and ObjectId.is_valid(reporter["id"])
        ):
            reporter["id"] = ObjectId(reporter["id"])

    if (
        "reference_report_id" in update_data
        and isinstance(update_data["reference_report_id"], str)
        and ObjectId.is_valid(update_data["reference_report_id"])
    ):
        update_data["reference_report_id"] = ObjectId(
            update_data["reference_report_id"]
        )

    if (
        "form_id" in update_data
        and isinstance(update_data["form_id"], str)
        and ObjectId.is_valid(update_data["form_id"])
    ):
        update_data["form_id"] = ObjectId(update_data["form_id"])

    update_data["last_updated_at"] = datetime.now(timezone.utc)

    await db["reports"].update_one({"_id": object_id}, {"$set": update_data})
    return report_id


async def remove_report(report_id: str, db):
    try:
        result = await db["reports"].delete_one({"_id": ObjectId(report_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")


async def approve_report(report_id: str, db) -> str:
    try:
        object_id = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    report_data = await db["reports"].find_one({"_id": object_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")

    update_data = {"status": "Published", "published_at": datetime.now(timezone.utc)}
    await db["reports"].update_one({"_id": object_id}, {"$set": update_data})
    return report_id


async def add_report_review(report_id: str, review_data: ReportReviewCreate, db) -> str:
    try:
        object_id = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    report_data = await db["reports"].find_one({"_id": object_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report_data.get("status") == "Changes Requested":
        raise HTTPException(status_code=400, detail="Cannot review a report that is already under review")

    review = ReportReview(
        **review_data.model_dump(),
        reviewed_at=datetime.now(timezone.utc),
        status=ReportReviewStatus.PENDING
    )

    report_data["reviews"].append(review.model_dump())
    report_data["status"] = ReportStatus.CHANGES_REQUESTED

    await db["reports"].update_one({"_id": object_id}, {"$set": report_data})
    return report_id
    

async def resolve_report_review(report_id: str, resolution: str, db) -> str:
    try:
        object_id = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    report_data = await db["reports"].find_one({"_id": object_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")

    report_data["reviews"][-1]["resolution"] = resolution
    report_data["reviews"][-1]["status"] = ReportReviewStatus.RESOLVED
    report_data["reviews"][-1]["resolved_at"] = datetime.now(timezone.utc)
    report_data["status"] = ReportStatus.CHANGES_MADE

    await db["reports"].update_one({"_id": object_id}, {"$set": report_data})
    return report_id
