from typing import Callable, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from chatbot.admin_reporting import filter_records_by_window, records_to_csv
from chatbot.onboarding import profile_to_dict


def create_admin_router(
    history_store,
    onboarding_store,
    admin_view_code: str,
    extract_admin_code: Callable[[Request], str],
) -> APIRouter:
    router = APIRouter(tags=["admin"])

    def assert_admin(request: Request) -> None:
        if not admin_view_code:
            raise HTTPException(
                status_code=403,
                detail="Admin inspection is disabled. Set ADMIN_VIEW_CODE to enable.",
            )
        supplied_code = extract_admin_code(request)
        if supplied_code != admin_view_code:
            raise HTTPException(status_code=401, detail="Unauthorized admin access")

    @router.get("/admin/users")
    def admin_users(request: Request) -> dict:
        assert_admin(request)
        chat_user_ids = set(history_store.list_user_ids())
        profiles = onboarding_store.list_profiles()
        profile_user_ids = {profile.user_id for profile in profiles}
        all_user_ids = sorted(chat_user_ids | profile_user_ids)
        return {
            "count": len(all_user_ids),
            "user_ids": all_user_ids,
            "profiles": [profile_to_dict(profile) for profile in profiles],
        }

    @router.get("/admin/chat-inputs")
    def admin_chat_inputs(
        request: Request,
        limit: int = 200,
        window: Literal["today", "7d", "30d", "all"] = "7d",
    ) -> dict:
        assert_admin(request)
        records = history_store.list_recent_records(limit=limit)
        records = filter_records_by_window(records, window)
        return {
            "window": window,
            "count": len(records),
            "records": records,
        }

    @router.get("/admin/chat-inputs.csv", response_class=PlainTextResponse)
    def admin_chat_inputs_csv(
        request: Request,
        limit: int = 1000,
        window: Literal["today", "7d", "30d", "all"] = "7d",
    ) -> PlainTextResponse:
        assert_admin(request)
        records = history_store.list_recent_records(limit=limit)
        records = filter_records_by_window(records, window)

        headers = {
            "Content-Disposition": f"attachment; filename=chat-inputs-{window}.csv"
        }
        return PlainTextResponse(
            content=records_to_csv(records),
            media_type="text/csv",
            headers=headers,
        )

    return router
