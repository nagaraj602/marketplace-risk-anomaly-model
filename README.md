# Marketplace Risk Anomaly Scoring Model Service

Real-time statistical and machine learning anomaly detection engine for the **Marketplace Seller Risk & Abuse Detection Platform**.

## 🚀 Tech Stack
- **Python**: 3.12 (Base image: `python:3.12-slim-bookworm`)
- **Framework**: FastAPI + Uvicorn
- **Machine Learning**: `scikit-learn` (IsolationForest), `numpy`, `pydantic` v2
- **Orchestration**: Kubernetes + Helm (with HPA autoscaling)
- **CI/CD**: Jenkins Multibranch Pipelines with SonarQube & Trivy Quality Gates

## 📡 API Endpoints
- `GET /health`: Liveness and readiness probe for Kubernetes
- `POST /score`: Real-time risk evaluation of seller activity signals
- `POST /batch-score`: High-throughput batch anomaly scoring
- `POST /admin/toggle-health`: Chaos engineering & simulated failover toggle
- `GET /admin/status`: Model telemetry and active feature weights

## 🧪 Local Testing & Verification
```bash
python3 -m unittest discover tests
```

## 🐳 Docker Multi-Stage Build
```bash
docker build -t marketplace-risk-anomaly-model:latest .
docker run -p 5000:5000 marketplace-risk-anomaly-model:latest
```
