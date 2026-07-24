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
- `GET /onboarding/questions`: list onboarding start questions
- `POST /onboarding/submit`: save user onboarding profile
- `GET /onboarding/{user_id}`: read saved onboarding profile
- `DELETE /onboarding/{user_id}`: clear onboarding profile
- `POST /chat`: single request
- `POST /chat/batch`: batch requests
- `GET /chat/history/{user_id}`: get stored chat history for user
- `DELETE /chat/history/{user_id}`: clear stored chat history for user

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

- History storage is in-memory and resets when the server restarts.
- History is stored per `user_id`.
- `use_history=true` lets follow-up prompts reuse previous turns.

## CLI Onboarding

When running `python -m chatbot.cli`, onboarding questions are asked at startup before normal chat begins.

## Project Structure

- `chatbot/logger_config.py`: logging configuration
- `chatbot/engine.py`: chatbot logic with retries and concurrency
- `chatbot/planner.py`: meal and training plan generation from prompts
- `chatbot/demo.py`: runnable demonstration
- `chatbot/cli.py`: interactive terminal chatbot
- `chatbot/api.py`: FastAPI HTTP service
