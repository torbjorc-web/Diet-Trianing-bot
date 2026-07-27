import pytest


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/", "/portal"])
def test_portal_pages_render_html(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<!doctype html>" in response.text.lower()


@pytest.mark.parametrize("path", ["/admin", "/admin/login"])
def test_admin_login_page_renders(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert "Admin Login" in response.text


def test_share_links_include_request_host(client):
    response = client.get("/portal/share-links", headers={"host": "127.0.0.1:8000"})

    assert response.status_code == 200
    body = response.json()
    assert "http://127.0.0.1:8000/portal" in body["urls"]
    assert body["note"]


def test_share_links_on_render_only_expose_public_url(client):
    response = client.get(
        "/portal/share-links", headers={"host": "diet-bot.onrender.com"}
    )

    assert response.json()["urls"] == ["http://diet-bot.onrender.com/portal"]


def test_share_links_are_deduplicated(client):
    urls = client.get("/portal/share-links").json()["urls"]
    assert len(urls) == len(set(urls))


def test_openapi_schema_documents_the_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/health",
        "/onboarding/questions",
        "/onboarding/submit",
        "/onboarding/{user_id}",
        "/chat",
        "/chat/batch",
        "/chat/history/{user_id}",
        "/admin/users",
        "/admin/chat-inputs",
        "/admin/chat-inputs.csv",
    ]:
        assert path in paths


def test_unknown_route_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404
