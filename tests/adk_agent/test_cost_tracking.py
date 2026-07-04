import unittest

from src.adk_agent.cost_tracking import (
    build_model_cost_event,
    estimate_tokens,
    gemini_equivalent_cost_usd,
    gemini_usage_from_monitoring_events,
    summarize_cost_evidence,
)


class CostTrackingTests(unittest.TestCase):
    def test_estimate_tokens_and_cost_are_positive_for_text(self):
        self.assertGreaterEqual(estimate_tokens("customer profile text"), 1)
        self.assertEqual(gemini_equivalent_cost_usd(1_000_000, 1_000_000), 0.5)

    def test_build_model_cost_event_maps_endpoint(self):
        event = build_model_cost_event(
            endpoint="/predict/segmentation",
            payload={"text": "Customer profile"},
            response={"segment": "Champions"},
            latency_ms=12.34,
            story="alpha",
            workflow_step="campaign_segmentation",
        )

        self.assertEqual(event["story"], "alpha")
        self.assertEqual(event["provider_type"], "local_slm")
        self.assertEqual(event["model_name"], "qwen2.5-0.5b-lora-segmentation")
        self.assertGreater(event["gemini_equivalent_cost_usd"], 0)

    def test_summarize_cost_evidence_compares_local_and_gemini_cost(self):
        cost_events = [
            {
                "input_tokens": 10_000,
                "output_tokens": 5_000,
                "total_tokens": 15_000,
                "gemini_equivalent_cost_usd": gemini_equivalent_cost_usd(10_000, 5_000),
            }
        ]
        monitoring_events = [
            {
                "event_type": "model_call",
                "prompt_tokens": 100_000,
                "completion_tokens": 50_000,
                "total_tokens": 150_000,
                "cached_tokens": 1_000,
            }
        ]

        summary = summarize_cost_evidence(cost_events, monitoring_events)

        self.assertEqual(summary["gemini_model_calls"], 1)
        self.assertEqual(summary["gemini_input_tokens"], 100_000)
        self.assertEqual(summary["gemini_output_tokens"], 50_000)
        self.assertEqual(summary["gemini_total_tokens"], 150_000)
        self.assertEqual(summary["gemini_cached_tokens"], 1_000)
        self.assertAlmostEqual(summary["gemini_token_cost_usd"], 0.03)
        self.assertEqual(summary["local_model_calls"], 1)
        self.assertEqual(summary["local_total_tokens"], 15_000)
        self.assertAlmostEqual(summary["local_gemini_equivalent_cost_usd"], 0.003)
        self.assertAlmostEqual(summary["total_gemini_token_cost_usd"], 0.03)
        self.assertAlmostEqual(summary["all_gemini_baseline_cost_usd"], 0.033)
        self.assertAlmostEqual(summary["estimated_api_cost_reduction_usd"], 0.003)
        self.assertAlmostEqual(summary["estimated_api_cost_reduction_pct"], 9.09)

    def test_gemini_usage_from_monitoring_events_ignores_non_model_rows(self):
        usage = gemini_usage_from_monitoring_events([
            {
                "event_type": "model_call",
                "prompt_tokens": 1_000,
                "completion_tokens": 500,
                "total_tokens": 1_500,
                "cached_tokens": 100,
            },
            {
                "event_type": "tool_call",
                "prompt_tokens": 9_999,
                "completion_tokens": 9_999,
                "total_tokens": 19_998,
            },
        ])

        self.assertEqual(usage["gemini_model_calls"], 1)
        self.assertEqual(usage["gemini_input_tokens"], 1_000)
        self.assertEqual(usage["gemini_output_tokens"], 500)
        self.assertEqual(usage["gemini_total_tokens"], 1_500)
        self.assertEqual(usage["gemini_cached_tokens"], 100)
        self.assertAlmostEqual(usage["gemini_token_cost_usd"], 0.0003)


if __name__ == "__main__":
    unittest.main()
