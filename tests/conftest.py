import importlib
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from chatbot.engine import AIProviderError
from chatbot.history_store import SqliteChatHistoryStore
from chatbot.onboarding import SqliteOnboardingStore, UserOnboardingProfile
from chatbot.planner import DietTrainingPlanner


ADMIN_VIEW_CODE = "secret-admin"


class DeterministicProvider:
    """Provider stub with the same contract as MockAIProvider but no latency.

    Keeps plan generation real while removing the random sleeps that make the
    production mock provider slow and non-deterministic under test.
    """

    def __init__(self) -> None:
        self.planner = DietTrainingPlanner()
        self.calls: list[tuple[str, str]] = []

    def generate_reply(self, user_id: str, prompt: str) -> str:
        self.calls.append((user_id, prompt))
        if "error" in prompt.lower() or "fail" in prompt.lower():
            raise AIProviderError("Transient upstream error")
        return self.planner.build_plan(user_id=user_id, prompt=prompt)


class FlakyProvider:
    """Fails the first ``failures`` calls, then succeeds."""

    def __init__(self, failures: int, reply: str = "ok") -> None:
        self.failures = failures
        self.reply = reply
        self.call_count = 0

    def generate_reply(self, user_id: str, prompt: str) -> str:
        self.call_count += 1
        if self.call_count <= self.failures:
            raise AIProviderError(f"Transient failure {self.call_count}")
        return self.reply


@dataclass
class ApiHarness:
    client: TestClient
    provider: DeterministicProvider


@pytest.fixture
def make_api(tmp_path, monkeypatch):
    """Build an isolated API app (fresh SQLite file, chosen access codes)."""
    clients: list[TestClient] = []

    def _make(invite_code: str = "", admin_code: str = "") -> ApiHarness:
        monkeypatch.setenv("CHATBOT_DB_PATH", str(tmp_path / "test.db"))
        monkeypatch.setenv("PORTAL_INVITE_CODE", invite_code)
        monkeypatch.setenv("ADMIN_VIEW_CODE", admin_code)

        module = importlib.reload(importlib.import_module("chatbot.api"))
        provider = DeterministicProvider()
        module.bot.provider = provider

        client = TestClient(module.app)
        clients.append(client)
        return ApiHarness(client=client, provider=provider)

    yield _make

    for client in clients:
        client.close()


@pytest.fixture
def api(make_api) -> ApiHarness:
    return make_api()


@pytest.fixture
def client(api) -> TestClient:
    return api.client


@pytest.fixture
def admin_client(make_api) -> TestClient:
    return make_api(admin_code=ADMIN_VIEW_CODE).client


@pytest.fixture
def history_store(tmp_path) -> SqliteChatHistoryStore:
    return SqliteChatHistoryStore(db_path=str(tmp_path / "history.db"))


@pytest.fixture
def onboarding_store(tmp_path) -> SqliteOnboardingStore:
    return SqliteOnboardingStore(db_path=str(tmp_path / "onboarding.db"))


@pytest.fixture
def planner() -> DietTrainingPlanner:
    return DietTrainingPlanner()


def make_profile(user_id: str = "alice", **overrides) -> UserOnboardingProfile:
    values = {
        "user_id": user_id,
        "full_name": "Anna Hansen",
        "goal": "fat loss",
        "training_level": "beginner",
        "meal_preference": "halal",
        "weight_kg": 78.0,
        "health_notes": "knee discomfort",
        "training_setting": "studio",
    }
    values.update(overrides)
    return UserOnboardingProfile(**values)


def onboarding_payload(user_id: str = "alice", **overrides) -> dict:
    payload = {
        "user_id": user_id,
        "full_name": "Anna Hansen",
        "goal": "Fat Loss",
        "training_level": "Beginner",
        "meal_preference": "halal",
        "weight_kg": 78,
        "health_notes": "knee discomfort",
        "training_setting": "gym",
    }
    payload.update(overrides)
    return payload
