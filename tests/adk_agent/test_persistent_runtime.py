import asyncio
import os
import sys
import types
import unittest
from unittest.mock import patch

from src.adk_agent import persistent_runtime


class FakeSession:
    def __init__(self, state=None):
        self.state = state or {}


class FakeDatabaseSessionService:
    def __init__(self, db_url):
        self.db_url = db_url
        self.sessions = {}
        self.updated_sessions = []

    async def get_session(self, *, app_name, user_id, session_id):
        return self.sessions.get((app_name, user_id, session_id))

    async def create_session(self, *, app_name, user_id, session_id, state=None):
        session = FakeSession(state=state)
        self.sessions[(app_name, user_id, session_id)] = session
        return session

    def update_session(self, session):
        self.updated_sessions.append(session)


class FakeRunner:
    def __init__(self, *, agent, app_name, session_service):
        self.agent = agent
        self.app_name = app_name
        self.session_service = session_service


class FakeInMemoryRunner:
    def __init__(self, *, agent, app_name):
        self.agent = agent
        self.app_name = app_name
        self.session_service = FakeDatabaseSessionService("memory://")


class PersistentRuntimeTests(unittest.TestCase):
    def fake_adk_modules(self, database_service_cls=FakeDatabaseSessionService):
        google_module = types.ModuleType("google")
        adk_module = types.ModuleType("google.adk")
        runners_module = types.ModuleType("google.adk.runners")
        sessions_module = types.ModuleType("google.adk.sessions")

        runners_module.Runner = FakeRunner
        runners_module.InMemoryRunner = FakeInMemoryRunner
        sessions_module.DatabaseSessionService = database_service_cls

        return {
            "google": google_module,
            "google.adk": adk_module,
            "google.adk.runners": runners_module,
            "google.adk.sessions": sessions_module,
        }

    def runtime_status_patch(self):
        return patch.object(
            persistent_runtime,
            "_LAST_RUNTIME_STATUS",
            {
                "persistent": False,
                "service": "not_initialized",
                "db_url": None,
                "error": None,
            },
        )

    def test_create_persistent_runner_uses_database_session_service(self):
        db_url = "sqlite:///tmp/unit-test-sessions.db"

        with patch.dict(sys.modules, self.fake_adk_modules()):
            with self.runtime_status_patch():
                with patch.dict(os.environ, {"ADK_SESSION_DB_URL": db_url}):
                    runner = persistent_runtime.create_persistent_runner(
                        agent=object(),
                        app_name="test_app",
                    )

                status = persistent_runtime.get_runtime_status()

        self.assertIsInstance(runner, FakeRunner)
        self.assertEqual(runner.session_service.db_url, db_url)
        self.assertTrue(status["persistent"])
        self.assertEqual(status["service"], "DatabaseSessionService")

    def test_create_persistent_runner_reports_in_memory_fallback(self):
        class BrokenDatabaseSessionService:
            def __init__(self, db_url):
                raise RuntimeError("database unavailable")

        with patch.dict(
            sys.modules,
            self.fake_adk_modules(database_service_cls=BrokenDatabaseSessionService),
        ):
            with self.runtime_status_patch():
                runner = persistent_runtime.create_persistent_runner(
                    agent=object(),
                    app_name="test_app",
                )
                status = persistent_runtime.get_runtime_status()

        self.assertIsInstance(runner, FakeInMemoryRunner)
        self.assertFalse(status["persistent"])
        self.assertEqual(status["service"], "InMemoryRunner")
        self.assertIn("database unavailable", status["error"])

    def test_get_or_create_session_creates_identity_state(self):
        with patch.dict(sys.modules, self.fake_adk_modules()):
            runner = persistent_runtime.create_persistent_runner(
                agent=object(),
                app_name="test_app",
            )

            session = asyncio.run(
                persistent_runtime.get_or_create_session(
                    runner,
                    user_id="alice",
                    session_id="session-1",
                    role="data_scientist",
                    extra_state={"project": "msc"},
                )
            )

        self.assertEqual(session.state["adk.user_id"], "alice")
        self.assertEqual(session.state["adk.role"], "data_scientist")
        self.assertEqual(session.state["adk.session_id"], "session-1")
        self.assertEqual(session.state["project"], "msc")

    def test_get_or_create_session_backfills_existing_session_identity(self):
        with patch.dict(sys.modules, self.fake_adk_modules()):
            runner = persistent_runtime.create_persistent_runner(
                agent=object(),
                app_name="test_app",
            )
            existing = FakeSession(state={})
            runner.session_service.sessions[("test_app", "alice", "session-1")] = existing

            session = asyncio.run(
                persistent_runtime.get_or_create_session(
                    runner,
                    user_id="alice",
                    session_id="session-1",
                    role="data_scientist",
                )
            )

        self.assertIs(session, existing)
        self.assertEqual(session.state["adk.user_id"], "alice")
        self.assertEqual(session.state["adk.role"], "data_scientist")
        self.assertEqual(runner.session_service.updated_sessions, [existing])


if __name__ == "__main__":
    unittest.main()
