"""
Marketplace Seller Risk & Abuse Detection Platform
Anomaly Scoring Service (ML & Statistical Profiler)
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import numpy as np
from sklearn.ensemble import IsolationForest
import time
import os
import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("risk-anomaly-model")

app = FastAPI(
    title="Marketplace Risk Anomaly Scoring Service",
    description="Real-time statistical and ML anomaly detection for marketplace seller abuse",
    version="2.0.0"
)

MODEL_PORT = int(os.getenv("MODEL_PORT", "5000"))
model_healthy = True

# Synthetic baseline data to prime the IsolationForest estimator
# Features: [listings_per_hr, device_count, ip_count, account_age_days, price_usd, reviews_ratio]
baseline_data = np.array([
    [2, 1, 1, 365, 45.0, 0.95],
    [5, 1, 1, 180, 60.0, 0.90],
    [1, 1, 1, 720, 25.0, 0.98],
    [8, 2, 2, 90, 80.0, 0.85],
    [3, 1, 1, 400, 30.0, 0.92],
    [12, 2, 2, 60, 110.0, 0.88],
    [0, 1, 1, 30, 15.0, 1.0],
    [4, 1, 1, 500, 50.0, 0.94],
    [6, 1, 2, 120, 75.0, 0.89],
    [2, 1, 1, 250, 40.0, 0.96],
])

clf = IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
clf.fit(baseline_data)
logger.info("IsolationForest model successfully trained on baseline seller behaviors.")


class SellerSignalPayload(BaseModel):
    seller_id: str = Field(..., example="seller_847291")
    account_age_days: int = Field(default=30, ge=0)
    listings_last_hour: int = Field(default=0, ge=0)
    orders_last_hour: int = Field(default=0, ge=0)
    positive_reviews_ratio: float = Field(default=0.90, ge=0.0, le=1.0)
    unique_devices_count: int = Field(default=1, ge=1)
    distinct_ip_count: int = Field(default=1, ge=1)
    avg_listing_price_usd: float = Field(default=50.0, ge=0.0)
    payout_account_changed_recently: bool = Field(default=False)
    geo_mismatch_country: bool = Field(default=False)


class AnomalyResponse(BaseModel):
    seller_id: str
    anomaly_score: float
    confidence: str
    is_anomaly: bool
    risk_tier: str
    anomaly_flags: List[str]
    feature_contributions: Dict[str, float]
    evaluation_latency_ms: float
    model_version: str
    timestamp: str


def compute_anomaly(payload: SellerSignalPayload) -> Dict[str, Any]:
    start_time = time.perf_counter()
    flags: List[str] = []
    contributions: Dict[str, float] = {}

    score = 0.05  # Base baseline risk

    # 1. Listing Velocity Burst Check
    if payload.listings_last_hour > 50:
        flags.append("EXTREME_LISTING_VELOCITY")
        score += 0.35
        contributions["listing_velocity"] = 0.35
    elif payload.listings_last_hour > 15:
        flags.append("HIGH_LISTING_VELOCITY")
        score += 0.18
        contributions["listing_velocity"] = 0.18

    # 2. Account Age & Category Risk
    if payload.account_age_days < 7 and payload.listings_last_hour > 10:
        flags.append("NEW_ACCOUNT_LISTING_FLOOD")
        score += 0.25
        contributions["account_age_velocity"] = 0.25

    # 3. Device & Network Footprint Anomalies
    if payload.unique_devices_count >= 4 or payload.distinct_ip_count >= 5:
        flags.append("SUSPICIOUS_MULTI_DEVICE_COLLISION")
        score += 0.20
        contributions["device_ip_dispersion"] = 0.20

    # 4. Critical Account Mutex Modifications (ATO indicator)
    if payload.payout_account_changed_recently:
        flags.append("CRITICAL_PAYOUT_MODIFICATION")
        score += 0.22
        contributions["payout_change"] = 0.22

    # 5. Geolocation Divergence
    if payload.geo_mismatch_country:
        flags.append("GEOLOCATION_MISMATCH")
        score += 0.15
        contributions["geo_mismatch"] = 0.15

    # 6. Unsupervised Machine Learning Isolation Forest Score
    feature_vector = np.array([[
        payload.listings_last_hour,
        payload.unique_devices_count,
        payload.distinct_ip_count,
        payload.account_age_days,
        payload.avg_listing_price_usd,
        payload.positive_reviews_ratio
    ]])
    
    # isolation_score returns negative for anomalies, positive for normal
    raw_decision = clf.decision_function(feature_vector)[0]
    # Normalize to [0, 1] range: lower decision = higher anomaly score
    ml_anomaly_boost = max(0.0, min(0.30, (0.20 - raw_decision)))
    score += ml_anomaly_boost
    contributions["isolation_forest_boost"] = round(ml_anomaly_boost, 3)

    # Normalize bounded score [0.00, 1.00]
    final_score = round(min(1.0, max(0.0, score)), 3)

    # Determine confidence & Risk Tier
    if final_score >= 0.80:
        risk_tier = "CRITICAL"
        confidence = "high"
    elif final_score >= 0.60:
        risk_tier = "HIGH"
        confidence = "high"
    elif final_score >= 0.40:
        risk_tier = "ELEVATED"
        confidence = "medium"
    else:
        risk_tier = "LOW"
        confidence = "high" if final_score < 0.20 else "low"

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "seller_id": payload.seller_id,
        "anomaly_score": final_score,
        "confidence": confidence,
        "is_anomaly": final_score >= 0.60,
        "risk_tier": risk_tier,
        "anomaly_flags": flags,
        "feature_contributions": contributions,
        "evaluation_latency_ms": elapsed_ms,
        "model_version": "2.0.0-isolationforest",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.get("/health")
def health_check():
    if not model_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "message": "Model service marked unhealthy via admin toggle"}
        )
    return {
        "status": "healthy",
        "service": "marketplace-risk-anomaly-model",
        "model_version": "2.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.post("/score", response_model=AnomalyResponse)
def score_seller(payload: SellerSignalPayload):
    if not model_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model service temporarily unavailable for inference"
        )
    result = compute_anomaly(payload)
    logger.info(f"Evaluated seller={payload.seller_id} -> score={result['anomaly_score']} tier={result['risk_tier']}")
    return result


@app.post("/batch-score", response_model=List[AnomalyResponse])
def batch_score(payloads: List[SellerSignalPayload]):
    if not model_healthy:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model service unavailable")
    return [compute_anomaly(p) for p in payloads]


@app.post("/admin/toggle-health")
def toggle_health():
    global model_healthy
    model_healthy = not model_healthy
    new_state = "healthy" if model_healthy else "unhealthy"
    logger.warning(f"Admin simulated model health toggle: {new_state}")
    return {"message": f"Model health state changed to {new_state}", "healthy": model_healthy}


@app.get("/admin/status")
def admin_status():
    return {
        "service": "marketplace-risk-anomaly-model",
        "healthy": model_healthy,
        "version": "2.0.0",
        "framework": "FastAPI + scikit-learn",
        "algorithms": ["IsolationForest", "SlidingWindowHeuristics", "ZScoreVelocity"],
        "active_features": [
            "listings_last_hour",
            "account_age_days",
            "unique_devices_count",
            "distinct_ip_count",
            "payout_account_changed_recently",
            "geo_mismatch_country"
        ]
    }


@app.get("/")
def root():
    return {
        "service": "Marketplace Risk Anomaly Scoring API",
        "version": "2.0.0",
        "status": "healthy" if model_healthy else "unhealthy",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=MODEL_PORT, reload=False)
