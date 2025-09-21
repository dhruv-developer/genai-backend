# from fastapi import APIRouter

# router = APIRouter()

# @router.get("/monitoring/status")
# def monitoring_status():
#     return {
#         "ingestion_lag_sec": 10,
#         "feature_freshness_sec": 30,
#         "alert_volume_today": 12,
#         "precision_sample": 0.85,
#         "model_version": "v1.0",
#         "drift_metrics": {"feature_psi": 0.02, "prediction_drift": 0.01},
#     }

from fastapi import APIRouter
from database import db
import logging

router = APIRouter()
logger = logging.getLogger("monitoring")


@router.get("/monitoring/status")
def monitoring_status():
    # compute simple runtime metrics
    ingestion_lag_sec = 0
    try:
        # look for latest ingestion time if a collection 'ingest_log' exists
        last = db.get_collection("ingest_log").find_one(sort=[("ts", -1)])
        if last and last.get("ts"):
            from datetime import datetime
            ingestion_lag_sec = int((datetime.utcnow() - datetime.fromisoformat(last["ts"])).total_seconds())
    except Exception:
        ingestion_lag_sec = 0

    feature_doc = db.features.find_one(sort=[("computed_at", -1)])
    feature_freshness_sec = 0
    if feature_doc and feature_doc.get("computed_at"):
        from datetime import datetime
        try:
            feature_freshness_sec = int((datetime.utcnow() - datetime.fromisoformat(feature_doc["computed_at"])).total_seconds())
        except Exception:
            feature_freshness_sec = 0

    alert_volume_today = db.alerts.count_documents({})
    model_version = "v1.0"
    drift_metrics = {"feature_psi": 0.02, "prediction_drift": 0.01}

    return {
        "ingestion_lag_sec": ingestion_lag_sec,
        "feature_freshness_sec": feature_freshness_sec,
        "alert_volume_today": alert_volume_today,
        "precision_sample": 0.85,
        "model_version": model_version,
        "drift_metrics": drift_metrics,
    }
