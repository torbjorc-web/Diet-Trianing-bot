import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock

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
        self._store: dict[str, UserOnboardingProfile] = {}
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


class SqliteOnboardingStore:
    """Thread-safe SQLite-backed onboarding profile storage."""

    def __init__(self, db_path: str) -> None:
        self._lock = Lock()
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS onboarding_profiles (
                user_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                goal TEXT NOT NULL,
                training_level TEXT NOT NULL,
                meal_preference TEXT NOT NULL,
                weight_kg REAL,
                health_notes TEXT NOT NULL,
                training_setting TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.commit()

    def upsert(self, profile: UserOnboardingProfile) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO onboarding_profiles (
                    user_id, full_name, goal, training_level,
                    meal_preference, weight_kg, health_notes, training_setting, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    goal = excluded.goal,
                    training_level = excluded.training_level,
                    meal_preference = excluded.meal_preference,
                    weight_kg = excluded.weight_kg,
                    health_notes = excluded.health_notes,
                    training_setting = excluded.training_setting,
                    updated_at = datetime('now')
                """,
                (
                    profile.user_id,
                    profile.full_name,
                    profile.goal,
                    profile.training_level,
                    profile.meal_preference,
                    profile.weight_kg,
                    profile.health_notes,
                    profile.training_setting,
                ),
            )
            self._conn.commit()

    def get(self, user_id: str) -> UserOnboardingProfile | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT user_id, full_name, goal, training_level, meal_preference,
                       weight_kg, health_notes, training_setting
                FROM onboarding_profiles
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return UserOnboardingProfile(
            user_id=row[0],
            full_name=row[1],
            goal=row[2],
            training_level=row[3],
            meal_preference=row[4],
            weight_kg=row[5],
            health_notes=row[6],
            training_setting=row[7],
        )

    def clear(self, user_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM onboarding_profiles WHERE user_id = ?",
                (user_id,),
            )
            self._conn.commit()
            return cur.rowcount > 0

    def list_profiles(self) -> list[UserOnboardingProfile]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT user_id, full_name, goal, training_level, meal_preference,
                       weight_kg, health_notes, training_setting
                FROM onboarding_profiles
                ORDER BY user_id ASC
                """
            ).fetchall()
        return [
            UserOnboardingProfile(
                user_id=row[0],
                full_name=row[1],
                goal=row[2],
                training_level=row[3],
                meal_preference=row[4],
                weight_kg=row[5],
                health_notes=row[6],
                training_setting=row[7],
            )
            for row in rows
        ]


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
