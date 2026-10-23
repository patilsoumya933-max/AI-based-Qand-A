
"""Load and validate application settings from the environment."""

import math
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PLACEHOLDER_KEYS = {
    "your_gemini_api_key_here",
    "your_api_key_here",
    "replace_me",
    "example",
}


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Validated configuration used by the Flask app and Gemini service."""

    api_key: str = field(repr=False)
    model: str = "gemini-4-argon"
    temperature: float = 0.2
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False


def _parse_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be a boolean value.")


def get_settings() -> Settings:
    """Load settings from the project-level .env file."""
    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.lower() in _PLACEHOLDER_KEYS:
        raise ConfigurationError(
            "GEMINI_API_KEY is missing or contains a placeholder. "
            "Set it in your .env file."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-4-argon").strip()
    if not model:
        raise ConfigurationError("GEMINI_MODEL must not be empty.")

    try:
        temperature = float(os.getenv("TEMPERATURE", "0.2"))
    except ValueError as error:
        raise ConfigurationError(
            "TEMPERATURE must be a number between 0 and 2."
        ) from error

    if not math.isfinite(temperature) or not 0 <= temperature <= 2:
        raise ConfigurationError("TEMPERATURE must be a number between 0 and 2.")

    host = os.getenv("FLASK_HOST", "127.0.0.1").strip()
    if not host:
        raise ConfigurationError("FLASK_HOST must not be empty.")

    try:
        port = int(os.getenv("FLASK_PORT", "5000"))
    except ValueError as error:
        raise ConfigurationError(
            "FLASK_PORT must be an integer between 1 and 65535."
        ) from error

    if not 1 <= port <= 65535:
        raise ConfigurationError("FLASK_PORT must be an integer between 1 and 65535.")

    return Settings(
        api_key=api_key,
        model=model,
        temperature=temperature,
        host=host,
        port=port,
        debug=_parse_bool("FLASK_DEBUG", False),
    )
