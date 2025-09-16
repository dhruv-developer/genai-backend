from fastapi import APIRouter, Body
from database import db

router = APIRouter()

@router.post("/features/{grant_id}")
def compute_features(grant_id: str, theta_micro: float = 0.005, windows: list[int] = Body([7, 30, 90])):
    features = {
        "return_ratio": 0.12,
        "micro_count": 3,
        "fragmentation_index": 0.4,
        "latency_first_inflow_d": 15,
        "twohop_amount_capped": 1000,
        "relationship_overlap": 2,
        "burstiness": 0.7,
        "conduit_entropy": 0.3,
        "cycle_count": 1,
    }
    db.features.update_one({"grant_id": grant_id}, {"$set": {"features": features}}, upsert=True)
    return {"grant_id": grant_id, "computed_features": features}

@router.get("/features/{grant_id}")
def get_features(grant_id: str):
    doc = db.features.find_one({"grant_id": grant_id}, {"_id": 0})
    return doc or {"grant_id": grant_id, "features": {}}
