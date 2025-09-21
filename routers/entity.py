# from fastapi import APIRouter
# from models.schemas import ResolveRequest

# router = APIRouter()

# @router.post("/entity/resolve")
# def resolve_entities(payload: ResolveRequest):
#     mappings = [{"party_id": pid, "canonical_id": pid, "confidence": 1.0} for pid in payload.party_ids]
#     return {"mappings": mappings}

from fastapi import APIRouter, HTTPException
from models.schemas import ResolveRequest
from database import db
from utils.gemini_client import call_gemini
import logging

router = APIRouter()
logger = logging.getLogger("entity")


@router.post("/entity/resolve")
def resolve_entities(payload: ResolveRequest):
    mappings = []
    for pid in payload.party_ids:
        # Try to find existing mapping
        existing = db.entities.find_one({"party_id": pid}, {"_id": 0})
        if existing and existing.get("canonical_id"):
            mappings.append({"party_id": pid, "canonical_id": existing["canonical_id"], "confidence": existing.get("confidence", 1.0)})
            continue

        # Fallback: ask Gemini to normalize / suggest canonical id (instruct JSON response)
        prompt = (
            "You are a data normalization assistant. Given the party identifier below, suggest a canonical ID "
            "and a confidence (0.0-1.0). Return only JSON: {\"canonical_id\":..., \"confidence\": ...}\n\nparty_id: "
            f"{pid}"
        )
        try:
            g = call_gemini(prompt)
            parsed = g.get("json")
            canonical = parsed.get("canonical_id") if parsed else pid
            confidence = float(parsed.get("confidence") if parsed and parsed.get("confidence") is not None else 1.0)
        except Exception:
            canonical = pid
            confidence = 1.0

        # persist suggestion
        db.entities.update_one({"party_id": pid}, {"$set": {"party_id": pid, "canonical_id": canonical, "confidence": confidence}}, upsert=True)
        mappings.append({"party_id": pid, "canonical_id": canonical, "confidence": confidence})

    return {"mappings": mappings}
