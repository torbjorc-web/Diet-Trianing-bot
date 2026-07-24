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


def _get_admin_login_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Admin Login</title>
    <style>
        :root {
            --bg: #eef3f7;
            --panel: #ffffff;
            --line: #d7dee6;
            --text: #13212d;
            --muted: #526170;
            --accent: #1f6eb5;
            --accent2: #16578f;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Segoe UI, Tahoma, sans-serif;
            color: var(--text);
            background: linear-gradient(180deg, #f4f8fb, #e9f0f6);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 20px;
        }
        .card {
            width: min(640px, 100%);
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }
        h1 { margin: 0 0 8px; }
        p { margin: 0 0 14px; color: var(--muted); }
        label { display: block; margin: 8px 0 4px; font-size: 13px; color: var(--muted); }
        input, select {
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 10px;
            font-size: 14px;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 160px;
            gap: 10px;
        }
        .actions { margin-top: 12px; }
        button {
            border: 0;
            border-radius: 10px;
            padding: 10px 14px;
            color: white;
            background: var(--accent);
            cursor: pointer;
            font-weight: 600;
            margin-right: 8px;
        }
        button.secondary { background: #425568; }
        button:hover { background: var(--accent2); }
        pre {
            white-space: pre-wrap;
            margin-top: 12px;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 10px;
            background: #f6f9fc;
            min-height: 82px;
        }
        .links { margin-top: 12px; display: grid; gap: 8px; }
        .links a { color: var(--accent2); word-break: break-all; }
        @media (max-width: 620px) { .row { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="card">
        <h1>Admin Login</h1>
        <p>Enter invite and admin code, then open the admin pages.</p>

        <label>Invite Code</label>
        <input id="invite" placeholder="inv-..." />

        <label>Admin Code</label>
        <input id="admin" placeholder="adm-..." />

        <label>Window</label>
        <div class="row">
            <input id="limit" type="number" value="200" min="1" max="1000" />
            <select id="window">
                <option value="today">today</option>
                <option value="7d" selected>7d</option>
                <option value="30d">30d</option>
                <option value="all">all</option>
            </select>
        </div>

        <div class="actions">
            <button onclick="verifyAccess()">Verify Access</button>
            <button class="secondary" onclick="openUsers()">Open Users</button>
            <button class="secondary" onclick="openInputs()">Open Inputs</button>
            <button class="secondary" onclick="openCsv()">Open CSV</button>
        </div>

        <pre id="result">Not verified yet.</pre>

        <div class="links">
            <a id="users_link" href="#"></a>
            <a id="inputs_link" href="#"></a>
            <a id="csv_link" href="#"></a>
        </div>
    </div>

    <script>
        function v(id) { return document.getElementById(id).value.trim(); }
        function setText(id, text) { document.getElementById(id).textContent = text; }
        function setLink(id, label, url) {
            const a = document.getElementById(id);
            a.href = url;
            a.textContent = label + ': ' + url;
        }

        function qp(obj) {
            const p = new URLSearchParams();
            Object.entries(obj).forEach(([k, val]) => {
                if (String(val || '').trim()) p.set(k, String(val));
            });
            return p.toString();
        }

        function build() {
            const invite = v('invite');
            const admin = v('admin');
            const limit = v('limit') || '200';
            const window = v('window') || '7d';

            const users = '/admin/users?' + qp({ invite, admin });
            const inputs = '/admin/chat-inputs?' + qp({ limit, window, invite, admin });
            const csv = '/admin/chat-inputs.csv?' + qp({ limit: 1000, window, invite, admin });

            setLink('users_link', 'Users', users);
            setLink('inputs_link', 'Inputs', inputs);
            setLink('csv_link', 'CSV', csv);
            return { users, inputs, csv, invite, admin };
        }

        async function verifyAccess() {
            const { users, invite, admin } = build();
            const headers = {};
            if (invite) headers['x-invite-code'] = invite;
            if (admin) headers['x-admin-code'] = admin;
            const res = await fetch(users, { headers });
            const text = await res.text();
            setText('result', 'Status: ' + res.status + '\\n' + text);
        }

        function openUsers() { const { users } = build(); window.open(users, '_blank', 'noopener'); }
        function openInputs() { const { inputs } = build(); window.open(inputs, '_blank', 'noopener'); }
        function openCsv() { const { csv } = build(); window.open(csv, '_blank', 'noopener'); }

        const inviteFromUrl = new URLSearchParams(window.location.search).get('invite') || '';
        if (inviteFromUrl) {
            document.getElementById('invite').value = inviteFromUrl;
        }
        build();
    </script>
</body>
</html>
"""


def create_portal_router(portal_html: str) -> APIRouter:
    router = APIRouter(tags=["portal"])

    @router.get("/", response_class=HTMLResponse)
    def portal_home() -> str:
        return portal_html

    @router.get("/portal", response_class=HTMLResponse)
    def portal_page() -> str:
        return portal_html

    @router.get("/admin", response_class=HTMLResponse)
    @router.get("/admin/login", response_class=HTMLResponse)
    def admin_login_page() -> str:
        return _get_admin_login_html()

    @router.get("/portal/share-links")
    def portal_share_links(request: Request) -> dict:
        return {
            "urls": _get_portal_share_urls(request),
            "note": "People on your local network can use a LAN URL if your firewall allows port 8000.",
        }

    return router
