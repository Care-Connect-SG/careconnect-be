def convert_id(document):
    """Helper function to convert MongoDB ObjectId to a string."""
    if document and "_id" in document:
        document["_id"] = str(document["_id"])
    return document