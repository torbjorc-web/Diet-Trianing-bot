from dataclasses import asdict, dataclass
from threading import Lock
from typing import Dict


ONBOARDING_QUESTIONS = [
    {
        "id": "full_name",
        "question": "What is your name?",
    },
    {
        "id": "goal",
        "question": "What is your main goal? (fat loss, muscle gain, maintenance, general fitness)",
    },
    {
        "id": "training_level",
        "question": "What is your training level? (beginner, intermediate, advanced)",
    },
    {
        "id": "meal_preference",
        "question": "What meal preference should we follow? (halal, kosher, vegan, vegetarian, none)",
    },
    {
        "id": "weight_kg",
        "question": "What is your current weight in kg?",
    },
    {
        "id": "health_notes",
        "question": "Any health issues or injuries we should consider?",
    },
    {
        "id": "training_setting",
        "question": "How do you prefer to train? (studio, group, self)",
    },
]


@dataclass
class UserOnboardingProfile:
    user_id: str
    full_name: str
    goal: str
    training_level: str
    meal_preference: str
    weight_kg: float | None
    health_notes: str
    training_setting: str

    def to_prompt_context(self) -> str:
        weight_text = "unknown"
        if self.weight_kg is not None:
            weight_text = f"{self.weight_kg:g} kg"

        return "\n".join(
            [
                "Onboarding profile:",
                f"- Full name: {self.full_name}",
                f"- Goal: {self.goal}",
                f"- Training level: {self.training_level}",
                f"- Meal preference: {self.meal_preference}",
                f"- Weight: {weight_text}",
                f"- Health notes: {self.health_notes}",
                f"- Training setting: {self.training_setting}",
            ]
        )


class InMemoryOnboardingStore:
    """Thread-safe in-memory onboarding profile storage."""

    def __init__(self) -> None:
        self._store: Dict[str, UserOnboardingProfile] = {}
        self._lock = Lock()

    def upsert(self, profile: UserOnboardingProfile) -> None:
        with self._lock:
            self._store[profile.user_id] = profile

    def get(self, user_id: str) -> UserOnboardingProfile | None:
        with self._lock:
            return self._store.get(user_id)

    def clear(self, user_id: str) -> bool:
        with self._lock:
            existed = user_id in self._store
            self._store.pop(user_id, None)
            return existed


def normalize_training_setting(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"studio", "gym", "fitness center"}:
        return "studio"
    if lowered in {"group", "class", "team"}:
        return "group"
    return "self"


def normalize_meal_preference(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"halal", "kosher", "vegan", "vegetarian"}:
        return lowered
    if lowered in {"veg", "veggie"}:
        return "vegetarian"
    return "none"


def profile_to_dict(profile: UserOnboardingProfile) -> dict:
    return asdict(profile)
