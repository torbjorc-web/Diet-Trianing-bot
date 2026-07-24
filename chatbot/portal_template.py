def get_portal_html() -> str:
    return """<!doctype html>
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
            <label>Admin View Code (owner only)</label>
            <input id=\"admin_code\" placeholder=\"Optional admin code\" />
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

        <div class=\"card\">
            <h2>3) Owner Tools</h2>
            <p>Use this section to inspect what users submitted to the bot.</p>
            <label>Date Window</label>
            <select id=\"admin_window\">
                <option value=\"today\">today</option>
                <option value=\"7d\" selected>7d</option>
                <option value=\"30d\">30d</option>
                <option value=\"all\">all</option>
            </select>
            <button onclick=\"loadAdminUsers()\">Show Users and Profiles</button>
            <button class=\"secondary\" onclick=\"loadAdminInputs()\">Show Recent Chat Inputs</button>
            <button class=\"secondary\" onclick=\"exportAdminCsv()\">Export CSV</button>
            <pre id=\"admin_result\">No admin query yet.</pre>
        </div>
    </div>

    <script>
        let shareUrls = [];

        function v(id) { return document.getElementById(id).value; }
        function setv(id, value) { document.getElementById(id).value = value; }
        function show(id, value) {
            document.getElementById(id).textContent = typeof value === \"string\" ? value : JSON.stringify(value, null, 2);
        }

        function loadInviteFromUrl() {
            const params = new URLSearchParams(window.location.search);
            const invite = (params.get(\"invite\") || \"\").trim();
            if (invite) {
                setv(\"invite_code\", invite);
            }
        }

        function inviteCode() {
            return (v(\"invite_code\") || \"\").trim();
        }

        function adminCode() {
            return (v(\"admin_code\") || \"\").trim();
        }

        function adminWindow() {
            return (v(\"admin_window\") || \"7d\").trim();
        }

        function withInvite(path) {
            const code = inviteCode();
            if (!code) {
                return path;
            }
            const sep = path.includes(\"?\") ? \"&\" : \"?\";
            return `${path}${sep}invite=${encodeURIComponent(code)}`;
        }

        function requestHeaders() {
            const code = inviteCode();
            const headers = { \"Content-Type\": \"application/json\" };
            if (code) {
                headers[\"x-invite-code\"] = code;
            }
            return headers;
        }

        function adminHeaders() {
            const headers = requestHeaders();
            const code = adminCode();
            if (code) {
                headers[\"x-admin-code\"] = code;
            }
            return headers;
        }

        async function loadShareLinks() {
            const res = await fetch(withInvite(\"/portal/share-links\"));
            const data = await res.json();
            shareUrls = data.urls || [];
            if (!shareUrls.length) {
                show(\"share_result\", \"No share links found.\");
                return;
            }
            const text = [
                \"Share links:\",
                ...shareUrls.map((u, i) => `${i + 1}. ${u}`),
                \"\",
                data.note || \"\",
            ].join(\"\\n\");
            show(\"share_result\", text);
        }

        async function copyPrimaryLink() {
            if (!shareUrls.length) {
                await loadShareLinks();
            }
            const primary = shareUrls[0];
            if (!primary) {
                show(\"share_result\", \"No link available to copy.\");
                return;
            }
            await navigator.clipboard.writeText(primary);
            show(\"share_result\", `Copied: ${primary}`);
        }

        async function submitOnboarding() {
            const payload = {
                user_id: v(\"user_id\"),
                full_name: v(\"full_name\"),
                goal: v(\"goal\"),
                training_level: v(\"training_level\"),
                meal_preference: v(\"meal_preference\"),
                weight_kg: Number(v(\"weight_kg\")) || null,
                health_notes: v(\"health_notes\"),
                training_setting: v(\"training_setting\")
            };

            const res = await fetch(withInvite(\"/onboarding/submit\"), {
                method: \"POST\",
                headers: requestHeaders(),
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            show(\"onboarding_result\", data);
        }

        async function loadOnboarding() {
            const res = await fetch(withInvite(`/onboarding/${encodeURIComponent(v(\"user_id\"))}`));
            const data = await res.json();
            show(\"onboarding_result\", data);
        }

        async function sendChat() {
            const payload = {
                user_id: v(\"user_id\"),
                prompt: v(\"prompt\"),
                use_history: true,
                history_turns: 5,
                use_onboarding: true
            };

            const res = await fetch(withInvite(\"/chat\"), {
                method: \"POST\",
                headers: requestHeaders(),
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            show(\"chat_result\", data.response || data);
        }

        async function loadHistory() {
            const res = await fetch(withInvite(`/chat/history/${encodeURIComponent(v(\"user_id\"))}`));
            const data = await res.json();
            show(\"chat_result\", data);
        }

        async function loadAdminUsers() {
            const code = adminCode();
            const path = code
                ? `/admin/users?admin=${encodeURIComponent(code)}`
                : \"/admin/users\";
            const res = await fetch(withInvite(path), { headers: adminHeaders() });
            const data = await res.json();
            show(\"admin_result\", data);
        }

        async function loadAdminInputs() {
            const code = adminCode();
            const window = encodeURIComponent(adminWindow());
            const path = code
                ? `/admin/chat-inputs?limit=200&window=${window}&admin=${encodeURIComponent(code)}`
                : `/admin/chat-inputs?limit=200&window=${window}`;
            const res = await fetch(withInvite(path), { headers: adminHeaders() });
            const data = await res.json();
            show(\"admin_result\", data);
        }

        async function exportAdminCsv() {
            const code = adminCode();
            const window = encodeURIComponent(adminWindow());
            const path = code
                ? `/admin/chat-inputs.csv?limit=1000&window=${window}&admin=${encodeURIComponent(code)}`
                : `/admin/chat-inputs.csv?limit=1000&window=${window}`;
            const res = await fetch(withInvite(path), { headers: adminHeaders() });
            if (!res.ok) {
                const data = await res.json();
                show(\"admin_result\", data);
                return;
            }
            const text = await res.text();
            const blob = new Blob([text], { type: \"text/csv;charset=utf-8\" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement(\"a\");
            a.href = url;
            a.download = `chat-inputs-${adminWindow()}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            show(\"admin_result\", \"CSV export completed.\");
        }

        loadInviteFromUrl();
        loadShareLinks();
    </script>
</body>
</html>
"""
