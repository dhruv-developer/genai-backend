from fastapi import APIRouter, Body
from database import db
from datetime import datetime

router = APIRouter()

@router.get("/alerts/today")
def get_alerts(limit: int = 50):
    alerts = [
        {
            "grant_id": "G123",
            "risk_score": 0.9,
            "risk_tier": "High",
            "rule_hits": ["R1", "R2"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]
    return {"alerts": alerts[:limit]}

@router.get("/alerts/{grant_id}")
def get_alert(grant_id: str):
    return {
        "grant_id": grant_id,
        "risk_score": 0.85,
        "risk_tier": "High",
        "rule_hits": ["R1"],
        "computed_features": {"return_ratio": 0.12},
        "timeline": [{"date": "2025-09-16", "event": "Transaction", "amount": 500}],
        "subgraph": {
            "nodes": [{"id": "P1", "label": "Party", "amount": 500}],
            "edges": [{"source": "P1", "target": "P2", "amount": 500}],
        },
        "top_shap_drivers": [{"feature": "burstiness", "value": 0.7, "contribution": 0.25}],
    }

@router.post("/alerts/triage/{grant_id}")
def triage_alert(grant_id: str, disposition: str = Body(...), analyst_notes: str = Body(...)):
    db.triage.update_one(
        {"grant_id": grant_id},
        {"$set": {"disposition": disposition, "analyst_notes": analyst_notes, "ts": datetime.utcnow()}},
        upsert=True,
    )
    return {"message": "Disposition updated"}
