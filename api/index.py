from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from db.connection import lifespan, get_db, get_resident_db
from routers.activity import router as activity_router
from routers.cloudinary.image import router as image_router
from routers.group import router as group_router
from routers.health_record.careplan import router as careplan_router
from routers.health_record.medical_history import router as medical_history_router
from routers.health_record.medication import router as medication_router
from routers.incident.form import router as form_router
from routers.incident.report import router as report_router
from routers.resident import router as resident_router
from routers.tag import router as tag_router
from routers.task import router as task_router
from routers.user import router as user_router
from utils.config import FE_URL
from utils.limiter import limiter


app = FastAPI(root_path="/api/v1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(group_router)
app.include_router(task_router)
app.include_router(resident_router)
app.include_router(medication_router)
app.include_router(form_router)
app.include_router(report_router)
app.include_router(tag_router)
app.include_router(careplan_router)
app.include_router(activity_router)
app.include_router(medical_history_router)
app.include_router(image_router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
def read_root():
    return {"status": "Server is healthy"}


async def migrate_collection(source_db, target_db, collection_name):
    """
    Migrates a collection from source to target database while preserving ObjectIDs.

    Args:
        source_db: Source AsyncIOMotorDatabase
        target_db: Target AsyncIOMotorDatabase
        collection_name: Name of the collection to migrate
    """
    try:
        # Get all documents from source collection
        documents = await source_db[collection_name].find({}).to_list(None)

        if documents:
            # Insert all documents to target collection
            # This preserves the _id and all other fields exactly as they were
            await target_db[collection_name].insert_many(documents)

        print(
            f"✅ Successfully migrated {len(documents)} documents from {collection_name}"
        )

    except Exception as e:
        print(f"❌ Migration failed for {collection_name}: {str(e)}")


@app.post("/migrate-collection/{collection_name}")
async def migrate_collection_endpoint(
    collection_name: str,
    request: Request,
):

    target_db = await get_db(request)
    source_db = await get_resident_db(request)

    await migrate_collection(source_db, target_db, collection_name)

    return {"message": f"Migration of {collection_name} completed successfully"}
