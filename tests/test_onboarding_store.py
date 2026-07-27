import pytest

from chatbot.onboarding import (
    ONBOARDING_QUESTIONS,
    InMemoryOnboardingStore,
    SqliteOnboardingStore,
    normalize_meal_preference,
    normalize_training_setting,
    profile_to_dict,
)
from tests.conftest import make_profile


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryOnboardingStore()
    return SqliteOnboardingStore(db_path=str(tmp_path / "onboarding.db"))


def test_unknown_user_has_no_profile(store):
    assert store.get("nobody") is None


def test_upsert_then_get_returns_profile(store):
    store.upsert(make_profile("alice"))

    profile = store.get("alice")

    assert profile.full_name == "Anna Hansen"
    assert profile.meal_preference == "halal"
    assert profile.weight_kg == 78.0


def test_upsert_overwrites_existing_profile(store):
    store.upsert(make_profile("alice", goal="fat loss"))
    store.upsert(make_profile("alice", goal="muscle gain"))

    assert store.get("alice").goal == "muscle gain"


def test_profiles_are_isolated_per_user(store):
    store.upsert(make_profile("alice", full_name="Anna"))
    store.upsert(make_profile("bob", full_name="Bob"))

    assert store.get("alice").full_name == "Anna"
    assert store.get("bob").full_name == "Bob"


def test_clear_removes_existing_profile(store):
    store.upsert(make_profile("alice"))

    assert store.clear("alice") is True
    assert store.get("alice") is None


def test_clear_unknown_user_reports_nothing_removed(store):
    assert store.clear("nobody") is False


def test_optional_weight_can_be_missing(store):
    store.upsert(make_profile("alice", weight_kg=None))
    assert store.get("alice").weight_kg is None


def test_list_profiles_is_sorted_by_user_id(onboarding_store):
    onboarding_store.upsert(make_profile("carol"))
    onboarding_store.upsert(make_profile("alice"))

    assert [profile.user_id for profile in onboarding_store.list_profiles()] == [
        "alice",
        "carol",
    ]


def test_list_profiles_is_empty_for_new_store(onboarding_store):
    assert onboarding_store.list_profiles() == []


def test_sqlite_profile_persists_across_connections(tmp_path):
    db_path = str(tmp_path / "persist.db")
    SqliteOnboardingStore(db_path=db_path).upsert(make_profile("alice"))

    assert SqliteOnboardingStore(db_path=db_path).get("alice").full_name == "Anna Hansen"


def test_prompt_context_includes_all_profile_fields():
    context = make_profile("alice").to_prompt_context()

    assert "Onboarding profile:" in context
    assert "- Full name: Anna Hansen" in context
    assert "- Goal: fat loss" in context
    assert "- Training level: beginner" in context
    assert "- Meal preference: halal" in context
    assert "- Weight: 78 kg" in context
    assert "- Health notes: knee discomfort" in context
    assert "- Training setting: studio" in context


def test_prompt_context_handles_unknown_weight():
    assert "- Weight: unknown" in make_profile(weight_kg=None).to_prompt_context()


def test_profile_to_dict_exposes_every_field():
    assert profile_to_dict(make_profile("alice")) == {
        "user_id": "alice",
        "full_name": "Anna Hansen",
        "goal": "fat loss",
        "training_level": "beginner",
        "meal_preference": "halal",
        "weight_kg": 78.0,
        "health_notes": "knee discomfort",
        "training_setting": "studio",
    }


@pytest.mark.parametrize(
    "value, expected",
    [
        ("studio", "studio"),
        ("Gym", "studio"),
        ("fitness center", "studio"),
        ("group", "group"),
        ("class", "group"),
        ("team", "group"),
        ("self", "self"),
        ("  home  ", "self"),
    ],
)
def test_normalize_training_setting(value, expected):
    assert normalize_training_setting(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("halal", "halal"),
        ("Kosher", "kosher"),
        ("VEGAN", "vegan"),
        ("vegetarian", "vegetarian"),
        ("veg", "vegetarian"),
        ("veggie", "vegetarian"),
        ("none", "none"),
        ("pescatarian", "none"),
    ],
)
def test_normalize_meal_preference(value, expected):
    assert normalize_meal_preference(value) == expected


def test_onboarding_questions_cover_the_documented_fields():
    ids = [question["id"] for question in ONBOARDING_QUESTIONS]
    assert ids == [
        "full_name",
        "goal",
        "training_level",
        "meal_preference",
        "weight_kg",
        "health_notes",
        "training_setting",
    ]
    assert all(question["question"] for question in ONBOARDING_QUESTIONS)
