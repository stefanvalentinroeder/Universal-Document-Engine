from __future__ import annotations

from fastapi.testclient import TestClient

from ude_api.config import Settings
from ude_api.main import create_app
from ude_backend_db import ReadinessResult


class StaticReadinessProbe:
    def __init__(self, result: ReadinessResult) -> None:
        self._result = result

    async def check(self) -> ReadinessResult:
        return self._result


class StaticStorageHealth:
    def __init__(self, ready: bool) -> None:
        self._ready = ready

    async def is_ready(self) -> bool:
        return self._ready


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://ude:test@localhost:5432/ude_test",
        minio_endpoint="http://localhost:9000",
        cors_origins="http://localhost:3000,http://localhost:3001",
    )


def test_health_is_live_and_returns_a_correlation_id() -> None:
    app = create_app(make_settings())
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "test-request-1"})

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ude-api"}
    assert response.headers["X-Request-ID"] == "test-request-1"


def assert_readiness_response(
    *,
    database_ready: bool,
    object_storage_ready: bool,
    expected_status_code: int,
) -> None:
    app = create_app(make_settings())
    app.state.readiness_probe = StaticReadinessProbe(
        ReadinessResult(
            ready=database_ready,
            detail="available" if database_ready else "unavailable",
        )
    )
    app.state.storage_health = StaticStorageHealth(object_storage_ready)
    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == expected_status_code
    assert response.json() == {
        "status": "ready" if expected_status_code == 200 else "not_ready",
        "checks": {
            "database": {"status": "up" if database_ready else "down"},
            "object_storage": {"status": "up" if object_storage_ready else "down"},
        },
    }


def test_ready_when_both_dependencies_are_available() -> None:
    assert_readiness_response(
        database_ready=True,
        object_storage_ready=True,
        expected_status_code=200,
    )


def test_ready_when_only_database_is_unavailable() -> None:
    assert_readiness_response(
        database_ready=False,
        object_storage_ready=True,
        expected_status_code=503,
    )


def test_ready_when_only_object_storage_is_unavailable() -> None:
    assert_readiness_response(
        database_ready=True,
        object_storage_ready=False,
        expected_status_code=503,
    )


def test_ready_when_both_dependencies_are_unavailable() -> None:
    assert_readiness_response(
        database_ready=False,
        object_storage_ready=False,
        expected_status_code=503,
    )


def test_http_errors_use_the_consistent_error_envelope() -> None:
    app = create_app(make_settings())
    with TestClient(app) as client:
        response = client.get("/not-a-route")

    payload = response.json()
    assert response.status_code == 404
    assert payload["error"]["code"] == "http_error"
    assert payload["error"]["message"] == "Not Found"
    assert payload["error"]["request_id"] == response.headers["X-Request-ID"]


def test_unhandled_errors_preserve_the_correlation_id() -> None:
    app = create_app(make_settings())

    @app.get("/test-only-failure")
    async def test_only_failure() -> None:
        message = "synthetic failure"
        raise RuntimeError(message)

    with TestClient(app) as client:
        response = client.get(
            "/test-only-failure",
            headers={"X-Request-ID": "failure-request-1"},
        )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "An internal error occurred",
            "request_id": "failure-request-1",
        }
    }
    assert response.headers["X-Request-ID"] == "failure-request-1"


def test_openapi_is_available() -> None:
    app = create_app(make_settings())
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Universal Document Engine API"
