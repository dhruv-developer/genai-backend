# from fastapi import APIRouter

# router = APIRouter()

# @router.post("/score/{grant_id}")
# def score(grant_id: str):
#     risk_score = 0.8
#     risk_tier = "High"
#     rule_hits = ["R1", "R3"]
#     top_shap_drivers = [
#         {"feature": "return_ratio", "value": 0.12, "contribution": 0.4},
#         {"feature": "micro_count", "value": 3, "contribution": 0.3},
#     ]
#     return {
#         "grant_id": grant_id,
#         "risk_score": risk_score,
#         "risk_tier": risk_tier,
#         "rule_hits": rule_hits,
#         "top_shap_drivers": top_shap_drivers,
#     }

from fastapi import APIRouter, HTTPException
from database import db
from utils.gemini_client import call_gemini
import logging

router = APIRouter()
logger = logging.getLogger("score")


@router.post("/score/{grant_id}")
def score(grant_id: str):
    # load features and rule eval
    fdoc = db.features.find_one({"grant_id": grant_id}, {"_id": 0})
    if not fdoc:
        raise HTTPException(status_code=404, detail="No features found; compute features first")

    features = fdoc.get("features", {})

    # Very simple scoring function: normalized weighted sum (ensure bounded 0..1)
    # We pick a handful of features and normalize by sensible caps
    def _norm(v, cap):
        try:
            return min(max(float(v) / float(cap), 0.0), 1.0)
        except Exception:
            return 0.0

    score = 0.0
    score += _norm(features.get("return_ratio", 0), 5.0) * 0.4
    score += _norm(features.get("micro_count", 0), 50) * 0.2
    score += _norm(features.get("burstiness", 0), 3.0) * 0.2
    score += _norm(features.get("fragmentation_index", 0), 1.0) * 0.1
    score += _norm(features.get("conduit_entropy", 0), 5.0) * 0.1

    # clamp
    risk_score = min(max(score, 0.0), 1.0)

    # risk tier
    if risk_score >= 0.75:
        risk_tier = "High"
    elif risk_score >= 0.4:
        risk_tier = "Medium"
    else:
        risk_tier = "Low"

    # ask Gemini to produce top shap-like drivers in JSON
    prompt = (
        "You are an AML assistant. Given the following computed numeric features, return a JSON object\n"
        "with a key 'top_shap_drivers' which is a list of up to 4 objects with keys: feature, value, contribution (0..1).\n"
        "Return only JSON (no markdown). Features:\n\n"
        f"{features}\n\n"
        "Compute contributions proportionally to the absolute normalized influence (explainable), sum of contributions should be <= 1.0."
    )

    try:
        g = call_gemini(prompt)
    except Exception as e:
        logger.exception("Gemini failed")
        # fallback: craft drivers deterministically
        top_shap_drivers = [
            {"feature": "return_ratio", "value": features.get("return_ratio"), "contribution": 0.4},
            {"feature": "micro_count", "value": features.get("micro_count"), "contribution": 0.2},
            {"feature": "burstiness", "value": features.get("burstiness"), "contribution": 0.2},
        ]
    else:
        parsed = g.get("json")
        if parsed and isinstance(parsed, dict) and parsed.get("top_shap_drivers"):
            top_shap_drivers = parsed["top_shap_drivers"]
        else:
            # attempt to extract from text by searching for "top_shap_drivers"
            text = g.get("text") or ""
            # fallback deterministic
            top_shap_drivers = [
                {"feature": "return_ratio", "value": features.get("return_ratio"), "contribution": 0.4},
                {"feature": "micro_count", "value": features.get("micro_count"), "contribution": 0.2},
                {"feature": "burstiness", "value": features.get("burstiness"), "contribution": 0.2},
            ]

    result = {
        "grant_id": grant_id,
        "risk_score": round(risk_score, 4),
        "risk_tier": risk_tier,
        "rule_hits": db.rules_eval.find_one({"grant_id": grant_id}, {"_id": 0}) or {},
        "top_shap_drivers": top_shap_drivers,
    }

    # persist
    db.scores.update_one({"grant_id": grant_id}, {"$set": result}, upsert=True)
    return result
