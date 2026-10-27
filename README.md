# Marketplace Risk Anomaly Scoring Model Service

Real-time statistical and machine learning anomaly detection engine for the **Marketplace Seller Risk & Abuse Detection Platform**.

---

## 🔗 Platform Repositories

| Repository | GitHub Link | Purpose & Tech Stack |
| :--- | :--- | :--- |
| **Platform & Infrastructure** | [nagaraj602/marketplace-risk-platform](https://github.com/nagaraj602/marketplace-risk-platform.git) | Terraform AWS IaC (VPC, EKS 1.37, RDS PostgreSQL 17, Redis 7.4, Jenkins), DB init scripts, Docker Compose |
| **Core Risk Backend** | [nagaraj602/marketplace-risk-backend](https://github.com/nagaraj602/marketplace-risk-backend.git) | Java 25 LTS, Spring Boot 4.1.2, JPA, Velocity Rule Engine, Risk Aggregation, Enforcement Orchestration |
| **ML Anomaly Model** | [nagaraj602/marketplace-risk-anomaly-model](https://github.com/nagaraj602/marketplace-risk-anomaly-model.git) | Python 3.15.2, FastAPI 0.162, scikit-learn 1.9.1 Isolation Forest, behavioral anomaly inference |
| **Trust & Safety Portal** | [nagaraj602/marketplace-risk-frontend](https://github.com/nagaraj602/marketplace-risk-frontend.git) | React 19, Vite 8, Node 24, Express 5, Lucide-React, live review queue & signal injection simulator |
| **Jenkins Shared Libraries** | [nagaraj602/jenkins-sharedlibraries](https://github.com/nagaraj602/jenkins-sharedlibraries.git) | Reusable Groovy pipeline vars (`trivyScan`, `sonarAnalysis`, `dockerECRImagePush`, `kubernetesEKSHelmDeployEnv`) |

---

## 🚀 Tech Stack
- **Python**: 3.15.2 (Base image: `python:3.15.2-slim`)
- **Framework**: FastAPI + Uvicorn
- **Machine Learning**: `scikit-learn` (IsolationForest), `numpy`, `pydantic` v2
- **Orchestration**: Kubernetes + Helm (with HPA autoscaling)
- **CI/CD**: Jenkins Multibranch Pipelines with SonarQube & Trivy Quality Gates

---

## ⚙️ Prerequisites

Before setting up the ML Anomaly Model service, verify the following prerequisites:
- **Python 3.15.2+**: Runtimes and headers (`python3 --version`)
- **Python venv & pip**: Standard virtual environment and package tools (`python3 -m pip --version`)
- **Docker Engine 24.0+**: (Optional for local script execution; required for containerized builds)
- **Port Availability**: Port `5000` available on localhost

---

## 🛠️ How to Setup & Run

### Local Execution
```bash
# 1. Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run automated tests
python3 -m unittest discover tests

# 4. Start API server on port 5000
python3 app.py
```

### Docker Execution
```bash
docker build -t marketplace-risk-anomaly-model:latest .
docker run -p 5000:5000 marketplace-risk-anomaly-model:latest
```

---

## 🎮 How to Operate the Anomaly Model

### 1. Health Probe
```bash
curl http://localhost:5000/health
```

### 2. Anomaly Scoring Inference (`/score`)
```bash
curl -X POST http://localhost:5000/score \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": "seller_test_99",
    "account_age_days": 2,
    "listings_last_hour": 80,
    "unique_devices_count": 4,
    "distinct_ip_count": 5,
    "payout_account_changed_recently": true,
    "geo_mismatch_country": true
  }'
```

### 3. Failover / Chaos Testing (`/admin/toggle-health`)
Simulates an ML pod outage to test backend circuit-breaker fallback:
```bash
curl -X POST http://localhost:5000/admin/toggle-health
```

### 4. Interactive API Documentation (Swagger)
Open [http://localhost:5000/docs](http://localhost:5000/docs) in your browser.
