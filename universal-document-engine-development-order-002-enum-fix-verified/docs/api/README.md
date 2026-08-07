# API foundation

The FastAPI factory is `ude_api.main:create_app`. It produces OpenAPI at
`/openapi.json`, Swagger UI at `/docs`, and ReDoc at `/redoc`.

## Operational endpoints

| Endpoint      | Purpose                | Dependency behavior                  |
| ------------- | ---------------------- | ------------------------------------ |
| `GET /health` | Process liveness       | Does not contact infrastructure      |
| `GET /ready`  | Ability to accept work | Checks PostgreSQL and object storage |

`GET /ready` executes a minimal database query and calls MinIO's readiness endpoint
concurrently. It returns HTTP `200` only when both checks succeed and HTTP `503`
when either or both fail. Its public payload intentionally contains no URLs,
credentials, exception messages, or provider internals.

Ready response:

```json
{
  "status": "ready",
  "checks": {
    "database": { "status": "up" },
    "object_storage": { "status": "up" }
  }
}
```

Unavailable response example:

```json
{
  "status": "not_ready",
  "checks": {
    "database": { "status": "up" },
    "object_storage": { "status": "down" }
  }
}
```

Every HTTP response receives an `X-Request-ID`. A safe supplied identifier is
preserved; otherwise the API generates one. Error responses use this shape:

```json
{
  "error": {
    "code": "http_error",
    "message": "Not Found",
    "request_id": "..."
  }
}
```

The `/api/v1` router is registered but intentionally contains no business route.
When application endpoints are approved, OpenAPI will become the only contract
source for a generated client under `libs/frontend/api-client`.

## Persistence boundary

The API currently exposes no domain CRUD routes. Its database metadata is defined
by `ude_backend_db.models`, while API schemas will remain separate from ORM models
when endpoints are approved. The `Database.session()` boundary opens one async
SQLAlchemy transaction per use; it commits on success and rolls back on error.
The persistent core model, its tenant constraints, immutable version guarantees,
and deferred RLS decision are documented in
`docs/architecture/CORE_DOMAIN_MODEL.md`.
