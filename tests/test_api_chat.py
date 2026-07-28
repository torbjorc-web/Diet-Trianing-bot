import pytest

from tests.conftest import onboarding_payload


def chat(client, prompt: str, user_id: str = "alice", **overrides):
    payload = {"user_id": user_id, "prompt": prompt, "use_history": False, "use_onboarding": False}
    payload.update(overrides)
    return client.post("/chat", json=payload)


def test_chat_returns_a_meal_plan(client):
    response = chat(client, "give me a vegan meal plan for fat loss")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["user_id"] == "alice"
    assert body["attempts"] == 1
    assert body["error"] is None
    assert "Meal plan:" in body["response"]
    assert "Training plan:" not in body["response"]


def test_chat_returns_a_training_plan(client):
    body = chat(client, "give me an advanced training plan 5 days").json()

    assert "Training plan:" in body["response"]
    assert "Meal plan:" not in body["response"]
    assert "Level: advanced" in body["response"]
    assert "Days/week: 5" in body["response"]


def test_chat_returns_a_combined_plan(client):
    body = chat(client, "make both meal and training plan for fat loss").json()

    assert "Meal plan:" in body["response"]
    assert "Training plan:" in body["response"]


def test_chat_stores_the_turn_in_history(client):
    chat(client, "meal plan")

    body = chat(client, "training plan").json()

    assert body["history_count"] == 2


@pytest.mark.parametrize("payload", [{"user_id": "", "prompt": "meal plan"}, {"user_id": "alice", "prompt": ""}])
def test_chat_rejects_empty_fields_with_422(client, payload):
    assert client.post("/chat", json=payload).status_code == 422


def test_chat_rejects_missing_body(client):
    assert client.post("/chat", json={}).status_code == 422


@pytest.mark.parametrize("turns", [0, 11])
def test_chat_rejects_out_of_range_history_turns(client, turns):
    response = chat(client, "meal plan", history_turns=turns)
    assert response.status_code == 422


def test_provider_failure_returns_graceful_fallback(client):
    body = chat(client, "please fail on purpose").json()

    assert body["success"] is False
    assert "trouble reaching my planning engine" in body["response"]
    assert body["attempts"] == 3  # initial attempt plus the two configured retries


def test_failed_turns_are_still_recorded_in_history(client):
    chat(client, "please fail on purpose")

    turns = client.get("/chat/history/alice").json()["turns"]

    assert len(turns) == 1
    assert turns[0]["success"] is False


def test_history_context_is_sent_to_the_provider(api):
    chat(api.client, "meal plan for fat loss")
    chat(api.client, "make it 5 days", use_history=True)

    last_prompt = api.provider.calls[-1][1]

    assert "Recent conversation context:" in last_prompt
    assert "1. User: meal plan for fat loss" in last_prompt
    assert "Current user request: make it 5 days" in last_prompt


def test_history_context_is_limited_to_requested_turns(api):
    for index in range(4):
        chat(api.client, f"meal plan {index}")

    chat(api.client, "follow up", use_history=True, history_turns=2)
    last_prompt = api.provider.calls[-1][1]

    assert "meal plan 3" in last_prompt
    assert "meal plan 0" not in last_prompt


def test_history_context_is_omitted_when_disabled(api):
    chat(api.client, "meal plan")
    chat(api.client, "training plan", use_history=False)

    assert "Recent conversation context:" not in api.provider.calls[-1][1]


def test_history_is_isolated_per_user(api):
    chat(api.client, "meal plan", user_id="alice")
    chat(api.client, "training plan", user_id="bob", use_history=True)

    assert "Recent conversation context:" not in api.provider.calls[-1][1]


def test_onboarding_profile_is_injected_as_context(api):
    api.client.post("/onboarding/submit", json=onboarding_payload())

    chat(api.client, "make my plan", use_onboarding=True)
    last_prompt = api.provider.calls[-1][1]

    assert "Onboarding profile:" in last_prompt
    assert "- Meal preference: halal" in last_prompt
    assert last_prompt.endswith("make my plan")


def test_onboarding_context_is_omitted_when_disabled(api):
    api.client.post("/onboarding/submit", json=onboarding_payload())

    chat(api.client, "make my plan", use_onboarding=False)

    assert "Onboarding profile:" not in api.provider.calls[-1][1]


def test_onboarding_full_name_is_used_as_display_name(api):
    api.client.post("/onboarding/submit", json=onboarding_payload())

    body = chat(api.client, "meal plan", use_onboarding=True).json()

    assert body["response"].startswith("Hi Anna Hansen.")
    assert body["user_id"] == "Anna Hansen"


def test_user_id_is_used_when_no_profile_exists(client):
    assert chat(client, "meal plan").json()["response"].startswith("Hi alice.")


def test_missing_profile_leaves_prompt_unchanged(api):
    chat(api.client, "meal plan", use_onboarding=True)

    assert api.provider.calls[-1][1] == "meal plan"


def test_batch_chat_processes_every_request(client):
    response = client.post(
        "/chat/batch",
        json={
            "requests": [
                {"user_id": "alice", "prompt": "meal plan for fat loss"},
                {"user_id": "bob", "prompt": "training plan 4 days"},
            ]
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert set(results) == {"alice", "bob"}
    assert "Meal plan:" in results["alice"]["response"]
    assert "Training plan:" in results["bob"]["response"]


def test_batch_chat_records_history_for_each_user(client):
    client.post(
        "/chat/batch",
        json={
            "requests": [
                {"user_id": "alice", "prompt": "meal plan"},
                {"user_id": "bob", "prompt": "training plan"},
            ]
        },
    )

    assert client.get("/chat/history/alice").json()["count"] == 1
    assert client.get("/chat/history/bob").json()["count"] == 1


def test_batch_chat_with_empty_list_returns_no_results(client):
    assert client.post("/chat/batch", json={"requests": []}).json() == {"results": {}}


def test_batch_chat_isolates_failures(client):
    results = client.post(
        "/chat/batch",
        json={
            "requests": [
                {"user_id": "alice", "prompt": "meal plan"},
                {"user_id": "bob", "prompt": "please fail"},
            ]
        },
    ).json()["results"]

    assert results["alice"]["success"] is True
    assert results["bob"]["success"] is False


def test_get_history_is_empty_for_unknown_user(client):
    assert client.get("/chat/history/nobody").json() == {
        "user_id": "nobody",
        "count": 0,
        "turns": [],
    }


def test_get_history_returns_stored_turns_in_order(client):
    chat(client, "meal plan")
    chat(client, "training plan")

    body = client.get("/chat/history/alice").json()

    assert body["count"] == 2
    assert [turn["prompt"] for turn in body["turns"]] == ["meal plan", "training plan"]
    assert all(turn["success"] for turn in body["turns"])


def test_history_stores_the_raw_prompt_without_injected_context(client):
    chat(client, "meal plan")
    chat(client, "training plan", use_history=True, use_onboarding=True)

    prompts = [turn["prompt"] for turn in client.get("/chat/history/alice").json()["turns"]]

    assert prompts == ["meal plan", "training plan"]


def test_clear_history_reports_number_of_removed_turns(client):
    chat(client, "meal plan")
    chat(client, "training plan")

    assert client.delete("/chat/history/alice").json() == {"user_id": "alice", "cleared": 2}
    assert client.get("/chat/history/alice").json()["count"] == 0


def test_clear_history_for_unknown_user_reports_zero(client):
    assert client.delete("/chat/history/nobody").json()["cleared"] == 0


def test_clear_history_only_affects_the_requested_user(client):
    chat(client, "meal plan", user_id="alice")
    chat(client, "meal plan", user_id="bob")

    client.delete("/chat/history/alice")

    assert client.get("/chat/history/alice").json()["count"] == 0
    assert client.get("/chat/history/bob").json()["count"] == 1


def test_history_is_reset_between_tests(client):
    """Guards the fixture isolation the other chat tests rely on."""
    assert client.get("/chat/history/alice").json()["count"] == 0
