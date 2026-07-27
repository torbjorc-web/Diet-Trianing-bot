import csv
import io

import pytest

from tests.conftest import ADMIN_VIEW_CODE, onboarding_payload


ADMIN_HEADERS = {"x-admin-code": ADMIN_VIEW_CODE}

ADMIN_PATHS = ["/admin/users", "/admin/chat-inputs", "/admin/chat-inputs.csv"]


def seed(client) -> None:
    client.post("/onboarding/submit", json=onboarding_payload("alice"))
    client.post(
        "/chat",
        json={"user_id": "bob", "prompt": "training plan", "use_history": False},
    )


@pytest.mark.parametrize("path", ADMIN_PATHS)
def test_admin_endpoints_are_disabled_without_admin_code_configured(client, path):
    response = client.get(path)

    assert response.status_code == 403
    assert "Admin inspection is disabled" in response.json()["detail"]


@pytest.mark.parametrize("path", ADMIN_PATHS)
def test_admin_endpoints_reject_missing_code(admin_client, path):
    response = admin_client.get(path)

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized admin access"


@pytest.mark.parametrize("path", ADMIN_PATHS)
def test_admin_endpoints_reject_wrong_code(admin_client, path):
    response = admin_client.get(path, headers={"x-admin-code": "wrong"})

    assert response.status_code == 401


@pytest.mark.parametrize("path", ADMIN_PATHS)
def test_admin_endpoints_accept_code_via_header(admin_client, path):
    assert admin_client.get(path, headers=ADMIN_HEADERS).status_code == 200


@pytest.mark.parametrize("path", ADMIN_PATHS)
def test_admin_endpoints_accept_code_via_query_parameter(admin_client, path):
    assert admin_client.get(path, params={"admin": ADMIN_VIEW_CODE}).status_code == 200


def test_admin_users_is_empty_before_any_activity(admin_client):
    body = admin_client.get("/admin/users", headers=ADMIN_HEADERS).json()

    assert body == {"count": 0, "user_ids": [], "profiles": []}


def test_admin_users_combines_chat_users_and_onboarded_profiles(admin_client):
    seed(admin_client)

    body = admin_client.get("/admin/users", headers=ADMIN_HEADERS).json()

    assert body["user_ids"] == ["alice", "bob"]
    assert body["count"] == 2
    assert [profile["user_id"] for profile in body["profiles"]] == ["alice"]
    assert body["profiles"][0]["full_name"] == "Anna Hansen"


def test_admin_users_deduplicates_a_user_present_in_both_sources(admin_client):
    admin_client.post("/onboarding/submit", json=onboarding_payload("alice"))
    admin_client.post(
        "/chat", json={"user_id": "alice", "prompt": "meal plan", "use_history": False}
    )

    body = admin_client.get("/admin/users", headers=ADMIN_HEADERS).json()

    assert body["user_ids"] == ["alice"]
    assert body["count"] == 1


def test_admin_chat_inputs_returns_recorded_prompts_and_responses(admin_client):
    seed(admin_client)

    body = admin_client.get(
        "/admin/chat-inputs", headers=ADMIN_HEADERS, params={"window": "all"}
    ).json()

    assert body["window"] == "all"
    assert body["count"] == 1
    record = body["records"][0]
    assert record["user_id"] == "bob"
    assert record["prompt"] == "training plan"
    assert "Training plan:" in record["response"]
    assert record["success"] is True
    assert record["created_at"]


def test_admin_chat_inputs_defaults_to_the_7d_window(admin_client):
    seed(admin_client)

    body = admin_client.get("/admin/chat-inputs", headers=ADMIN_HEADERS).json()

    assert body["window"] == "7d"
    assert body["count"] == 1


@pytest.mark.parametrize("window", ["today", "7d", "30d", "all"])
def test_admin_chat_inputs_accepts_every_documented_window(admin_client, window):
    seed(admin_client)

    body = admin_client.get(
        "/admin/chat-inputs", headers=ADMIN_HEADERS, params={"window": window}
    ).json()

    assert body["window"] == window
    assert body["count"] == 1


def test_admin_chat_inputs_rejects_unknown_window(admin_client):
    response = admin_client.get(
        "/admin/chat-inputs", headers=ADMIN_HEADERS, params={"window": "yesterday"}
    )

    assert response.status_code == 422


def test_admin_chat_inputs_respects_the_limit(admin_client):
    for index in range(3):
        admin_client.post(
            "/chat",
            json={"user_id": "bob", "prompt": f"meal plan {index}", "use_history": False},
        )

    body = admin_client.get(
        "/admin/chat-inputs",
        headers=ADMIN_HEADERS,
        params={"limit": 2, "window": "all"},
    ).json()

    assert body["count"] == 2
    assert [record["prompt"] for record in body["records"]] == ["meal plan 2", "meal plan 1"]


def test_admin_csv_export_returns_csv_content(admin_client):
    seed(admin_client)

    response = admin_client.get(
        "/admin/chat-inputs.csv", headers=ADMIN_HEADERS, params={"window": "all"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=chat-inputs-all.csv"
    )

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == ["created_at", "user_id", "success", "prompt", "response"]
    assert rows[1][1] == "bob"
    assert rows[1][3] == "training plan"


def test_admin_csv_export_is_header_only_without_data(admin_client):
    response = admin_client.get(
        "/admin/chat-inputs.csv", headers=ADMIN_HEADERS, params={"window": "all"}
    )

    assert [row for row in csv.reader(io.StringIO(response.text)) if row] == [
        ["created_at", "user_id", "success", "prompt", "response"]
    ]


def test_admin_csv_filename_reflects_the_window(admin_client):
    response = admin_client.get(
        "/admin/chat-inputs.csv", headers=ADMIN_HEADERS, params={"window": "30d"}
    )

    assert "chat-inputs-30d.csv" in response.headers["content-disposition"]


def test_admin_data_is_reset_between_tests(admin_client):
    """Guards the fixture isolation the other admin tests rely on."""
    body = admin_client.get(
        "/admin/chat-inputs", headers=ADMIN_HEADERS, params={"window": "all"}
    ).json()
    assert body["count"] == 0
