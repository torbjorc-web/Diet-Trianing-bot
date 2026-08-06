import concurrent.futures
import logging
import random
import time
from dataclasses import dataclass

from chatbot.planner import DietTrainingPlanner

logger = logging.getLogger(__name__)


class ChatbotError(Exception):
    """Base class for chatbot related errors."""


class ValidationError(ChatbotError):
    """Raised for invalid user inputs."""


class AIProviderError(ChatbotError):
    """Raised when the provider fails to produce an answer."""


class ProviderTimeoutError(ChatbotError):
    """Raised when the provider call exceeds the allowed timeout."""


@dataclass
class ChatResult:
    user_id: str
    prompt: str
    response: str
    success: bool
    attempts: int
    error: str | None = None


class MockAIProvider:
    """Simple stand-in for an AI model provider."""

    def __init__(self) -> None:
        self.planner = DietTrainingPlanner()

    def generate_reply(self, user_id: str, prompt: str) -> str:
        lowered = prompt.lower()

        if "error" in lowered or "fail" in lowered:
            raise AIProviderError("Transient upstream error")

        # Simulate provider latency and transient issues.
        time.sleep(random.uniform(0.1, 0.5))

        if "timeout" in lowered:
            time.sleep(2.0)

        return self.planner.build_plan(user_id=user_id, prompt=prompt)


class ConcurrentChatbot:
    def __init__(
        self,
        provider: MockAIProvider,
        max_workers: int = 4,
        per_request_timeout: float = 1.5,
        retries: int = 2,
        retry_delay_seconds: float = 0.2,
    ) -> None:
        self.provider = provider
        self.max_workers = max_workers
        self.per_request_timeout = per_request_timeout
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    def _validate(self, user_id: str, prompt: str) -> None:
        if not user_id.strip():
            raise ValidationError("user_id cannot be empty")
        if not prompt or not prompt.strip():
            raise ValidationError("prompt cannot be empty")

    def _ask_provider_with_retry(self, user_id: str, prompt: str) -> tuple[str, int]:
        attempts = 0
        for attempt in range(1, self.retries + 2):
            attempts = attempt
            try:
                logger.debug("Provider attempt %s for user '%s'", attempt, user_id)
                response = self.provider.generate_reply(user_id=user_id, prompt=prompt)
                return response, attempts
            except AIProviderError as exc:
                logger.warning(
                    "Attempt %s failed for user '%s': %s", attempt, user_id, exc
                )
                if attempt > self.retries:
                    raise
                time.sleep(self.retry_delay_seconds * attempt)
        raise AIProviderError("Unknown provider failure")

    def _ask_provider_with_retry_and_timeout(
        self, user_id: str, prompt: str
    ) -> tuple[str, int]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._ask_provider_with_retry, user_id, prompt)
            try:
                return future.result(timeout=self.per_request_timeout)
            except concurrent.futures.TimeoutError as exc:
                raise ProviderTimeoutError(
                    f"Provider timed out after {self.per_request_timeout:.2f}s"
                ) from exc

    def process_one(self, user_id: str, prompt: str) -> ChatResult:
        started = time.perf_counter()
        try:
            self._validate(user_id=user_id, prompt=prompt)
            response, attempts = self._ask_provider_with_retry_and_timeout(
                user_id=user_id, prompt=prompt
            )
            elapsed = time.perf_counter() - started
            logger.info(
                "Processed message for user '%s' in %.3fs with %s attempt(s)",
                user_id,
                elapsed,
                attempts,
            )
            return ChatResult(
                user_id=user_id,
                prompt=prompt,
                response=response,
                success=True,
                attempts=attempts,
            )
        except ValidationError as exc:
            logger.error("Validation failed for user '%s': %s", user_id, exc)
            return ChatResult(
                user_id=user_id,
                prompt=prompt,
                response="Please send a non-empty message.",
                success=False,
                attempts=0,
                error=str(exc),
            )
        except ProviderTimeoutError as exc:
            logger.error("Timeout for user '%s': %s", user_id, exc)
            return ChatResult(
                user_id=user_id,
                prompt=prompt,
                response="Your request timed out. Please try a shorter prompt.",
                success=False,
                attempts=0,
                error="Timeout",
            )
        except AIProviderError as exc:
            logger.exception("Provider permanently failed for user '%s'", user_id)
            return ChatResult(
                user_id=user_id,
                prompt=prompt,
                response=(
                    "I am having trouble reaching my planning engine right now. "
                    "Please try again in a moment."
                ),
                success=False,
                attempts=self.retries + 1,
                error=str(exc),
            )
        except Exception as exc:  # Defensive fallback for unknown failures.
            logger.exception("Unexpected error for user '%s'", user_id)
            return ChatResult(
                user_id=user_id,
                prompt=prompt,
                response="Unexpected issue occurred. Please try again.",
                success=False,
                attempts=0,
                error=f"Unexpected: {exc}",
            )

    def process_batch(self, requests: list[tuple[str, str]]) -> dict[str, ChatResult]:
        results: dict[str, ChatResult] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            future_map = {
                pool.submit(self.process_one, user_id, prompt): (user_id, prompt)
                for user_id, prompt in requests
            }

            for future, (user_id, prompt) in future_map.items():
                try:
                    result = future.result()
                    results[user_id] = result
                except Exception as exc:
                    logger.exception("Failed processing future for user '%s'", user_id)
                    results[user_id] = ChatResult(
                        user_id=user_id,
                        prompt=prompt,
                        response="Failed to process your request.",
                        success=False,
                        attempts=0,
                        error=str(exc),
                    )

        return results
