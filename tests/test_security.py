import pytest
from starlette.datastructures import Headers
from starlette.requests import Request

from chatbot.security import (
    PUBLIC_PATHS,
    extract_admin_code,
    extract_invite_code,
    is_public_path,
)

INVITE_CODE = "inv-123"


def build_request(headers: dict | None = None, query: str = "") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/chat",
        "query_string": query.encode(),
        "headers": Headers(headers or {}).raw,
    }
    return Request(scope)


@pytest.mark.parametrize("path", sorted(PUBLIC_PATHS))
def test_documented_paths_are_public(path):
    assert is_public_path(path) is True


@pytest.mark.parametrize("path", ["/chat", "/onboarding/submit", "/admin/users", "/portal/"])
def test_other_paths_are_protected(path):
    assert is_public_path(path) is False


def test_extract_invite_code_prefers_the_header():
    request = build_request({"x-invite-code": "from-header"}, "invite=from-query")
    assert extract_invite_code(request) == "from-header"


def test_extract_invite_code_falls_back_to_query_parameter():
    assert extract_invite_code(build_request(query="invite=from-query")) == "from-query"


def test_extract_invite_code_returns_empty_when_absent():
    assert extract_invite_code(build_request()) == ""


def test_extract_invite_code_strips_whitespace():
    assert extract_invite_code(build_request({"x-invite-code": "  code  "})) == "code"


def test_extract_admin_code_prefers_the_header():
    request = build_request({"x-admin-code": "from-header"}, "admin=from-query")
    assert extract_admin_code(request) == "from-header"


def test_extract_admin_code_falls_back_to_query_parameter():
    assert extract_admin_code(build_request(query="admin=from-query")) == "from-query"


def test_extract_admin_code_returns_empty_when_absent():
    assert extract_admin_code(build_request()) == ""


@pytest.fixture
def gated_client(make_api):
    return make_api(invite_code=INVITE_CODE).client


@pytest.mark.parametrize("path", ["/health", "/", "/portal", "/portal/share-links", "/docs"])
def test_public_paths_stay_reachable_without_invite_code(gated_client, path):
    assert gated_client.get(path).status_code == 200


def test_protected_path_is_rejected_without_invite_code(gated_client):
    response = gated_client.get("/chat/history/alice")

    assert response.status_code == 401
    assert "Provide valid invite code" in response.json()["detail"]


def test_protected_path_is_rejected_with_wrong_invite_code(gated_client):
    response = gated_client.get("/chat/history/alice", headers={"x-invite-code": "nope"})
    assert response.status_code == 401


def test_protected_path_accepts_invite_code_header(gated_client):
    response = gated_client.get(
        "/chat/history/alice", headers={"x-invite-code": INVITE_CODE}
    )
    assert response.status_code == 200


def test_protected_path_accepts_invite_code_query_parameter(gated_client):
    response = gated_client.get("/chat/history/alice", params={"invite": INVITE_CODE})
    assert response.status_code == 200


def test_chat_is_gated_by_the_invite_code(gated_client):
    payload = {"user_id": "alice", "prompt": "meal plan", "use_history": False}

    assert gated_client.post("/chat", json=payload).status_code == 401
    assert (
        gated_client.post(
            "/chat", json=payload, headers={"x-invite-code": INVITE_CODE}
        ).status_code
        == 200
    )


def test_no_invite_code_configured_leaves_every_route_open(client):
    assert client.get("/chat/history/alice").status_code == 200
