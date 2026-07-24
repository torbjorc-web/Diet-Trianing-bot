import logging
import os
import socket
from dataclasses import asdict
from typing import List, Literal

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from chatbot.engine import ConcurrentChatbot, MockAIProvider
from chatbot.history_store import ChatTurn, SqliteChatHistoryStore
from chatbot.logger_config import configure_logging
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

bot = ConcurrentChatbot(
    provider=MockAIProvider(),
    max_workers=6,
    per_request_timeout=2.0,
    retries=2,
)

history_store = SqliteChatHistoryStore(db_path=DB_PATH)
onboarding_store = SqliteOnboardingStore(db_path=DB_PATH)

PORTAL_HTML = """<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Diet-Training Bot Portal</title>
    <style>
        :root {
            --bg: #f4f8f1;
            --panel: #ffffff;
            --text: #1f2a1f;
            --accent: #2f7d32;
            --accent-2: #155d27;
            --muted: #5c6b5d;
            --line: #d7e2d7;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Segoe UI, Tahoma, sans-serif;
            color: var(--text);
            background: radial-gradient(circle at top left, #eaf6df, var(--bg));
        }
        .wrap {
            max-width: 980px;
            margin: 0 auto;
            padding: 24px;
            display: grid;
            gap: 16px;
        }
        .card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        }
        h1 { margin: 0 0 10px; font-size: 28px; }
        h2 { margin: 0 0 10px; font-size: 20px; }
        p { margin: 6px 0; color: var(--muted); }
        .grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
        }
        label { display: block; font-size: 13px; margin-bottom: 4px; color: var(--muted); }
        input, select, textarea {
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 10px;
            font-size: 14px;
            background: #fbfdfa;
        }
        textarea { min-height: 100px; resize: vertical; }
        button {
            border: 0;
            border-radius: 10px;
            background: var(--accent);
            color: #fff;
            padding: 10px 14px;
            font-weight: 600;
            cursor: pointer;
            margin-right: 8px;
            margin-top: 8px;
        }
        button.secondary { background: #3f5140; }
        button:hover { background: var(--accent-2); }
        pre {
            white-space: pre-wrap;
            background: #f4f9f4;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 12px;
            min-height: 120px;
            margin-top: 10px;
        }
        @media (max-width: 840px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"card\">
            <h1>Diet-Training Bot Portal</h1>
            <p>Use this page instead of Swagger. First fill onboarding, then chat.</p>
            <label>Invite Code (if enabled)</label>
            <input id=\"invite_code\" placeholder=\"Optional invite code\" />
        </div>

        <div class=\"card\">
            <h2>0) Share this with friends/family</h2>
            <p>Use one of these links. Pick a LAN link for other devices on your home network.</p>
            <button onclick=\"loadShareLinks()\">Refresh Links</button>
            <button class=\"secondary\" onclick=\"copyPrimaryLink()\">Copy First Link</button>
            <pre id=\"share_result\">Loading share links...</pre>
        </div>

        <div class=\"card\">
            <h2>1) Onboarding</h2>
            <div class=\"grid\">
                <div><label>User ID</label><input id=\"user_id\" value=\"friend1\" /></div>
                <div><label>Full Name</label><input id=\"full_name\" value=\"Lina Berg\" /></div>
                <div><label>Goal</label><input id=\"goal\" value=\"fat loss\" /></div>
                <div>
                    <label>Training Level</label>
                    <select id=\"training_level\">
                        <option>beginner</option>
                        <option>intermediate</option>
                        <option>advanced</option>
                    </select>
                </div>
                <div>
                    <label>Meal Preference</label>
                    <select id=\"meal_preference\">
                        <option>none</option>
                        <option>halal</option>
                        <option>kosher</option>
                        <option>vegan</option>
                        <option>vegetarian</option>
                    </select>
                </div>
                <div><label>Weight (kg)</label><input id=\"weight_kg\" type=\"number\" value=\"66\" /></div>
                <div><label>Health Notes</label><input id=\"health_notes\" value=\"none\" /></div>
                <div>
                    <label>Training Setting</label>
                    <select id=\"training_setting\">
                        <option>self</option>
                        <option>studio</option>
                        <option>group</option>
                    </select>
                </div>
            </div>
            <button onclick=\"submitOnboarding()\">Save Onboarding</button>
            <button class=\"secondary\" onclick=\"loadOnboarding()\">Load Onboarding</button>
            <pre id=\"onboarding_result\">No onboarding call yet.</pre>
        </div>

        <div class=\"card\">
            <h2>2) Chat</h2>
            <label>Prompt</label>
            <textarea id=\"prompt\">Make both meal and training plan for me.</textarea>
            <button onclick=\"sendChat()\">Send</button>
            <button class=\"secondary\" onclick=\"loadHistory()\">Show History</button>
            <pre id=\"chat_result\">No chat call yet.</pre>
        </div>
    </div>

    <script>
        let shareUrls = [];

        function v(id) { return document.getElementById(id).value; }
        function show(id, value) {
            document.getElementById(id).textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
        }

        function inviteCode() {
            return (v("invite_code") || "").trim();
        }

        function withInvite(path) {
            const code = inviteCode();
            if (!code) {
                return path;
            }
            const sep = path.includes("?") ? "&" : "?";
            return `${path}${sep}invite=${encodeURIComponent(code)}`;
        }

        function requestHeaders() {
            const code = inviteCode();
            const headers = { "Content-Type": "application/json" };
            if (code) {
                headers["x-invite-code"] = code;
            }
            return headers;
        }

        async function loadShareLinks() {
            const res = await fetch(withInvite("/portal/share-links"));
            const data = await res.json();
            shareUrls = data.urls || [];
            if (!shareUrls.length) {
                show("share_result", "No share links found.");
                return;
            }
            const text = [
                "Share links:",
                ...shareUrls.map((u, i) => `${i + 1}. ${u}`),
                "",
                data.note || "",
            ].join("\\n");
            show("share_result", text);
        }

        async function copyPrimaryLink() {
            if (!shareUrls.length) {
                await loadShareLinks();
            }
            const primary = shareUrls[0];
            if (!primary) {
                show("share_result", "No link available to copy.");
                return;
            }
            await navigator.clipboard.writeText(primary);
            show("share_result", `Copied: ${primary}`);
        }

        async function submitOnboarding() {
            const payload = {
                user_id: v("user_id"),
                full_name: v("full_name"),
                goal: v("goal"),
                training_level: v("training_level"),
                meal_preference: v("meal_preference"),
                weight_kg: Number(v("weight_kg")) || null,
                health_notes: v("health_notes"),
                training_setting: v("training_setting")
            };

            const res = await fetch(withInvite("/onboarding/submit"), {
                method: "POST",
                headers: requestHeaders(),
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            show("onboarding_result", data);
        }

        async function loadOnboarding() {
            const res = await fetch(withInvite(`/onboarding/${encodeURIComponent(v("user_id"))}`));
            const data = await res.json();
            show("onboarding_result", data);
        }

        async function sendChat() {
            const payload = {
                user_id: v("user_id"),
                prompt: v("prompt"),
                use_history: true,
                history_turns: 5,
                use_onboarding: true
            };

            const res = await fetch(withInvite("/chat"), {
                method: "POST",
                headers: requestHeaders(),
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            show("chat_result", data.response || data);
        }

        async function loadHistory() {
            const res = await fetch(withInvite(`/chat/history/${encodeURIComponent(v("user_id"))}`));
            const data = await res.json();
            show("chat_result", data);
        }

        loadShareLinks();
    </script>
</body>
</html>
"""


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
    return path in {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}


def _extract_invite_code(request: Request) -> str:
    header_code = request.headers.get("x-invite-code", "").strip()
    if header_code:
        return header_code
    query_code = request.query_params.get("invite", "").strip()
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
