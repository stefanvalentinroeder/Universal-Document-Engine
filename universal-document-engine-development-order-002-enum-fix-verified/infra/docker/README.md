# Local containers

Docker Compose runs only stateful infrastructure in normal development:

- PostgreSQL on port `5432`;
- MinIO API on port `9000`;
- MinIO console on port `9001`.

The web, admin, and API processes run on the host for fast reloads and consistent
debugging on Windows, macOS, and Linux. See ADR-006 for the rationale.

The named volumes `postgres_data` and `minio_data` persist local state. Running
`docker compose down` keeps both volumes. Removal with `--volumes` is destructive
and is therefore intentionally not part of any project script.
