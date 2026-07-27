import pytest

from tests.conftest import onboarding_payload


def test_questions_endpoint_lists_start_questions(client):
    response = client.get("/onboarding/questions")

    assert response.status_code == 200
    questions = response.json()["questions"]
    assert [question["id"] for question in questions] == [
        "full_name",
        "goal",
        "training_level",
        "meal_preference",
        "weight_kg",
        "health_notes",
        "training_setting",
    ]


def test_submit_saves_profile_and_returns_it(client):
    response = client.post("/onboarding/submit", json=onboarding_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is True
    assert body["profile"]["user_id"] == "alice"
    assert body["profile"]["full_name"] == "Anna Hansen"
    assert body["profile"]["weight_kg"] == 78


def test_submit_normalizes_goal_level_and_training_setting(client):
    profile = client.post(
        "/onboarding/submit",
        json=onboarding_payload(goal="  Fat Loss ", training_level="BEGINNER", training_setting="gym"),
    ).json()["profile"]

    assert profile["goal"] == "fat loss"
    assert profile["training_level"] == "beginner"
    assert profile["training_setting"] == "studio"


@pytest.mark.parametrize(
    "supplied, expected",
    [("studio", "studio"), ("group", "group"), ("class", "group"), ("home", "self")],
)
def test_submit_maps_every_training_setting(client, supplied, expected):
    profile = client.post(
        "/onboarding/submit", json=onboarding_payload(training_setting=supplied)
    ).json()["profile"]

    assert profile["training_setting"] == expected


def test_submit_defaults_blank_health_notes_to_none(client):
    profile = client.post(
        "/onboarding/submit", json=onboarding_payload(health_notes="   ")
    ).json()["profile"]

    assert profile["health_notes"] == "none"


def test_submit_accepts_missing_optional_weight(client):
    payload = onboarding_payload()
    payload.pop("weight_kg")

    response = client.post("/onboarding/submit", json=payload)

    assert response.status_code == 200
    assert response.json()["profile"]["weight_kg"] is None


@pytest.mark.parametrize(
    "preference", ["halal", "kosher", "vegan", "vegetarian", "none"]
)
def test_submit_accepts_documented_meal_preferences(client, preference):
    response = client.post(
        "/onboarding/submit", json=onboarding_payload(meal_preference=preference)
    )

    assert response.status_code == 200
    assert response.json()["profile"]["meal_preference"] == preference


@pytest.mark.parametrize("preference", ["pescatarian", "HALAL", "", "keto"])
def test_submit_rejects_unsupported_meal_preference_with_422(client, preference):
    response = client.post(
        "/onboarding/submit", json=onboarding_payload(meal_preference=preference)
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field", ["user_id", "full_name", "goal", "training_level", "meal_preference", "training_setting"]
)
def test_submit_rejects_missing_required_fields(client, field):
    payload = onboarding_payload()
    payload.pop(field)

    assert client.post("/onboarding/submit", json=payload).status_code == 422


@pytest.mark.parametrize("field", ["user_id", "full_name", "goal", "training_level"])
def test_submit_rejects_empty_strings(client, field):
    assert (
        client.post("/onboarding/submit", json=onboarding_payload(**{field: ""})).status_code
        == 422
    )


@pytest.mark.parametrize("weight", [0, -10, "heavy"])
def test_submit_rejects_invalid_weight(client, weight):
    assert (
        client.post("/onboarding/submit", json=onboarding_payload(weight_kg=weight)).status_code
        == 422
    )


def test_get_profile_returns_saved_data(client):
    client.post("/onboarding/submit", json=onboarding_payload())

    body = client.get("/onboarding/alice").json()

    assert body["found"] is True
    assert body["profile"]["meal_preference"] == "halal"


def test_get_profile_for_unknown_user_reports_not_found(client):
    assert client.get("/onboarding/nobody").json() == {"found": False}


def test_submit_twice_updates_the_same_profile(client):
    client.post("/onboarding/submit", json=onboarding_payload(goal="fat loss"))
    client.post("/onboarding/submit", json=onboarding_payload(goal="muscle gain"))

    assert client.get("/onboarding/alice").json()["profile"]["goal"] == "muscle gain"


def test_delete_removes_profile(client):
    client.post("/onboarding/submit", json=onboarding_payload())

    assert client.delete("/onboarding/alice").json() == {"removed": True}
    assert client.get("/onboarding/alice").json()["found"] is False


def test_delete_unknown_profile_reports_nothing_removed(client):
    assert client.delete("/onboarding/nobody").json() == {"removed": False}


def test_profiles_are_isolated_per_user(client):
    client.post("/onboarding/submit", json=onboarding_payload("alice", full_name="Anna"))
    client.post("/onboarding/submit", json=onboarding_payload("bob", full_name="Bob"))

    client.delete("/onboarding/alice")

    assert client.get("/onboarding/alice").json()["found"] is False
    assert client.get("/onboarding/bob").json()["profile"]["full_name"] == "Bob"


def test_storage_is_reset_between_tests(client):
    """Guards the fixture isolation the other onboarding tests rely on."""
    assert client.get("/onboarding/alice").json() == {"found": False}
