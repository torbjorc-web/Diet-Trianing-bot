import logging
import os
import socket
from dataclasses import asdict
from typing import List, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from chatbot.engine import ConcurrentChatbot, MockAIProvider
from chatbot.history_store import ChatTurn, SqliteChatHistoryStore
from chatbot.logger_config import configure_logging
from chatbot.portal_template import get_portal_html
from chatbot.admin_reporting import filter_records_by_window, records_to_csv
from chatbot.onboarding import (
    ONBOARDING_QUESTIONS,
    SqliteOnboardingStore,
    UserOnboardingProfile,
    normalize_training_setting,
    profile_to_dict,
)


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, examples=["alice"])
    prompt: str = Field(
        ...,
        min_length=1,
        examples=["Make both meal and training plan for fat loss with 4 days training"],
    )
    use_history: bool = Field(
        default=True,
        description="Use recent history to interpret follow-up prompts.",
    )
    history_turns: int = Field(
        default=3,
        ge=1,
        le=10,
        description="How many previous turns to include as context.",
    )
    use_onboarding: bool = Field(
        default=True,
        description="Use stored onboarding profile as context for planning.",
    )


class OnboardingSubmitRequest(BaseModel):
    user_id: str = Field(..., min_length=1, examples=["alice"])
    full_name: str = Field(..., min_length=1, examples=["Anna Hansen"])
    goal: str = Field(..., min_length=1, examples=["fat loss"])
    training_level: str = Field(..., min_length=1, examples=["beginner"])
    meal_preference: Literal["halal", "kosher", "vegan", "vegetarian", "none"] = Field(
        ...,
        examples=["halal"],
        description="Allowed values: halal, kosher, vegan, vegetarian, none",
    )
    weight_kg: float | None = Field(default=None, gt=0, examples=[78])
    health_notes: str = Field(default="none", examples=["knee discomfort"])
    training_setting: str = Field(..., min_length=1, examples=["studio"])


class BatchChatRequest(BaseModel):
    requests: List[ChatRequest] = Field(default_factory=list)


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


def _build_contextual_prompt(turns: List[ChatTurn], prompt: str) -> str:
    if not turns:
        return prompt

    lines: List[str] = [
        "Recent conversation context:",
    ]

    for idx, turn in enumerate(turns, start=1):
        lines.append(f"{idx}. User: {turn.prompt}")
        lines.append(f"{idx}. Bot: {turn.response}")

    lines.append(f"Current user request: {prompt}")
    return "\n".join(lines)


def _inject_onboarding_context(
    user_id: str, prompt: str, use_onboarding: bool
) -> str:
    if not use_onboarding:
        return prompt

    profile = onboarding_store.get(user_id)
    if profile is None:
        return prompt

    return f"{profile.to_prompt_context()}\n\n{prompt}"


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


def _assert_admin(request: Request) -> None:
    if not ADMIN_VIEW_CODE:
        raise HTTPException(
            status_code=403,
            detail="Admin inspection is disabled. Set ADMIN_VIEW_CODE to enable.",
        )
    supplied_code = _extract_admin_code(request)
    if supplied_code != ADMIN_VIEW_CODE:
        raise HTTPException(status_code=401, detail="Unauthorized admin access")


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


@app.get("/admin/users")
def admin_users(request: Request) -> dict:
    _assert_admin(request)
    chat_user_ids = set(history_store.list_user_ids())
    profiles = onboarding_store.list_profiles()
    profile_user_ids = {profile.user_id for profile in profiles}
    all_user_ids = sorted(chat_user_ids | profile_user_ids)
    return {
        "count": len(all_user_ids),
        "user_ids": all_user_ids,
        "profiles": [profile_to_dict(profile) for profile in profiles],
    }


@app.get("/admin/chat-inputs")
def admin_chat_inputs(
    request: Request,
    limit: int = 200,
    window: Literal["today", "7d", "30d", "all"] = "7d",
) -> dict:
    _assert_admin(request)
    records = history_store.list_recent_records(limit=limit)
    records = filter_records_by_window(records, window)
    return {
        "window": window,
        "count": len(records),
        "records": records,
    }


@app.get("/admin/chat-inputs.csv", response_class=PlainTextResponse)
def admin_chat_inputs_csv(
    request: Request,
    limit: int = 1000,
    window: Literal["today", "7d", "30d", "all"] = "7d",
) -> PlainTextResponse:
    _assert_admin(request)
    records = history_store.list_recent_records(limit=limit)
    records = filter_records_by_window(records, window)

    headers = {"Content-Disposition": f"attachment; filename=chat-inputs-{window}.csv"}
    return PlainTextResponse(
        content=records_to_csv(records),
        media_type="text/csv",
        headers=headers,
    )


@app.get("/onboarding/questions")
def onboarding_questions() -> dict:
    return {"questions": ONBOARDING_QUESTIONS}


@app.post("/onboarding/submit")
def onboarding_submit(req: OnboardingSubmitRequest) -> dict:
    profile = UserOnboardingProfile(
        user_id=req.user_id,
        full_name=req.full_name.strip(),
        goal=req.goal.strip().lower(),
        training_level=req.training_level.strip().lower(),
        meal_preference=req.meal_preference,
        weight_kg=req.weight_kg,
        health_notes=req.health_notes.strip() or "none",
        training_setting=normalize_training_setting(req.training_setting),
    )
    onboarding_store.upsert(profile)
    return {"saved": True, "profile": profile_to_dict(profile)}


@app.get("/onboarding/{user_id}")
def onboarding_get(user_id: str) -> dict:
    profile = onboarding_store.get(user_id)
    if profile is None:
        return {"found": False}
    return {"found": True, "profile": profile_to_dict(profile)}


@app.delete("/onboarding/{user_id}")
def onboarding_clear(user_id: str) -> dict:
    removed = onboarding_store.clear(user_id)
    return {"removed": removed}


@app.post(
    "/chat",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "meal_plan": {
                            "summary": "Meal plan request",
                            "value": {
                                "user_id": "alice",
                                "prompt": "Create a vegetarian meal plan for fat loss",
                                "use_history": True,
                                "history_turns": 3,
                                "use_onboarding": True,
                            },
                        },
                        "training_followup": {
                            "summary": "Follow-up using history",
                            "value": {
                                "user_id": "alice",
                                "prompt": "Adjust the training to 5 days and intermediate level",
                                "use_history": True,
                                "history_turns": 5,
                                "use_onboarding": True,
                            },
                        },
                        "without_onboarding_context": {
                            "summary": "Ignore onboarding context for this request",
                            "value": {
                                "user_id": "alice",
                                "prompt": "Give me a quick training plan",
                                "use_history": False,
                                "history_turns": 3,
                                "use_onboarding": False,
                            },
                        },
                    }
                }
            }
        }
    },
)
def chat(req: ChatRequest) -> dict:
    history_context = history_store.get_recent(req.user_id, req.history_turns)
    profile = onboarding_store.get(req.user_id)
    display_name = req.user_id
    if profile is not None and profile.full_name.strip():
        display_name = profile.full_name.strip()

    request_prompt = req.prompt

    if req.use_history:
        request_prompt = _build_contextual_prompt(history_context, req.prompt)

    request_prompt = _inject_onboarding_context(
        user_id=req.user_id,
        prompt=request_prompt,
        use_onboarding=req.use_onboarding,
    )

    result = bot.process_one(user_id=display_name, prompt=request_prompt)
    history_store.append(
        req.user_id,
        ChatTurn(prompt=req.prompt, response=result.response, success=result.success),
    )

    response = asdict(result)
    response["history_count"] = len(history_store.get_all(req.user_id))
    return response


@app.post("/chat/batch")
def chat_batch(req: BatchChatRequest) -> dict:
    payload = [(item.user_id, item.prompt) for item in req.requests]
    results = bot.process_batch(payload)
    for item in req.requests:
        item_result = results[item.user_id]
        history_store.append(
            item.user_id,
            ChatTurn(
                prompt=item.prompt,
                response=item_result.response,
                success=item_result.success,
            ),
        )
    return {"results": {key: asdict(value) for key, value in results.items()}}


@app.get("/chat/history/{user_id}")
def get_history(user_id: str) -> dict:
    turns = history_store.get_all(user_id)
    return {
        "user_id": user_id,
        "count": len(turns),
        "turns": [asdict(turn) for turn in turns],
    }


@app.delete("/chat/history/{user_id}")
def clear_history(user_id: str) -> dict:
    cleared = history_store.clear(user_id)
    return {"user_id": user_id, "cleared": cleared}

