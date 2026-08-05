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
