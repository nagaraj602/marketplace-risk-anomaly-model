import unittest
from fastapi.testclient import TestClient
from app import app

class TestAnomalyModel(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "marketplace-risk-anomaly-model")

    def test_score_normal_seller(self):
        payload = {
            "seller_id": "seller_normal_01",
            "account_age_days": 300,
            "listings_last_hour": 1,
            "orders_last_hour": 2,
            "positive_reviews_ratio": 0.98,
            "unique_devices_count": 1,
            "distinct_ip_count": 1,
            "avg_listing_price_usd": 45.0,
            "payout_account_changed_recently": False,
            "geo_mismatch_country": False
        }
        response = self.client.post("/score", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["seller_id"], "seller_normal_01")
        self.assertLess(data["anomaly_score"], 0.40)
        self.assertFalse(data["is_anomaly"])
        self.assertEqual(data["risk_tier"], "LOW")

    def test_score_fraudulent_burst(self):
        payload = {
            "seller_id": "seller_fraud_99",
            "account_age_days": 2,
            "listings_last_hour": 75,
            "orders_last_hour": 0,
            "positive_reviews_ratio": 0.50,
            "unique_devices_count": 5,
            "distinct_ip_count": 6,
            "avg_listing_price_usd": 1500.0,
            "payout_account_changed_recently": True,
            "geo_mismatch_country": True
        }
        response = self.client.post("/score", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["anomaly_score"], 0.70)
        self.assertTrue(data["is_anomaly"])
        self.assertIn("EXTREME_LISTING_VELOCITY", data["anomaly_flags"])
        self.assertIn("CRITICAL_PAYOUT_MODIFICATION", data["anomaly_flags"])
        self.assertIn(data["risk_tier"], ["CRITICAL", "HIGH"])

if __name__ == "__main__":
    unittest.main()
