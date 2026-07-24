import logging
import os
import socket

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from chatbot.engine import ConcurrentChatbot, MockAIProvider
from chatbot.history_store import SqliteChatHistoryStore
from chatbot.logger_config import configure_logging
from chatbot.portal_template import get_portal_html
from chatbot.onboarding import SqliteOnboardingStore
from chatbot.routes_admin import create_admin_router
from chatbot.routes_chat import create_chat_router
from chatbot.routes_onboarding import create_onboarding_router


app = FastAPI(title="Diet-Training Bot API", version="1.0.0")

DB_PATH = os.getenv("CHATBOT_DB_PATH", "data/chatbot.db")
INVITE_CODE = os.getenv("PORTAL_INVITE_CODE", "").strip()
ADMIN_VIEW_CODE = os.getenv("ADMIN_VIEW_CODE", "").strip()

bot = ConcurrentChatbot(
    provider=MockAIProvider(),
    max_workers=6,
    per_request_timeout=2.0,
    retries=2,
)

history_store = SqliteChatHistoryStore(db_path=DB_PATH)
onboarding_store = SqliteOnboardingStore(db_path=DB_PATH)

PORTAL_HTML = get_portal_html()


def _get_portal_share_urls(request: Request) -> list[str]:
    scheme = request.url.scheme
    port = request.url.port or 8000
    host_header = request.headers.get("host", f"127.0.0.1:{port}")

    # In hosted environments such as Render, only share the public host URL.
    if ".onrender.com" in host_header:
        return [f"{scheme}://{host_header}/portal"]

    urls: list[str] = [f"{scheme}://{host_header}/portal"]

    candidates: set[str] = set()
    try:
        host_name = socket.gethostname()
        for info in socket.getaddrinfo(host_name, None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith("127.") or ip.startswith("169.254."):
                continue
            candidates.add(ip)
    except OSError:
        pass

    for ip in sorted(candidates):
        urls.append(f"{scheme}://{ip}:{port}/portal")

    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            deduped.append(url)
            seen.add(url)
    return deduped


def _is_public_path(path: str) -> bool:
    return path in {
        "/",
        "/portal",
        "/portal/share-links",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }


def _extract_invite_code(request: Request) -> str:
    header_code = request.headers.get("x-invite-code", "").strip()
    if header_code:
        return header_code
    query_code = request.query_params.get("invite", "").strip()
    return query_code


def _extract_admin_code(request: Request) -> str:
    header_code = request.headers.get("x-admin-code", "").strip()
    if header_code:
        return header_code
    query_code = request.query_params.get("admin", "").strip()
    return query_code


@app.middleware("http")
async def invite_code_middleware(request: Request, call_next):
    if not INVITE_CODE:
        return await call_next(request)

    if _is_public_path(request.url.path):
        return await call_next(request)

    supplied_code = _extract_invite_code(request)
    if supplied_code != INVITE_CODE:
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Unauthorized. Provide valid invite code via ?invite=... or x-invite-code header.",
            },
        )

    return await call_next(request)


@app.on_event("startup")
def on_startup() -> None:
    configure_logging(logging.INFO)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def portal_home() -> str:
    return PORTAL_HTML


@app.get("/portal", response_class=HTMLResponse)
def portal_page() -> str:
    return PORTAL_HTML


@app.get("/portal/share-links")
def portal_share_links(request: Request) -> dict:
    return {
        "urls": _get_portal_share_urls(request),
        "note": "People on your local network can use a LAN URL if your firewall allows port 8000.",
    }


app.include_router(
    create_admin_router(
        history_store=history_store,
        onboarding_store=onboarding_store,
        admin_view_code=ADMIN_VIEW_CODE,
        extract_admin_code=_extract_admin_code,
    )
)
app.include_router(create_onboarding_router(onboarding_store=onboarding_store))
app.include_router(
    create_chat_router(
        bot=bot,
        history_store=history_store,
        onboarding_store=onboarding_store,
    )
)

