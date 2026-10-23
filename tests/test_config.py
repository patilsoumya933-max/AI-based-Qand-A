"""Configuration tests."""

import pytest

from app.config.settings import ConfigurationError, get_settings


def test_get_settings_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.config.settings.load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("TEMPERATURE", raising=False)

    settings = get_settings()

    assert settings.api_key == "test-key"
    assert settings.model == "gemini-4-argon"
    assert settings.temperature == 0.2
    assert "test-key" not in repr(settings)


def test_get_settings_reads_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setenv("TEMPERATURE", "0.7")

    settings = get_settings()

    assert settings.model == "gemini-test"
    assert settings.temperature == 0.7


def test_get_settings_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.config.settings.load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        get_settings()


def test_get_settings_rejects_example_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "your_gemini_api_key_here")

    with pytest.raises(ConfigurationError, match="placeholder"):
        get_settings()


@pytest.mark.parametrize("temperature", ["-0.1", "2.1", "nan", "not-a-number"])
def test_get_settings_rejects_invalid_temperature(
    monkeypatch: pytest.MonkeyPatch, temperature: str
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("TEMPERATURE", temperature)

    with pytest.raises(ConfigurationError, match="TEMPERATURE"):
        get_settings()


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("FLASK_PORT", "70000", "FLASK_PORT"),
        ("FLASK_PORT", "not-a-number", "FLASK_PORT"),
        ("FLASK_DEBUG", "sometimes", "FLASK_DEBUG"),
    ],
)
def test_get_settings_rejects_invalid_server_config(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str, message: str
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv(name, value)

    with pytest.raises(ConfigurationError, match=message):
        get_settings()