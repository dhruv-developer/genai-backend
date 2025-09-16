from fastapi import APIRouter
from models.schemas import IngestRequest
from database import db

router = APIRouter()

@router.post("/ingest/data")
def ingest_data(payload: IngestRequest):
    collection = db[payload.data_type]  # dynamic collection
    result = collection.insert_many(payload.records)
    return {"message": "Ingestion successful", "ingested_count": len(result.inserted_ids)}
