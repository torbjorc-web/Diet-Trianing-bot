from dataclasses import asdict

from fastapi import APIRouter

from chatbot.history_store import ChatTurn
from chatbot.schemas import BatchChatRequest, ChatRequest

CHAT_OPENAPI_EXTRA = {
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
}


def _build_contextual_prompt(turns: list[ChatTurn], prompt: str) -> str:
    if not turns:
        return prompt

    lines: list[str] = [
        "Recent conversation context:",
    ]

    for idx, turn in enumerate(turns, start=1):
        lines.append(f"{idx}. User: {turn.prompt}")
        lines.append(f"{idx}. Bot: {turn.response}")

    lines.append(f"Current user request: {prompt}")
    return "\n".join(lines)


def _inject_onboarding_context(user_id: str, prompt: str, use_onboarding: bool, onboarding_store) -> str:
    if not use_onboarding:
        return prompt

    profile = onboarding_store.get(user_id)
    if profile is None:
        return prompt

    return f"{profile.to_prompt_context()}\n\n{prompt}"


def create_chat_router(bot, history_store, onboarding_store) -> APIRouter:
    router = APIRouter(tags=["chat"])

    @router.post("/chat", openapi_extra=CHAT_OPENAPI_EXTRA)
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
            onboarding_store=onboarding_store,
        )

        result = bot.process_one(user_id=display_name, prompt=request_prompt)
        history_store.append(
            req.user_id,
            ChatTurn(prompt=req.prompt, response=result.response, success=result.success),
        )

        response = asdict(result)
        response["history_count"] = len(history_store.get_all(req.user_id))
        return response

    @router.post("/chat/batch")
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

    @router.get("/chat/history/{user_id}")
    def get_history(user_id: str) -> dict:
        turns = history_store.get_all(user_id)
        return {
            "user_id": user_id,
            "count": len(turns),
            "turns": [asdict(turn) for turn in turns],
        }

    @router.delete("/chat/history/{user_id}")
    def clear_history(user_id: str) -> dict:
        cleared = history_store.clear(user_id)
        return {"user_id": user_id, "cleared": cleared}

    return router
