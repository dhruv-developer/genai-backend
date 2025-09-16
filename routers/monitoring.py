from fastapi import APIRouter

router = APIRouter()

@router.get("/monitoring/status")
def monitoring_status():
    return {
        "ingestion_lag_sec": 10,
        "feature_freshness_sec": 30,
        "alert_volume_today": 12,
        "precision_sample": 0.85,
        "model_version": "v1.0",
        "drift_metrics": {"feature_psi": 0.02, "prediction_drift": 0.01},
    }
