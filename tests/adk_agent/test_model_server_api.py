import importlib
import unittest
from unittest.mock import patch


try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:
    TestClient = None


class FakeTextModel:
    def __init__(self, key, value, success=True):
        self.key = key
        self.value = value
        self.success = success

    def predict(self, text):
        return {
            "success": self.success,
            self.key: self.value,
            "schema_valid": True,
            "input": text,
        }

    def predict_batch(self, texts):
        return [
            {
                "success": self.success,
                self.key: self.value,
                "schema_valid": True,
                "input": text,
            }
            for text in texts
        ]


class FakeSentimentModel:
    def predict(self, text):
        return {
            "label": "positive",
            "confidence": 0.91,
            "scores": {"negative": 0.02, "neutral": 0.07, "positive": 0.91},
            "input": text,
        }

    def predict_batch(self, texts):
        return [
            {"label": "positive", "confidence": 0.9, "scores": {}}
            for _ in texts
        ]


class FakeProbability:
    def __getitem__(self, item):
        rows, col = item
        if isinstance(rows, slice) and col == 1:
            return [0.73]
        raise IndexError(item)


class FakeChurnModel:
    def predict_proba(self, features):
        return FakeProbability()


class FakeChurnPredictor:
    label_encoders = {}
    feature_names = ["tenure"]

    class Scaler:
        feature_names_in_ = []

        def transform(self, values):
            return values

    scaler = Scaler()
    model = FakeChurnModel()


@unittest.skipIf(TestClient is None, "fastapi is not installed")
class ModelServerApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_server = importlib.import_module("src.adk_agent.model_server")
        cls.client = TestClient(cls.model_server.app)

    def setUp(self):
        self.original_models = dict(self.model_server._models)
        self.model_server._models.clear()
        self.model_server._models.update(
            {
                "sentiment": FakeSentimentModel(),
                "churn_xgb": FakeChurnPredictor(),
                "churn_llm": FakeTextModel("risk", "LOW_RISK"),
                "segmentation": FakeTextModel("segment", "Champions"),
                "support": FakeTextModel("intent", "BILLING"),
                "content": FakeTextModel("strategy", "LOYALTY_UPSELL"),
                "recommendation": FakeTextModel("action", "RECOMMEND"),
            }
        )
        self.cost_patch = patch.object(self.model_server, "save_model_cost_event")
        self.mock_save_cost_event = self.cost_patch.start()

    def tearDown(self):
        self.cost_patch.stop()
        self.model_server._models.clear()
        self.model_server._models.update(self.original_models)

    def test_health_returns_loaded_model_keys(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("sentiment", payload["models_loaded"])
        self.assertIn("churn_xgb", payload["models_loaded"])

    def test_sentiment_endpoints_call_model_cache(self):
        response = self.client.post(
            "/predict/sentiment",
            json={"text": "Great product"},
            headers={
                "X-ADK-Cost-Story": "alpha",
                "X-ADK-Cost-Workflow-Step": "risk_sentiment_watch",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["label"], "positive")
        self.assertEqual(response.json()["input"], "Great product")
        self.assertEqual(self.mock_save_cost_event.call_args.args[0]["story"], "alpha")

        response = self.client.post(
            "/predict/sentiment/batch",
            json={"texts": ["Good", "Better"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_llm_prediction_endpoints_return_fake_model_payloads(self):
        endpoints = {
            "/predict/churn_llm": ("risk", "LOW_RISK"),
            "/predict/segmentation": ("segment", "Champions"),
            "/predict/support": ("intent", "BILLING"),
            "/predict/content": ("strategy", "LOYALTY_UPSELL"),
            "/predict/recommendation": ("action", "RECOMMEND"),
        }

        for endpoint, (key, expected) in endpoints.items():
            with self.subTest(endpoint=endpoint):
                response = self.client.post(endpoint, json={"text": "customer text"})

                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["success"])
                self.assertEqual(response.json()[key], expected)

    def test_batch_llm_prediction_endpoints_return_lists(self):
        endpoints = [
            "/predict/segmentation/batch",
            "/predict/recommendation/batch",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(endpoint, json={"texts": ["one", "two"]})

                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.json()), 2)

    def test_churn_xgboost_endpoint_engineers_payload_and_returns_risk(self):
        request = {
            "tenure": 2,
            "monthly_charges": 89.5,
            "total_charges": 179.0,
            "contract": "Month-to-month",
            "internet_service": "Fiber optic",
            "payment_method": "Electronic check",
        }

        with patch.object(
            self.model_server,
            "_encode_and_scale",
            side_effect=lambda df, label_encoders, scaler: df,
        ):
            response = self.client.post("/predict/churn_xgboost", json=request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["risk"], "HIGH_RISK")
        self.assertEqual(response.json()["churn_probability"], 0.73)


if __name__ == "__main__":
    unittest.main()
