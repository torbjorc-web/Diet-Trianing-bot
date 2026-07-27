import time

import pytest

from chatbot.engine import (
    AIProviderError,
    ConcurrentChatbot,
    MockAIProvider,
    ProviderTimeoutError,
    ValidationError,
)
from tests.conftest import DeterministicProvider, FlakyProvider


class AlwaysFailingProvider:
    def __init__(self) -> None:
        self.call_count = 0

    def generate_reply(self, user_id: str, prompt: str) -> str:
        self.call_count += 1
        raise AIProviderError("Upstream is down")


class SlowProvider:
    def __init__(self, delay: float) -> None:
        self.delay = delay

    def generate_reply(self, user_id: str, prompt: str) -> str:
        time.sleep(self.delay)
        return "slow reply"


class ExplodingProvider:
    def generate_reply(self, user_id: str, prompt: str) -> str:
        raise RuntimeError("something totally unexpected")


def build_bot(provider, **overrides) -> ConcurrentChatbot:
    options = {
        "max_workers": 4,
        "per_request_timeout": 2.0,
        "retries": 2,
        "retry_delay_seconds": 0.0,
    }
    options.update(overrides)
    return ConcurrentChatbot(provider=provider, **options)


def test_successful_request_returns_plan_on_first_attempt():
    bot = build_bot(DeterministicProvider())
    result = bot.process_one(user_id="alice", prompt="meal plan for fat loss")

    assert result.success is True
    assert result.attempts == 1
    assert result.error is None
    assert "Meal plan:" in result.response


@pytest.mark.parametrize("prompt", ["", "   "])
def test_empty_prompt_is_rejected_with_fallback_message(prompt):
    bot = build_bot(DeterministicProvider())
    result = bot.process_one(user_id="alice", prompt=prompt)

    assert result.success is False
    assert result.attempts == 0
    assert result.response == "Please send a non-empty message."
    assert "prompt cannot be empty" in result.error


def test_empty_user_id_is_rejected_with_fallback_message():
    bot = build_bot(DeterministicProvider())
    result = bot.process_one(user_id="   ", prompt="meal plan")

    assert result.success is False
    assert result.response == "Please send a non-empty message."
    assert "user_id cannot be empty" in result.error


def test_validate_raises_for_invalid_input():
    bot = build_bot(DeterministicProvider())
    with pytest.raises(ValidationError):
        bot._validate(user_id="alice", prompt="")


@pytest.mark.parametrize("failures", [1, 2])
def test_transient_provider_errors_are_retried_until_success(failures):
    provider = FlakyProvider(failures=failures, reply="recovered plan")
    bot = build_bot(provider, retries=2)

    result = bot.process_one(user_id="alice", prompt="meal plan")

    assert result.success is True
    assert result.response == "recovered plan"
    assert result.attempts == failures + 1
    assert provider.call_count == failures + 1


def test_provider_is_not_retried_when_first_attempt_succeeds():
    provider = FlakyProvider(failures=0, reply="plan")
    bot = build_bot(provider, retries=2)

    bot.process_one(user_id="alice", prompt="meal plan")

    assert provider.call_count == 1


def test_retries_are_exhausted_and_fallback_message_is_returned():
    provider = AlwaysFailingProvider()
    bot = build_bot(provider, retries=2)

    result = bot.process_one(user_id="alice", prompt="meal plan")

    assert result.success is False
    assert provider.call_count == 3  # initial attempt + 2 retries
    assert result.attempts == 3
    assert "trouble reaching my planning engine" in result.response
    assert result.error == "Upstream is down"


def test_retry_count_is_configurable():
    provider = AlwaysFailingProvider()
    bot = build_bot(provider, retries=4)

    bot.process_one(user_id="alice", prompt="meal plan")

    assert provider.call_count == 5


def test_no_retries_configured_means_single_attempt():
    provider = AlwaysFailingProvider()
    bot = build_bot(provider, retries=0)

    result = bot.process_one(user_id="alice", prompt="meal plan")

    assert provider.call_count == 1
    assert result.success is False


def test_retry_delay_grows_between_attempts(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("chatbot.engine.time.sleep", sleeps.append)

    bot = build_bot(AlwaysFailingProvider(), retries=2, retry_delay_seconds=0.5)
    bot.process_one(user_id="alice", prompt="meal plan")

    assert sleeps == [0.5, 1.0]


def test_slow_provider_triggers_timeout_fallback():
    bot = build_bot(SlowProvider(delay=1.0), per_request_timeout=0.05)

    result = bot.process_one(user_id="alice", prompt="meal plan")

    assert result.success is False
    assert result.error == "Timeout"
    assert result.response == "Your request timed out. Please try a shorter prompt."


def test_timeout_error_is_raised_by_inner_helper():
    bot = build_bot(SlowProvider(delay=1.0), per_request_timeout=0.05)

    with pytest.raises(ProviderTimeoutError):
        bot._ask_provider_with_retry_and_timeout(user_id="alice", prompt="meal plan")


def test_unexpected_errors_get_a_generic_fallback():
    bot = build_bot(ExplodingProvider())

    result = bot.process_one(user_id="alice", prompt="meal plan")

    assert result.success is False
    assert result.response == "Unexpected issue occurred. Please try again."
    assert result.error.startswith("Unexpected:")


def test_batch_processes_every_user():
    bot = build_bot(DeterministicProvider())
    requests = [
        ("alice", "meal plan for fat loss"),
        ("bob", "training plan 4 days"),
        ("carol", "both meal and training plan"),
    ]

    results = bot.process_batch(requests)

    assert set(results) == {"alice", "bob", "carol"}
    assert all(result.success for result in results.values())
    assert "Meal plan:" in results["alice"].response
    assert "Training plan:" in results["bob"].response


def test_batch_isolates_failures_per_user():
    bot = build_bot(DeterministicProvider())

    results = bot.process_batch([("alice", "meal plan"), ("bob", "please fail")])

    assert results["alice"].success is True
    assert results["bob"].success is False
    assert "trouble reaching my planning engine" in results["bob"].response


def test_batch_with_no_requests_returns_empty_mapping():
    bot = build_bot(DeterministicProvider())
    assert bot.process_batch([]) == {}


def test_mock_provider_raises_on_error_keywords():
    provider = MockAIProvider()
    with pytest.raises(AIProviderError):
        provider.generate_reply(user_id="alice", prompt="please error")


def test_mock_provider_builds_a_plan_for_normal_prompts():
    provider = MockAIProvider()
    reply = provider.generate_reply(user_id="alice", prompt="meal plan for fat loss")
    assert "Meal plan:" in reply
