from fastapi import APIRouter

router = APIRouter()

@router.post("/rules/{grant_id}")
def apply_rules(grant_id: str):
    triggered = ["R1", "R3"]
    signals = {
        "return_ratio": 0.12,
        "micro_count": 3,
        "twohop_amount_capped": 1000,
        "relationship_overlap": 2,
        "burstiness": 0.7,
    }
    return {"grant_id": grant_id, "triggered_rules": triggered, "signals": signals}
