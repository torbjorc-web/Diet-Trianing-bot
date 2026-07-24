import logging

from chatbot.engine import ConcurrentChatbot, MockAIProvider
from chatbot.logger_config import configure_logging
from chatbot.onboarding import (
    UserOnboardingProfile,
    normalize_meal_preference,
    normalize_training_setting,
)


def _ask(question: str, default: str = "") -> str:
    value = input(question).strip()
    if not value:
        return default
    return value


def _run_onboarding(user_id: str) -> UserOnboardingProfile:
    print("\nStart onboarding setup")
    full_name = _ask("Your name: ", user_id)
    goal = _ask("Goal (fat loss/muscle gain/maintenance/general fitness): ", "general fitness")
    level = _ask("Training level (beginner/intermediate/advanced): ", "beginner")
    meal_preference = _ask(
        "Meal preference (halal/kosher/vegan/vegetarian/none): ",
        "none",
    )
    weight_raw = _ask("Weight in kg (optional): ", "")
    health_notes = _ask("Any health issues/injuries? (optional): ", "none")
    training_setting = _ask("Training setting (studio/group/self): ", "self")

    weight_kg = None
    if weight_raw:
        try:
            weight_kg = float(weight_raw)
        except ValueError:
            weight_kg = None

    return UserOnboardingProfile(
        user_id=user_id,
        full_name=full_name,
        goal=goal.lower(),
        training_level=level.lower(),
        meal_preference=normalize_meal_preference(meal_preference),
        weight_kg=weight_kg,
        health_notes=health_notes,
        training_setting=normalize_training_setting(training_setting),
    )


def run_cli() -> None:
    configure_logging(logging.INFO)
    bot = ConcurrentChatbot(
        provider=MockAIProvider(),
        max_workers=4,
        per_request_timeout=2.0,
        retries=2,
    )

    print("Diet-Training Bot CLI")
    print("Type your request for a meal plan, training plan, or both.")
    print("Commands: 'quit', 'exit'\n")

    user_id = _ask("User id (default: cli-user): ", "cli-user")
    onboarding = _run_onboarding(user_id)
    print("\nOnboarding saved. You can now ask for plans.\n")

    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if prompt.lower() in {"quit", "exit"}:
            print("Session ended.")
            break

        prompt_with_context = (
            f"{onboarding.to_prompt_context()}\n"
            f"Current user request: {prompt}"
        )

        result = bot.process_one(user_id=onboarding.full_name, prompt=prompt_with_context)
        print("\nBot:")
        print(result.response)

        if result.error:
            print(f"[error: {result.error}]")

        print()


def main() -> None:
    run_cli()


if __name__ == "__main__":
    main()
