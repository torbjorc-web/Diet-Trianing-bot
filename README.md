# Diet-Training Bot (Python)

A chatbot demo where users can ask for:

- meal plans
- training plans
- combined meal and training plans

The implementation also focuses on:

- concurrency (multiple users processed in parallel)
- structured logging (console + log file)
- robust error handling (validation, retries, fallback replies)

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Run one of the modes:

Demo:

```bash
python -m chatbot.demo
```

Interactive CLI:

```bash
python -m chatbot.cli
```

FastAPI server:

```bash
uvicorn chatbot.api:app --reload
```

Customer portal (no Swagger needed):

Open `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/portal`.
The user can fill onboarding fields and chat directly from the web page.
The portal also includes a Share Links panel with one-click copy.

On Render, the Share Links panel now only shows the public `*.onrender.com` portal URL.

Then call:

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"alice\",\"prompt\":\"make both meal and training plan for fat loss\"}"
```

## What The Demo Shows

- Concurrent processing of multiple chat requests.
- Plan generation from natural-language prompts (goal, diet style, training level/days).
- Centralized logging setup in `logs/chatbot.log`.
- Retry logic for transient AI-provider errors.
- Graceful fallback messages for retries, timeouts, and validation issues.

## API Endpoints

- `GET /health`: health check
- `GET /`: simple customer portal UI
- `GET /portal`: simple customer portal UI
- `GET /portal/share-links`: suggest local and LAN shareable portal URLs
- `GET /onboarding/questions`: list onboarding start questions
- `POST /onboarding/submit`: save user onboarding profile
- `GET /onboarding/{user_id}`: read saved onboarding profile
- `DELETE /onboarding/{user_id}`: clear onboarding profile
- `POST /chat`: single request
- `POST /chat/batch`: batch requests
- `GET /chat/history/{user_id}`: get stored chat history for user
- `DELETE /chat/history/{user_id}`: clear stored chat history for user
- `GET /admin/users`: owner-only list of users and onboarding profiles
- `GET /admin/chat-inputs?limit=200`: owner-only recent user prompts and bot responses
- `GET /admin/chat-inputs?limit=200&window=today|7d|30d|all`: filtered owner view
- `GET /admin/chat-inputs.csv?limit=1000&window=today|7d|30d|all`: CSV export

## Onboarding Start Point

Before chat planning, ask and store onboarding data for each user:

- full name for personalized greeting
- goal for using the bot
- training level
- meal preference: halal, kosher, vegan, vegetarian, or none
- current weight
- health issues/injuries
- preferred training setup: studio, group, or self

Example onboarding submit payload:

```json
{
  "user_id": "alice",
  "full_name": "Anna Hansen",
  "goal": "fat loss",
  "training_level": "beginner",
  "meal_preference": "halal",
  "weight_kg": 78,
  "health_notes": "knee discomfort",
  "training_setting": "studio"
}
```

Tip: keep `user_id` stable for each person (for example `anna`), and use `full_name`
for the friendly greeting in responses.

The chat endpoint can automatically use this profile context with `use_onboarding=true`.

Validation note: `meal_preference` is strictly validated by the API and must be one of
`halal`, `kosher`, `vegan`, `vegetarian`, or `none`. Unsupported values return HTTP 422.

## Running Tests

Install the test dependencies and run the suite from the repository root:

```bash
pip install -r requirements-dev.txt
pytest
```

Useful variations:

```bash
pytest tests/test_planner.py          # one file
pytest -k onboarding                  # match test names
pytest -v                             # verbose output
```

Notes:

- Tests never call a real AI provider or the network: the provider is replaced with a
  deterministic stub, so plan output is stable and no API keys are needed.
- Each test gets a fresh SQLite database in a temporary directory, so onboarding
  profiles and chat history never leak between tests.
- API tests use `fastapi.testclient.TestClient` against the real routes.

## Swagger Examples

After starting the API, open `http://127.0.0.1:8000/docs`.

The `POST /chat` endpoint now includes built-in examples:

- meal plan request
- follow-up request that uses chat history context

You can test follow-ups by sending two requests with the same `user_id`.

Example payload:

```json
{
  "user_id": "alice",
  "prompt": "Adjust the training to 5 days and intermediate level",
  "use_history": true,
  "history_turns": 5
}
```

## Chat History Notes

- History and onboarding are now stored in SQLite (`CHATBOT_DB_PATH`, default: `data/chatbot.db`).
- Data is stored per `user_id`.
- `use_history=true` lets follow-up prompts reuse previous turns.

## Access Protection

- Set `PORTAL_INVITE_CODE` to require an invite code for all portal/API routes except health/docs.
- Clients can send invite code via:
  - query parameter: `?invite=YOUR_CODE`
  - header: `x-invite-code: YOUR_CODE`
- The portal includes an Invite Code input and automatically attaches it to requests.

## Owner Monitoring

- Set `ADMIN_VIEW_CODE` to enable owner-only inspection endpoints.
- Use `x-admin-code` header or `?admin=...` query parameter.
- In the portal, fill **Admin View Code** and use the **Owner Tools** section to inspect user input.
- Owner Tools includes date window filters and a CSV export button.

## Deploy On Render

This project includes `render.yaml` for quick deployment.

If a deploy fails quickly, verify:

- `runtime.txt` is present (pins Python version used on Render).
- `PORTAL_INVITE_CODE` is set in Render dashboard (can be empty while testing).
- Start command is `uvicorn chatbot.api:app --host 0.0.0.0 --port $PORT`.

- Push code to GitHub.
- In Render, click **New +** -> **Blueprint**.
- Select your repository.
- Set environment variables.

- `PORTAL_INVITE_CODE`: your private invite code
- `ADMIN_VIEW_CODE`: your private owner/admin inspection code
- `CHATBOT_DB_PATH`: keep default or set custom path

- Deploy and open.

- `https://<your-render-app>.onrender.com/portal`

Start command used on Render:

```bash
uvicorn chatbot.api:app --host 0.0.0.0 --port $PORT
```

## CLI Onboarding

When running `python -m chatbot.cli`, onboarding questions are asked at startup before normal chat begins.
The CLI asks for both a user id and full name so each person can have a stable profile and friendly greeting.

## Project Structure

- `chatbot/logger_config.py`: logging configuration
- `chatbot/engine.py`: chatbot logic with retries and concurrency
- `chatbot/planner.py`: meal and training plan generation from prompts
- `chatbot/portal_template.py`: customer portal HTML/JS template
- `chatbot/admin_reporting.py`: owner reporting filters and CSV formatting
- `chatbot/schemas.py`: shared request models for API routes
- `chatbot/routes_chat.py`: chat endpoints and contextual prompt flow
- `chatbot/routes_onboarding.py`: onboarding endpoints and profile persistence flow
- `chatbot/routes_admin.py`: owner/admin inspection and CSV export endpoints
- `chatbot/routes_portal.py`: portal page endpoints and share-link endpoint
- `chatbot/security.py`: invite/admin code extraction and invite middleware
- `chatbot/demo.py`: runnable demonstration
- `chatbot/cli.py`: interactive terminal chatbot
- `chatbot/api.py`: FastAPI app setup, middleware, health and portal endpoints
- `tests/`: pytest suite (unit tests plus `TestClient` API tests)
