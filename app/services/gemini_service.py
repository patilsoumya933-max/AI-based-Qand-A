"""Gemini API integration."""

import logging
from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict

import httpx
from google import genai
from google.genai import errors as genai_errors

from app.config.settings import Settings
from app.prompts.qa_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ChatMessage(TypedDict):
    """A user or assistant message in the conversation history."""

    role: Literal["user", "assistant"]
    content: str


class GeminiServiceError(RuntimeError):
    """Raised when the model cannot return a usable answer."""


class GeminiService:
    """Generate answers through the Gemini API."""

    def __init__(self, settings: Settings, client: genai.Client | None = None) -> None:
        self._model = settings.model
        self._temperature = settings.temperature
        self._client = (
            client
            if client is not None
            else genai.Client(
                api_key=settings.api_key,
                http_options={"timeout": 30_000},
            )
        )

    def generate_answer(self, messages: Sequence[ChatMessage]) -> str:
        """Return an answer for the supplied conversation history."""
        if not messages:
            raise ValueError("At least one conversation message is required.")

        for message in messages:
            if (
                not isinstance(message, Mapping)
                or message.get("role") not in {"user", "assistant"}
                or not isinstance(message.get("content"), str)
                or not message["content"].strip()
            ):
                raise ValueError("Conversation messages must have a valid role and non-empty content.")

        contents = [
            {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [{"text": message["content"]}],
            }
            for message in messages
        ]

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": self._temperature,
                },
            )
        except genai_errors.APIError as error:
            logger.error("Gemini API request failed (status %s).", error.code)
            if error.code in {401, 403}:
                raise GeminiServiceError(
                    "The AI service is not authorized. Check the server configuration."
                ) from None
            if error.code == 429:
                raise GeminiServiceError(
                    "The AI service is busy. Please wait a moment and try again."
                ) from None
            raise GeminiServiceError(
                "The AI service couldn't complete that request. Please try again."
            ) from None
        except (httpx.TimeoutException, httpx.RequestError):
            logger.warning("Gemini connection failed.")
            raise GeminiServiceError(
                "I couldn't connect to the AI service. Please try again."
            ) from None
        answer = response.text
        if not isinstance(answer, str) or not answer.strip():
            logger.error("Gemini returned an empty response.")
            raise GeminiServiceError(
                "The AI service returned an empty answer. Please try again."
            )

        logger.info("Generated an answer successfully.")
        return answer.strip()