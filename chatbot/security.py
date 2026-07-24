from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse


PUBLIC_PATHS = {
    "/",
    "/portal",
    "/portal/share-links",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
}


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS


def extract_invite_code(request: Request) -> str:
    header_code = request.headers.get("x-invite-code", "").strip()
    if header_code:
        return header_code
    query_code = request.query_params.get("invite", "").strip()
    return query_code


def extract_admin_code(request: Request) -> str:
    header_code = request.headers.get("x-admin-code", "").strip()
    if header_code:
        return header_code
    query_code = request.query_params.get("admin", "").strip()
    return query_code


def create_invite_code_middleware(invite_code: str) -> Callable[[Request, Callable], Awaitable]:
    async def invite_code_middleware(request: Request, call_next):
        if not invite_code:
            return await call_next(request)

        if is_public_path(request.url.path):
            return await call_next(request)

        supplied_code = extract_invite_code(request)
        if supplied_code != invite_code:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Unauthorized. Provide valid invite code via ?invite=... or x-invite-code header.",
                },
            )

        return await call_next(request)

    return invite_code_middleware
