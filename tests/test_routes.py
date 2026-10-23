"""Flask route tests without network requests."""

from unittest.mock import Mock

import pytest

from app.config.settings import Settings
from app.main import create_app
from app.services.gemini_service import GeminiServiceError


@pytest.fixture
def service() -> Mock:
    mock = Mock()
    mock.generate_answer.return_value = "A helpful answer."
    return mock


@pytest.fixture
def client(service: Mock):
    app = create_app(Settings(api_key="test-key"), service=service)
    app.config["TESTING"] = True
    return app.test_client()


def test_homepage_renders_chat_interface(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert b"What\xe2\x80\x99s on your mind?" in response.data


def test_health_does_not_expose_configuration(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_chat_sends_question_and_history(client, service: Mock) -> None:
    history = [{"role": "user", "content": "First"}, {"role": "assistant", "content": "Reply"}]

    response = client.post(
        "/api/chat",
        json={"question": "Follow up", "history": history},
    )

    assert response.status_code == 200
    assert response.get_json() == {"answer": "A helpful answer."}
    service.generate_answer.assert_called_once_with(
        history + [{"role": "user", "content": "Follow up"}]
    )


def test_chat_rejects_non_json_request(client) -> None:
    response = client.post("/api/chat", data="question=hello")

    assert response.status_code == 415
    assert "error" in response.get_json()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"question": " "},
        {"question": "hello", "history": "not a list"},
        {"question": "hello", "history": [{"role": "system", "content": "bad"}]},
    ],
)
def test_chat_rejects_invalid_payload(client, payload) -> None:
    response = client.post("/api/chat", json=payload)

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_chat_returns_safe_model_error(client, service: Mock) -> None:
    service.generate_answer.side_effect = GeminiServiceError("Try again.")

    response = client.post("/api/chat", json={"question": "hello"})

    assert response.status_code == 502
    assert response.get_json() == {"error": "Try again."}


def test_chat_rejects_oversized_body(client) -> None:
    response = client.post(
        "/api/chat",
        data='{"question":"' + ("x" * (65 * 1024)) + '"}',
        content_type="application/json",
    )

    assert response.status_code == 413
    assert response.get_json() == {"error": "Request is too large."}
