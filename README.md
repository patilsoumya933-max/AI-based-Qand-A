# Clarity — AI Question & Answering

A responsive, ChatGPT-style question-answering web app with a Flask backend and a vanilla HTML/CSS/JavaScript frontend. Model requests use the official Google Gen AI Python SDK and Gemini API. Conversation history lives only in the open browser tab and is sent to the server only when asking a follow-up; the application does not persist it.

## Features

- Responsive chat UI with starter prompts, Markdown-style answer formatting, and keyboard-friendly message entry.
- Flask JSON endpoints with content validation, safe error responses, and request size limits.
- Gemini API integration behind a service boundary, with request timeouts and sanitized errors.
- No credentials or full conversation contents in application logs.
- Tests use mocked Gemini responses and do not require a key or network access.

## Project structure

```text
question_answering_app/
├── app/
│   ├── config/          # Validated environment settings
│   ├── prompts/         # Model system instructions
│   ├── services/        # Gemini API integration
│   ├── static/          # Vanilla JavaScript and CSS
│   ├── templates/       # HTML
│   ├── utils/           # Logging
│   └── main.py          # Flask app factory, routes, local entry point
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── run.sh
```

## Requirements

- Python 3.11 or newer
- A Gemini API key with access to the configured model

## Setup

Run these commands from this directory. Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and replace `GEMINI_API_KEY` with your actual key. Never commit `.env`; it is excluded by `.gitignore`. The app refuses to start while the key is missing or still contains the example placeholder.

Available configuration:

| Variable | Default | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | Required | Server-side Gemini API key |
| `GEMINI_MODEL` | `gemini-4-argon` | Gemini model used to generate answers |
| `TEMPERATURE` | `0.2` | Sampling temperature from 0 to 2 |
| `FLASK_HOST` | `127.0.0.1` | Development server bind address |
| `FLASK_PORT` | `5000` | Development server port |
| `FLASK_DEBUG` | `false` | Enables Flask debug mode only when explicitly set |

## Run

```powershell
python -m app.main
```

Open <http://127.0.0.1:5000>. On macOS/Linux, `./run.sh` is also available. This built-in Flask server is intended for local development; use a production WSGI server and deployment-specific secret management when hosting the app.

## API

- `GET /` — chat interface.
- `GET /api/health` — minimal health response, `{"status":"ok"}`.
- `POST /api/chat` — JSON request with `question` and optional `history`:

```json
{
  "question": "Can you give me an example?",
  "history": [
    {"role": "user", "content": "Explain recursion."},
    {"role": "assistant", "content": "Recursion is when..."}
  ]
}
```

Responses contain `{"answer":"..."}` on success or `{"error":"..."}` with an appropriate HTTP status on failure. Requests are limited to 64 KiB; each message is limited to 8,000 characters and history to 40 messages.

## Tests

```powershell
python -m pytest
```

The test suite does not call Gemini. The API key must never be placed in frontend code; the browser calls only the local Flask endpoint.

## Operational notes

- The app does not save conversation history to disk or a database. Clearing the current chat resets the browser-side conversation.
- Chat requests and history are sent to the configured Gemini model to generate answers; avoid submitting data you are not authorized to share.
- Review model availability and pricing in Google AI Studio before deployment.
