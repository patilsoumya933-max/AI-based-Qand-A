"""Flask application routes and local development entry point."""

import logging
from collections.abc import Mapping
from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from app.config.settings import Settings, get_settings
from app.services.gemini_service import ChatMessage, GeminiService, GeminiServiceError
from app.utils.logging_config import configure_logging

logger = logging.getLogger(__name__)
MAX_HISTORY_MESSAGES = 40
MAX_MESSAGE_LENGTH = 8_000


def create_app(
    settings: Settings | None = None,
    service: GeminiService | None = None,
) -> Flask:
    """Create the configured Flask application."""
    configure_logging()
    resolved_settings = settings or get_settings()
    answer_service = service if service is not None else GeminiService(resolved_settings)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.extensions["qa_service"] = answer_service

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/health")
    def health() -> Any:
        return jsonify({"status": "ok"})

    @app.post("/api/chat")
    def chat() -> Any:
        if not request.is_json:
            return jsonify({"error": "Request body must use application/json."}), 415

        try:
            payload = request.get_json()
        except BadRequest:
            return jsonify({"error": "Request body must contain valid JSON."}), 400
        if not isinstance(payload, Mapping):
            return jsonify({"error": "Request body must be a JSON object."}), 400

        question = payload.get("question")
        history = payload.get("history", [])
        if not isinstance(question, str) or not question.strip():
            return jsonify({"error": "Enter a question before sending."}), 400
        if len(question) > MAX_MESSAGE_LENGTH:
            return jsonify({"error": "Question is too long. Keep it under 8,000 characters."}), 400
        if not isinstance(history, list) or len(history) > MAX_HISTORY_MESSAGES:
            return jsonify({"error": "Conversation history is invalid or too long."}), 400

        messages: list[ChatMessage] = []
        for message in history:
            if (
                not isinstance(message, Mapping)
                or message.get("role") not in {"user", "assistant"}
                or not isinstance(message.get("content"), str)
                or not message["content"].strip()
                or len(message["content"]) > MAX_MESSAGE_LENGTH
            ):
                return jsonify({"error": "Conversation history contains an invalid message."}), 400
            messages.append(
                {"role": message["role"], "content": message["content"]}
            )
        messages.append({"role": "user", "content": question.strip()})

        try:
            answer = answer_service.generate_answer(messages)
        except GeminiServiceError as error:
            return jsonify({"error": str(error)}), 502

        return jsonify({"answer": answer})

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_request(_: RequestEntityTooLarge) -> Any:
        return jsonify({"error": "Request is too large."}), 413

    logger.info("Question-answering application initialized.")
    return app


def main() -> None:
    """Run the Flask development server using validated environment settings."""
    settings = get_settings()
    application = create_app(settings)
    application.run(host=settings.host, port=settings.port, debug=settings.debug)


if __name__ == "__main__":
    main()
