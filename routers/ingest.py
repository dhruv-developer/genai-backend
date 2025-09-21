# from fastapi import APIRouter
# from models.schemas import IngestRequest
# from database import db

# router = APIRouter()

# @router.post("/ingest/data")
# def ingest_data(payload: IngestRequest):
#     collection = db[payload.data_type]  # dynamic collection
#     result = collection.insert_many(payload.records)
#     return {"message": "Ingestion successful", "ingested_count": len(result.inserted_ids)}

from fastapi import APIRouter, HTTPException
from models.schemas import IngestRequest
from database import db
import logging

router = APIRouter()
logger = logging.getLogger("ingest")


@router.post("/ingest/data")
def ingest_data(payload: IngestRequest):
    # Basic validation: restrict collection names if you want
    if not payload.data_type or not isinstance(payload.records, list):
        raise HTTPException(status_code=400, detail="Invalid payload")

    collection = db[payload.data_type]
    try:
        result = collection.insert_many(payload.records)
    except Exception as e:
        logger.exception("Failed to insert records")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Ingestion successful", "ingested_count": len(result.inserted_ids)}
