from __future__ import annotations

from fastapi import FastAPI

from ude_api.config import Settings
from ude_api.main import create_app


def main() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://ude:validation@localhost:5432/ude",
        minio_endpoint="http://localhost:9000",
        cors_origins="http://localhost:3000,http://localhost:3001",
    )
    app = create_app(settings)
    if not isinstance(app, FastAPI):
        message = "Application factory did not return a FastAPI application"
        raise TypeError(message)
    openapi = app.openapi()
    required_paths = {"/health", "/ready"}
    if not required_paths.issubset(openapi["paths"]):
        message = "Operational endpoints are absent from the OpenAPI contract"
        raise RuntimeError(message)
    print("FastAPI factory and OpenAPI contract validated.")


if __name__ == "__main__":
    main()
