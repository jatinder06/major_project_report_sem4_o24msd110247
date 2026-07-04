import os
import unittest
from unittest.mock import patch

from src.adk_agent import auth


class AuthTests(unittest.TestCase):
    def test_default_demo_users_authenticate_with_expected_roles(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ADK_DASHBOARD_USERS", None)

            admin = auth.authenticate_user("admin", "admin123")
            marketing = auth.authenticate_user("marketing", "mkt2024")
            viewer = auth.authenticate_user("viewer", "view123")

        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, auth.ROLE_DATA_SCIENTIST)
        self.assertIsNotNone(marketing)
        self.assertEqual(marketing.role, auth.ROLE_MARKETING_MANAGER)
        self.assertIsNotNone(viewer)
        self.assertEqual(viewer.role, auth.ROLE_VIEWER)

    def test_custom_dashboard_users_override_demo_credentials(self):
        with patch.dict(
            os.environ,
            {
                "ADK_DASHBOARD_USERS": (
                    "alice:secret:data_scientist,bob:pw:viewer"
                )
            },
        ):
            alice = auth.authenticate_user("alice", "secret")
            bob = auth.authenticate_user("bob", "pw")
            demo_admin = auth.authenticate_user("admin", "admin123")

        self.assertIsNotNone(alice)
        self.assertEqual(alice.role, auth.ROLE_DATA_SCIENTIST)
        self.assertIsNotNone(bob)
        self.assertEqual(bob.role, auth.ROLE_VIEWER)
        self.assertIsNone(demo_admin)

    def test_invalid_password_returns_none(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ADK_DASHBOARD_USERS", None)
            result = auth.authenticate_user("admin", "wrong")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
