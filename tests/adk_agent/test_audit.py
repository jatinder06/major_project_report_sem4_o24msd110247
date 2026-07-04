import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.adk_agent import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        audit._audit_log.clear()

    def tearDown(self):
        audit._audit_log.clear()

    def test_audit_log_is_reloaded_from_jsonl_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_file = Path(tmpdir) / "adk_audit.log"
            with patch.object(audit, "_AUDIT_FILE", audit_file):
                audit.log_audit_event(
                    action="dashboard_login",
                    user_id="alice",
                    role="data_scientist",
                    metadata={"source": "unit-test"},
                )
                audit._audit_log.clear()

                records = audit.get_audit_log()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["action"], "dashboard_login")
        self.assertEqual(records[0]["user_id"], "alice")
        self.assertEqual(records[0]["metadata"], {"source": "unit-test"})

    def test_clear_audit_log_clears_memory_and_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_file = Path(tmpdir) / "adk_audit.log"
            with patch.object(audit, "_AUDIT_FILE", audit_file):
                audit.log_audit_event(action="dashboard_logout", user_id="alice")
                audit.clear_audit_log()

                records = audit.get_audit_log()
                file_text = audit_file.read_text(encoding="utf-8")

        self.assertEqual(records, [])
        self.assertEqual(file_text, "")


if __name__ == "__main__":
    unittest.main()
