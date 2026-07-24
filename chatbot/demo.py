import logging

from chatbot.engine import ConcurrentChatbot, MockAIProvider
from chatbot.logger_config import configure_logging


def main() -> None:
    configure_logging(logging.INFO)

    bot = ConcurrentChatbot(
        provider=MockAIProvider(),
        max_workers=5,
        per_request_timeout=1.0,
        retries=2,
    )

    requests = [
        ("alice", "Can you make a vegetarian meal plan for fat loss?"),
        ("bob", "I need a 4 day intermediate training plan for muscle gain"),
        (
            "carl",
            "Please make both meal and training plan for muscle gain with high protein",
        ),
        ("charlie", "fail this request to test retries"),
        ("diana", ""),
        ("eve", "please timeout this request"),
    ]

    results = bot.process_batch(requests)

    print("\n=== Demo Results ===")
    for user_id, result in results.items():
        status = "OK" if result.success else "FAILED"
        print(f"[{status}] user={user_id} attempts={result.attempts}")
        print(f"  prompt:   {result.prompt!r}")
        print(f"  response: {result.response}")
        if result.error:
            print(f"  error:    {result.error}")


if __name__ == "__main__":
    main()
