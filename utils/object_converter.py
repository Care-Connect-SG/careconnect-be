from typing import Dict, Any
from bson import ObjectId


def convert_nested_ids_to_objectid(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert string IDs to ObjectIds in nested dictionaries."""
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if key == "id" and isinstance(value, str) and ObjectId.is_valid(value):
            continue
        elif key == "_id" and isinstance(value, str) and ObjectId.is_valid(value):
            result[key] = ObjectId(value)
        elif (
            key in ["form_id", "reference_report_id"]
            and isinstance(value, str)
            and ObjectId.is_valid(value)
        ):
            result[key] = ObjectId(value)
        elif isinstance(value, dict):
            nested_obj = convert_nested_ids_to_objectid(value)
            if (
                "id" in nested_obj
                and isinstance(nested_obj["id"], str)
                and ObjectId.is_valid(nested_obj["id"])
            ):
                nested_obj["_id"] = ObjectId(nested_obj.pop("id"))
            result[key] = nested_obj
        elif isinstance(value, list):
            result[key] = [
                convert_nested_ids_to_objectid(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result
