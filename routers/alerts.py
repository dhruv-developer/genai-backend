# from fastapi import APIRouter, Body
# from database import db
# from datetime import datetime

# router = APIRouter()

# @router.get("/alerts/today")
# def get_alerts(limit: int = 50):
#     alerts = [
#         {
#             "grant_id": "G123",
#             "risk_score": 0.9,
#             "risk_tier": "High",
#             "rule_hits": ["R1", "R2"],
#             "timestamp": datetime.utcnow().isoformat(),
#         }
#     ]
#     return {"alerts": alerts[:limit]}

# @router.get("/alerts/{grant_id}")
# def get_alert(grant_id: str):
#     return {
#         "grant_id": grant_id,
#         "risk_score": 0.85,
#         "risk_tier": "High",
#         "rule_hits": ["R1"],
#         "computed_features": {"return_ratio": 0.12},
#         "timeline": [{"date": "2025-09-16", "event": "Transaction", "amount": 500}],
#         "subgraph": {
#             "nodes": [{"id": "P1", "label": "Party", "amount": 500}],
#             "edges": [{"source": "P1", "target": "P2", "amount": 500}],
#         },
#         "top_shap_drivers": [{"feature": "burstiness", "value": 0.7, "contribution": 0.25}],
#     }

# @router.post("/alerts/triage/{grant_id}")
# def triage_alert(grant_id: str, disposition: str = Body(...), analyst_notes: str = Body(...)):
#     db.triage.update_one(
#         {"grant_id": grant_id},
#         {"$set": {"disposition": disposition, "analyst_notes": analyst_notes, "ts": datetime.utcnow()}},
#         upsert=True,
#     )
#     return {"message": "Disposition updated"}


from fastapi import APIRouter, HTTPException, Body
from database import db
from datetime import datetime
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger("alerts")


@router.get("/alerts/today")
def get_alerts(limit: int = 50):
    limit = min(limit, 200)
    # query recent alerts collection
    results = list(db.alerts.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return {"alerts": results}


@router.get("/alerts/{grant_id}")
def get_alert(grant_id: str):
    # first, try to find a stored alert
    doc = db.alerts.find_one({"grant_id": grant_id}, {"_id": 0})
    if doc:
        return doc

    # else, derive alert from stored computed score/features
    score_doc = db.scores.find_one({"grant_id": grant_id}, {"_id": 0})
    features_doc = db.features.find_one({"grant_id": grant_id}, {"_id": 0})

    if not score_doc and not features_doc:
        raise HTTPException(status_code=404, detail="No alert, features, or score found for this grant_id")

    # Build an alert object
    risk_score = score_doc.get("risk_score") if score_doc else 0.0
    risk_tier = score_doc.get("risk_tier") if score_doc else "Unknown"
    rule_hits = (score_doc.get("rule_hits", {}).get("triggered_rules")
                 if score_doc and isinstance(score_doc.get("rule_hits"), dict)
                 else (db.rules_eval.find_one({"grant_id": grant_id}, {"_id": 0}) or {}).get("triggered_rules", []))

    timeline = []
    # optionally construct a simple timeline from transactions
    txs = list(db.transactions.find({"grant_id": grant_id}, {"_id": 0}).sort("timestamp", -1).limit(20))
    for t in txs:
        timeline.append({"date": t.get("timestamp"), "event": t.get("direction"), "amount": t.get("amount")})

    # add computed features and a natural language justification using Gemini
    features = features_doc.get("features") if features_doc else {}

    # create a justification prompt
    from utils.gemini_client import call_gemini
    prompt = (
        "You are an AML analyst assistant. Given these features and rule hits, produce a short JSON justification for "
        "an alert containing keys: summary (string), recommended_action (string), severity_explanation (string).\n\n"
        f"features: {features}\nrule_hits: {rule_hits}\n\nReturn only JSON."
    )
    try:
        g = call_gemini(prompt)
        justification = g.get("json") or {"summary": g.get("text", "")}
    except Exception:
        justification = {"summary": "Could not generate explanation", "recommended_action": "Investigate", "severity_explanation": ""}

    alert_obj = {
        "grant_id": grant_id,
        "risk_score": risk_score,
        "risk_tier": risk_tier,
        "rule_hits": rule_hits,
        "computed_features": features,
        "timeline": timeline,
        "justification": justification,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # persist the generated alert for future fast retrieval
    db.alerts.update_one({"grant_id": grant_id}, {"$set": alert_obj}, upsert=True)

    return alert_obj


@router.post("/alerts/triage/{grant_id}")
def triage_alert(grant_id: str, disposition: str = Body(...), analyst_notes: str = Body(None)):
    doc = {
        "grant_id": grant_id,
        "disposition": disposition,
        "analyst_notes": analyst_notes,
        "ts": datetime.utcnow().isoformat(),
    }
    db.triage.update_one({"grant_id": grant_id}, {"$set": doc}, upsert=True)
    return {"message": "Disposition updated", "triage": doc}
