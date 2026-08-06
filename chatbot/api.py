import logging
import os

from fastapi import FastAPI

from chatbot.engine import ConcurrentChatbot, MockAIProvider
from chatbot.history_store import SqliteChatHistoryStore
from chatbot.logger_config import configure_logging
from chatbot.onboarding import SqliteOnboardingStore
from chatbot.portal_template import get_portal_html
from chatbot.routes_admin import create_admin_router
from chatbot.routes_chat import create_chat_router
from chatbot.routes_onboarding import create_onboarding_router
from chatbot.routes_portal import create_portal_router
from chatbot.security import create_invite_code_middleware, extract_admin_code

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

app.middleware("http")(create_invite_code_middleware(INVITE_CODE))


@app.on_event("startup")
def on_startup() -> None:
    configure_logging(logging.INFO)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(create_portal_router(portal_html=get_portal_html()))
app.include_router(
    create_admin_router(
        history_store=history_store,
        onboarding_store=onboarding_store,
        admin_view_code=ADMIN_VIEW_CODE,
        extract_admin_code=extract_admin_code,
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

