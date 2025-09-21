# from fastapi import APIRouter, Body
# from database import db

# router = APIRouter()

# @router.post("/features/{grant_id}")
# def compute_features(grant_id: str, theta_micro: float = 0.005, windows: list[int] = Body([7, 30, 90])):
#     features = {
#         "return_ratio": 0.12,
#         "micro_count": 3,
#         "fragmentation_index": 0.4,
#         "latency_first_inflow_d": 15,
#         "twohop_amount_capped": 1000,
#         "relationship_overlap": 2,
#         "burstiness": 0.7,
#         "conduit_entropy": 0.3,
#         "cycle_count": 1,
#     }
#     db.features.update_one({"grant_id": grant_id}, {"$set": {"features": features}}, upsert=True)
#     return {"grant_id": grant_id, "computed_features": features}

# @router.get("/features/{grant_id}")
# def get_features(grant_id: str):
#     doc = db.features.find_one({"grant_id": grant_id}, {"_id": 0})
#     return doc or {"grant_id": grant_id, "features": {}}

from fastapi import APIRouter, Body, HTTPException
from models.schemas import FeatureComputeRequest, FeatureRequest
from database import db
from datetime import datetime
from utils.gemini_client import call_gemini
from typing import List
import logging
import math

router = APIRouter()
logger = logging.getLogger("features")


def _compute_basic_features_from_transactions(transactions: List[dict]) -> dict:
    """
    Compute a conservative set of features from transactions list.
    Each txn is expected to have: {grant_id, amount, direction: 'in'|'out', timestamp, counterparty}
    Function returns numeric features.
    """
    if not transactions:
        return {
            "return_ratio": 0.0,
            "micro_count": 0,
            "fragmentation_index": 0.0,
            "latency_first_inflow_d": None,
            "twohop_amount_capped": 0,
            "relationship_overlap": 0,
            "burstiness": 0.0,
            "conduit_entropy": 0.0,
            "cycle_count": 0,
            "tx_count": 0,
        }

    # normalize transactions
    inflows = [t for t in transactions if t.get("direction") == "in"]
    outflows = [t for t in transactions if t.get("direction") == "out"]
    amounts_in = [abs(float(t.get("amount", 0))) for t in inflows]
    amounts_out = [abs(float(t.get("amount", 0))) for t in outflows]

    sum_in = sum(amounts_in) if amounts_in else 0.0
    sum_out = sum(amounts_out) if amounts_out else 0.0
    return_ratio = (sum_out / sum_in) if sum_in > 0 else 0.0

    # micro_count: number of inflows under a micro threshold (e.g., 1000)
    micro_threshold = 1000
    micro_count = sum(1 for a in amounts_in if a < micro_threshold)

    # fragmentation_index: unique counterparties / total inflows (higher -> more fragmented)
    counterparties = [t.get("counterparty") for t in inflows if t.get("counterparty")]
    unique_counterparties = len(set(counterparties))
    total_inflows = len(inflows) or 1
    fragmentation_index = unique_counterparties / total_inflows

    # latency_first_inflow_d: days between grant creation (if present) and first inflow timestamp
    timestamps = sorted([t.get("timestamp") for t in transactions if t.get("timestamp")])
    try:
        # timestamp strings -> parse as ISO
        ts_parsed = [datetime.fromisoformat(str(ts)) for ts in timestamps]
        latency_first_inflow_d = (ts_parsed[0] - ts_parsed[0]).days if ts_parsed else 0
    except Exception:
        latency_first_inflow_d = None

    # twohop_amount_capped: approximate by summing inflows capped at a threshold
    cap = 10000
    twohop_amount_capped = sum(min(a, cap) for a in amounts_in)

    # relationship_overlap: count counterparties which appear in both inflows and outflows
    cp_in = set(t.get("counterparty") for t in inflows if t.get("counterparty"))
    cp_out = set(t.get("counterparty") for t in outflows if t.get("counterparty"))
    relationship_overlap = len(cp_in.intersection(cp_out))

    # burstiness: simple metric = std(dev) / mean of inflow amounts
    burstiness = 0.0
    if amounts_in:
        mean = sum(amounts_in) / len(amounts_in)
        variance = sum((x - mean) ** 2 for x in amounts_in) / len(amounts_in)
        std = math.sqrt(variance)
        burstiness = (std / mean) if mean > 0 else 0.0

    # conduit_entropy: entropy over counterparties distribution
    from collections import Counter
    import math as _math

    cnt = Counter(counterparties)
    total = sum(cnt.values()) or 1
    entropy = 0.0
    for v in cnt.values():
        p = v / total
        entropy -= p * _math.log(p + 1e-12)
    conduit_entropy = entropy

    # cycle_count: naive - repeated pairs of (from,to) or same counterparty repeated
    cycle_count = 0
    pairs = set()
    for t in transactions:
        s = (t.get("from"), t.get("to"))
        if s in pairs:
            cycle_count += 1
        else:
            pairs.add(s)

    return {
        "return_ratio": round(return_ratio, 4),
        "micro_count": int(micro_count),
        "fragmentation_index": round(fragmentation_index, 4),
        "latency_first_inflow_d": latency_first_inflow_d,
        "twohop_amount_capped": int(twohop_amount_capped),
        "relationship_overlap": int(relationship_overlap),
        "burstiness": round(burstiness, 4),
        "conduit_entropy": round(conduit_entropy, 4),
        "cycle_count": int(cycle_count),
        "tx_count": len(transactions),
    }


@router.post("/features/{grant_id}")
def compute_features(grant_id: str, payload: FeatureRequest):
    theta_micro = payload.theta_micro
    windows = payload.windows
    # fetch transactions for grant_id (expect ingest to populate a 'transactions' collection)
    try:
        tx_cursor = list(db.transactions.find({"grant_id": grant_id}))
    except Exception as e:
        logger.exception("DB error while fetching transactions")
        raise HTTPException(status_code=500, detail=str(e))

    features = _compute_basic_features_from_transactions(tx_cursor)

    # store features with timestamp
    features_doc = {
        "grant_id": grant_id,
        "computed_at": datetime.utcnow().isoformat(),
        "features": features,
        "meta": {"theta_micro": theta_micro, "windows": windows},
    }
    try:
        db.features.update_one({"grant_id": grant_id}, {"$set": features_doc}, upsert=True)
    except Exception:
        logger.exception("Failed to persist features")

    return {"grant_id": grant_id, "computed_features": features}


@router.get("/features/{grant_id}")
def get_features(grant_id: str):
    doc = db.features.find_one({"grant_id": grant_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="No features found for grant_id")
    return doc
