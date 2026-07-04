import unittest
from unittest.mock import patch

from src.adk_agent import gemini_retry


class QuotaError(Exception):
    code = 429


class FakeModels:
    def __init__(self):
        self.calls = 0

    def generate_content(self, *, model, contents):
        self.calls += 1
        if self.calls == 1:
            raise QuotaError("quota")
        return {"model": model, "contents": contents}


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


class GeminiRetryTests(unittest.TestCase):
    def test_call_gemini_with_retry_retries_429(self):
        client = FakeClient()
        sleeps = []

        with patch.object(gemini_retry.time, "sleep", lambda seconds: sleeps.append(seconds)):
            with patch.object(gemini_retry, "_wait_for_rate_limit", lambda seconds: None):
                response = gemini_retry.call_gemini_with_retry(
                    client,
                    model="gemini-test",
                    prompt="hello",
                    retries=3,
                )

        self.assertEqual(response, {"model": "gemini-test", "contents": "hello"})
        self.assertEqual(client.models.calls, 2)
        self.assertEqual(sleeps, [1])

    def test_call_gemini_with_retry_raises_after_max_retries(self):
        class AlwaysFailModels(FakeModels):
            def generate_content(self, *, model, contents):
                self.calls += 1
                raise QuotaError("quota")

        client = FakeClient()
        client.models = AlwaysFailModels()

        with patch.object(gemini_retry.time, "sleep", lambda seconds: None):
            with patch.object(gemini_retry, "_wait_for_rate_limit", lambda seconds: None):
                with self.assertRaisesRegex(RuntimeError, "Max retries exceeded"):
                    gemini_retry.call_gemini_with_retry(
                        client,
                        "gemini-test",
                        "hello",
                        retries=2,
                    )


if __name__ == "__main__":
    unittest.main()
