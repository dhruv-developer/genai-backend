from fastapi import APIRouter

router = APIRouter()

@router.post("/score/{grant_id}")
def score(grant_id: str):
    risk_score = 0.8
    risk_tier = "High"
    rule_hits = ["R1", "R3"]
    top_shap_drivers = [
        {"feature": "return_ratio", "value": 0.12, "contribution": 0.4},
        {"feature": "micro_count", "value": 3, "contribution": 0.3},
    ]
    return {
        "grant_id": grant_id,
        "risk_score": risk_score,
        "risk_tier": risk_tier,
        "rule_hits": rule_hits,
        "top_shap_drivers": top_shap_drivers,
    }
