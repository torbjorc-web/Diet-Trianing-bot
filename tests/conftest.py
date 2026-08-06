"""Shared test fixtures and configuration."""

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot.engine import AIProviderError, ConcurrentChatbot
from chatbot.history_store import SqliteChatHistoryStore
from chatbot.onboarding import SqliteOnboardingStore, UserOnboardingProfile
from chatbot.planner import DietTrainingPlanner
from chatbot.portal_template import get_portal_html
from chatbot.routes_admin import create_admin_router
from chatbot.routes_chat import create_chat_router
from chatbot.routes_onboarding import create_onboarding_router
from chatbot.routes_portal import create_portal_router
from chatbot.security import create_invite_code_middleware, extract_admin_code

ADMIN_VIEW_CODE = "adm-123"


class DeterministicProvider:
    """Predictable provider for deterministic tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.call_count = 0
        self.planner = DietTrainingPlanner(use_ml=False)

    def generate_reply(self, user_id: str, prompt: str) -> str:
        self.call_count += 1
        self.calls.append((user_id, prompt))
        lowered = prompt.lower()
        if "error" in lowered or "fail" in lowered:
            raise AIProviderError("Transient upstream error")
        return self.planner.build_plan(user_id=user_id, prompt=prompt)


class FlakyProvider:
    """Fails a configured number of calls before succeeding."""

    def __init__(self, failures: int = 1, reply: str = "ok") -> None:
        self.failures = failures
        self.reply = reply
        self.call_count = 0

    def generate_reply(self, user_id: str, prompt: str) -> str:
        self.call_count += 1
        if self.call_count <= self.failures:
            raise AIProviderError("Transient upstream error")
        return self.reply


@dataclass
class ApiHarness:
    app: FastAPI
    client: TestClient
    provider: DeterministicProvider
    bot: ConcurrentChatbot
    history_store: SqliteChatHistoryStore
    onboarding_store: SqliteOnboardingStore


def onboarding_payload(user_id: str = "alice", **overrides) -> dict:
    payload = {
        "user_id": user_id,
        "full_name": "Anna Hansen",
        "goal": "fat loss",
        "training_level": "beginner",
        "meal_preference": "halal",
        "weight_kg": 78,
        "health_notes": "knee discomfort",
        "training_setting": "studio",
    }
    payload.update(overrides)
    return payload


def make_profile(user_id: str = "alice", **overrides) -> UserOnboardingProfile:
    data = onboarding_payload(user_id=user_id, **overrides)
    return UserOnboardingProfile(
        user_id=data["user_id"],
        full_name=data["full_name"],
        goal=str(data["goal"]).strip().lower(),
        training_level=str(data["training_level"]).strip().lower(),
        meal_preference=data["meal_preference"],
        weight_kg=data.get("weight_kg"),
        health_notes=(str(data.get("health_notes", "none")).strip() or "none"),
        training_setting="studio"
        if str(data.get("training_setting", "self")).strip().lower()
        in {"studio", "gym", "fitness center"}
        else "group"
        if str(data.get("training_setting", "self")).strip().lower()
        in {"group", "class", "team"}
        else "self",
    )


@pytest.fixture(autouse=True)
def cleanup_feedback_files():
    """Auto-cleanup feedback files before each test."""
    # Cleanup before test
    feedback_dir = Path(__file__).parent.parent / "data" / "feedback"
    if feedback_dir.exists():
        shutil.rmtree(feedback_dir)
    
    yield
    
    # Cleanup after test
    if feedback_dir.exists():
        shutil.rmtree(feedback_dir)


@pytest.fixture
def temp_model_dir():
    """Create temporary directory for test models."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_feedback_dir():
    """Create temporary directory for feedback files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_training_data():
    """Sample training data for classifiers."""
    return {
        "goal": [
            ("I want to lose weight fast", "fat loss"),
            ("help me burn fat", "fat loss"),
            ("I need to get lean", "fat loss"),
            ("build muscle and get strong", "muscle gain"),
            ("increase muscle mass", "muscle gain"),
            ("stay at same weight", "maintenance"),
            ("general fitness routine", "general fitness"),
        ],
        "diet_style": [
            ("I eat balanced meals", "balanced"),
            ("I'm vegetarian", "vegetarian"),
            ("I'm vegan no animal products", "vegan"),
            ("low carb diet", "low-carb"),
            ("high protein meals", "high-protein"),
        ],
        "training_level": [
            ("I'm a beginner", "beginner"),
            ("I've worked out before", "intermediate"),
            ("I'm very experienced", "advanced"),
        ],
    }


@pytest.fixture
def sample_feedback_data():
    """Sample feedback data for testing feedback collection."""
    from datetime import datetime, timezone
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": "test_user",
        "prompt": "lose weight, vegan, beginner",
        "detected_goal": "fat loss",
        "user_goal": None,
        "detected_diet_style": "vegan",
        "user_diet_style": None,
        "detected_training_level": "beginner",
        "user_training_level": None,
        "plan_quality": 5,
        "specific_feedback": "Great plan!",
        "helpful": True,
    }


@pytest.fixture
def planner():
    return DietTrainingPlanner(use_ml=False)


@pytest.fixture
def history_store(tmp_path):
    return SqliteChatHistoryStore(db_path=str(tmp_path / "history.db"))


@pytest.fixture
def onboarding_store(tmp_path):
    return SqliteOnboardingStore(db_path=str(tmp_path / "onboarding.db"))


@pytest.fixture
def make_api(tmp_path):
    def _build(invite_code: str = "", admin_view_code: str = "") -> ApiHarness:
        provider = DeterministicProvider()
        bot = ConcurrentChatbot(
            provider=provider,
            max_workers=4,
            per_request_timeout=1.0,
            retries=2,
            retry_delay_seconds=0.0,
        )
        db_path = str(tmp_path / "chatbot.db")
        history = SqliteChatHistoryStore(db_path=db_path)
        onboarding = SqliteOnboardingStore(db_path=db_path)

        app = FastAPI(title="Diet-Training Bot API", version="test")
        app.middleware("http")(create_invite_code_middleware(invite_code))

        @app.get("/health")
        def health() -> dict[str, str]:
            return {"status": "ok"}

        app.include_router(create_portal_router(portal_html=get_portal_html()))
        app.include_router(
            create_admin_router(
                history_store=history,
                onboarding_store=onboarding,
                admin_view_code=admin_view_code,
                extract_admin_code=extract_admin_code,
            )
        )
        app.include_router(create_onboarding_router(onboarding_store=onboarding))
        app.include_router(
            create_chat_router(
                bot=bot,
                history_store=history,
                onboarding_store=onboarding,
            )
        )

        client = TestClient(app)
        return ApiHarness(
            app=app,
            client=client,
            provider=provider,
            bot=bot,
            history_store=history,
            onboarding_store=onboarding,
        )

    return _build


@pytest.fixture
def api(make_api) -> ApiHarness:
    return make_api()


@pytest.fixture
def client(api):
    return api.client


@pytest.fixture
def admin_client(make_api):
    return make_api(admin_view_code=ADMIN_VIEW_CODE).client

