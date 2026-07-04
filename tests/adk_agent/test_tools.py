import unittest
from unittest.mock import patch

from src.adk_agent.tools import churn_tools
from src.adk_agent.tools import content_tools
from src.adk_agent.tools import recommendation_tools
from src.adk_agent.tools import segmentation_tools
from src.adk_agent.tools import sentiment_tools
from src.adk_agent.tools import support_tools


class ToolWrapperTests(unittest.TestCase):
    def test_analyze_sentiment_calls_model_server_and_shapes_response(self):
        fake_response = {
            "label": "positive",
            "confidence": 0.98765,
            "scores": {"negative": 0.01, "neutral": 0.02, "positive": 0.97},
        }

        with patch.object(sentiment_tools, "predict", return_value=fake_response) as predict:
            result = sentiment_tools.analyze_sentiment("  Great product  ")

        predict.assert_called_once_with("/predict/sentiment", {"text": "Great product"})
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["label"], "positive")
        self.assertEqual(result["confidence"], 0.9877)
        self.assertEqual(result["model"], "distilbert-sentiment-finetuned")

    def test_analyze_sentiment_batch_filters_empty_reviews(self):
        fake_response = [
            {"label": "positive", "confidence": 0.9},
            {"label": "negative", "confidence": 0.7},
        ]

        with patch.object(sentiment_tools, "predict", return_value=fake_response) as predict:
            result = sentiment_tools.analyze_sentiment_batch([" Good ", "", "Bad"])

        predict.assert_called_once_with(
            "/predict/sentiment/batch",
            {"texts": ["Good", "Bad"]},
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_analyzed"], 2)
        self.assertEqual(result["distribution"]["positive"], 1)
        self.assertEqual(result["distribution"]["negative"], 1)

    def test_churn_xgboost_tool_builds_structured_payload(self):
        fake_response = {"risk": "HIGH_RISK", "churn_probability": 0.8123}

        with patch.object(churn_tools, "predict", return_value=fake_response) as predict:
            result = churn_tools.predict_churn_xgboost(
                tenure=2,
                monthly_charges=89.5,
                total_charges=179.0,
                contract="Month-to-month",
                internet_service="Fiber optic",
                payment_method="Electronic check",
            )

        endpoint, payload = predict.call_args.args
        self.assertEqual(endpoint, "/predict/churn_xgboost")
        self.assertEqual(payload["tenure"], 2)
        self.assertEqual(payload["monthly_charges"], 89.5)
        self.assertEqual(payload["contract"], "Month-to-month")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["risk"], "HIGH_RISK")
        self.assertEqual(result["model"], "xgboost-churn-optuna")

    def test_llm_tool_wrappers_return_success_fields(self):
        cases = [
            (
                churn_tools,
                "predict_churn_llm",
                "/predict/churn_llm",
                {"success": True, "risk": "LOW_RISK", "schema_valid": True},
                "risk",
                "LOW_RISK",
            ),
            (
                segmentation_tools,
                "segment_customer",
                "/predict/segmentation",
                {"success": True, "segment": "Champions", "schema_valid": True},
                "segment",
                "Champions",
            ),
            (
                support_tools,
                "classify_support_intent",
                "/predict/support",
                {"success": True, "intent": "BILLING", "schema_valid": True},
                "intent",
                "BILLING",
            ),
            (
                content_tools,
                "recommend_content_strategy",
                "/predict/content",
                {
                    "success": True,
                    "strategy": "LOYALTY_UPSELL",
                    "schema_valid": True,
                },
                "strategy",
                "LOYALTY_UPSELL",
            ),
            (
                recommendation_tools,
                "recommend_product_action",
                "/predict/recommendation",
                {"success": True, "action": "RECOMMEND", "schema_valid": True},
                "action",
                "RECOMMEND",
            ),
        ]

        for module, func_name, endpoint, response, output_key, expected in cases:
            with self.subTest(func_name=func_name):
                with patch.object(module, "predict", return_value=response) as predict:
                    result = getattr(module, func_name)(" customer text ")

                predict.assert_called_once_with(endpoint, {"text": "customer text"})
                self.assertEqual(result["status"], "success")
                self.assertEqual(result[output_key], expected)
                self.assertTrue(result["schema_valid"])

    def test_batch_llm_tools_calculate_distribution(self):
        with patch.object(
            segmentation_tools,
            "predict",
            return_value=[
                {"success": True, "segment": "Champions", "schema_valid": True},
                {"success": True, "segment": "At Risk", "schema_valid": True},
                {"success": False, "segment": None, "schema_valid": False},
            ],
        ) as predict:
            result = segmentation_tools.segment_customers_batch([" one ", "", "two", "three"])

        predict.assert_called_once_with(
            "/predict/segmentation/batch",
            {"texts": ["one", "two", "three"]},
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_processed"], 3)
        self.assertEqual(result["successful"], 2)
        self.assertEqual(result["distribution"], {"Champions": 1, "At Risk": 1})

        with patch.object(
            recommendation_tools,
            "predict",
            return_value=[
                {"success": True, "action": "RECOMMEND", "schema_valid": True},
                {"success": True, "action": "CONSIDER", "schema_valid": True},
            ],
        ) as predict:
            result = recommendation_tools.recommend_product_actions_batch([" good ", "ok"])

        predict.assert_called_once_with(
            "/predict/recommendation/batch",
            {"texts": ["good", "ok"]},
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["distribution"], {"RECOMMEND": 1, "CONSIDER": 1})

    def test_empty_inputs_return_validation_errors_without_server_call(self):
        checks = [
            (sentiment_tools, "analyze_sentiment", ""),
            (churn_tools, "predict_churn_llm", ""),
            (segmentation_tools, "segment_customer", "   "),
            (support_tools, "classify_support_intent", ""),
            (content_tools, "recommend_content_strategy", ""),
            (recommendation_tools, "recommend_product_action", ""),
        ]

        for module, func_name, value in checks:
            with self.subTest(func_name=func_name):
                with patch.object(module, "predict") as predict:
                    result = getattr(module, func_name)(value)

                predict.assert_not_called()
                self.assertEqual(result["status"], "error")
                self.assertIn("empty", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
