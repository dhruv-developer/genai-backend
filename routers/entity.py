from fastapi import APIRouter
from models.schemas import ResolveRequest

router = APIRouter()

@router.post("/entity/resolve")
def resolve_entities(payload: ResolveRequest):
    mappings = [{"party_id": pid, "canonical_id": pid, "confidence": 1.0} for pid in payload.party_ids]
    return {"mappings": mappings}
