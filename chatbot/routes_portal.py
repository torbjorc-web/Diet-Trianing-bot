import socket

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


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


def create_portal_router(portal_html: str) -> APIRouter:
    router = APIRouter(tags=["portal"])

    @router.get("/", response_class=HTMLResponse)
    def portal_home() -> str:
        return portal_html

    @router.get("/portal", response_class=HTMLResponse)
    def portal_page() -> str:
        return portal_html

    @router.get("/portal/share-links")
    def portal_share_links(request: Request) -> dict:
        return {
            "urls": _get_portal_share_urls(request),
            "note": "People on your local network can use a LAN URL if your firewall allows port 8000.",
        }

    return router
