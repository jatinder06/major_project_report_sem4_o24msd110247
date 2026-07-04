import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.adk_agent import monitoring_store


class MonitoringStoreTests(unittest.TestCase):
    def test_monitoring_events_are_persisted_and_cleared(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            with patch.object(monitoring_store, "DEFAULT_DB_PATH", db_path):
                monitoring_store.save_monitoring_event(
                    {
                        "timestamp": "2026-06-29T00:00:00Z",
                        "event_type": "model_call",
                        "user_id": "alice",
                        "role": "data_scientist",
                        "session_id": "session-1",
                        "agent_name": "sentiment_agent",
                        "latency_ms": 12.3,
                        "total_tokens": 42,
                    }
                )

                events = monitoring_store.load_monitoring_events()

                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["event_type"], "model_call")
                self.assertEqual(events[0]["user_id"], "alice")
                self.assertEqual(events[0]["total_tokens"], 42)

                monitoring_store.clear_monitoring_events()

                self.assertEqual(monitoring_store.load_monitoring_events(), [])

    def test_demo_run_outputs_are_persisted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            with patch.object(monitoring_store, "DEFAULT_DB_PATH", db_path):
                monitoring_store.save_demo_run(
                    "alpha",
                    elapsed_seconds=2.5,
                    event_count=7,
                    outputs={"campaign": [{"Customer": "123", "Segment": "Champions"}]},
                )

                run = monitoring_store.get_demo_run("alpha")
                monitoring_store.clear_demo_run("alpha")
                cleared = monitoring_store.get_demo_run("alpha")

        self.assertIsNotNone(run)
        self.assertEqual(run["story"], "alpha")
        self.assertEqual(run["event_count"], 7)
        self.assertEqual(run["outputs"]["campaign"][0]["Segment"], "Champions")
        self.assertIsNone(cleared)

    def test_model_cost_events_are_persisted_by_story(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            with patch.object(monitoring_store, "DEFAULT_DB_PATH", db_path):
                monitoring_store.save_model_cost_event(
                    {
                        "timestamp": "2026-06-30T00:00:00Z",
                        "story": "alpha",
                        "workflow_step": "campaign_segmentation",
                        "endpoint": "/predict/segmentation",
                        "model_name": "qwen2.5-0.5b-lora-segmentation",
                        "provider_type": "local_slm",
                        "input_tokens": 100,
                        "output_tokens": 20,
                        "total_tokens": 120,
                        "latency_ms": 55.5,
                        "pricing_basis_model": "gemini-2.5-flash-lite",
                        "gemini_input_usd_per_1m": 0.10,
                        "gemini_output_usd_per_1m": 0.40,
                        "gemini_equivalent_cost_usd": 0.000018,
                        "actual_api_cost_usd": 0.0,
                    }
                )

                all_rows = monitoring_store.load_model_cost_events()
                alpha_rows = monitoring_store.load_model_cost_events(story="alpha")
                beta_rows = monitoring_store.load_model_cost_events(story="beta")
                monitoring_store.clear_model_cost_events("alpha")

                self.assertEqual(len(all_rows), 1)
                self.assertEqual(len(alpha_rows), 1)
                self.assertEqual(beta_rows, [])
                self.assertEqual(alpha_rows[0]["workflow_step"], "campaign_segmentation")
                self.assertEqual(monitoring_store.load_model_cost_events(), [])


if __name__ == "__main__":
    unittest.main()
