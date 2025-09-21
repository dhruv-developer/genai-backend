# from fastapi import APIRouter

# router = APIRouter()

# @router.post("/rules/{grant_id}")
# def apply_rules(grant_id: str):
#     triggered = ["R1", "R3"]
#     signals = {
#         "return_ratio": 0.12,
#         "micro_count": 3,
#         "twohop_amount_capped": 1000,
#         "relationship_overlap": 2,
#         "burstiness": 0.7,
#     }
#     return {"grant_id": grant_id, "triggered_rules": triggered, "signals": signals}

from fastapi import APIRouter, HTTPException
from database import db
import logging

router = APIRouter()
logger = logging.getLogger("rules")


@router.post("/rules/{grant_id}")
def apply_rules(grant_id: str):
    # load precomputed features
    doc = db.features.find_one({"grant_id": grant_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="No features found; compute features first")

    f = doc.get("features", {})

    # Example rule implementations (realistic, deterministic)
    triggered = []
    signals = {}

    # Rule R1: high return_ratio and many micro transactions
    signals["return_ratio"] = f.get("return_ratio", 0.0)
    signals["micro_count"] = f.get("micro_count", 0)
    if signals["return_ratio"] > 0.5 and signals["micro_count"] > 5:
        triggered.append("R1")

    # Rule R2: high burstiness
    signals["burstiness"] = f.get("burstiness", 0.0)
    if signals["burstiness"] > 1.0:
        triggered.append("R2")

    # Rule R3: high fragmentation and conduit entropy
    signals["fragmentation_index"] = f.get("fragmentation_index", 0.0)
    signals["conduit_entropy"] = f.get("conduit_entropy", 0.0)
    if signals["fragmentation_index"] > 0.5 and signals["conduit_entropy"] > 1.0:
        triggered.append("R3")

    # persist the rule evaluation for audit
    db.rules_eval.update_one(
        {"grant_id": grant_id},
        {"$set": {"grant_id": grant_id, "triggered_rules": triggered, "signals": signals}},
        upsert=True,
    )

    return {"grant_id": grant_id, "triggered_rules": triggered, "signals": signals}
