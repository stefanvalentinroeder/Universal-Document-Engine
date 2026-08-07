# ADR-006: Host-run applications with containerized local infrastructure

## Status

Accepted.

## Context

Normal development must work on Windows, macOS, and Linux with fast reloads while
PostgreSQL and S3-compatible storage remain reproducible.

## Decision

Run PostgreSQL and MinIO through Docker Compose. Run Next.js and FastAPI on the host
through pinned pnpm and uv environments. Cross-platform Node scripts coordinate
setup and development.

## Consequences

Debugging and reload cycles remain fast, and stateful dependencies are consistent.
Developers install Node, Python/uv, and Docker instead of only Docker. Production
container packaging remains a separate approved order.

## Rejected alternatives

- Containerize every development process: rejected because host debugging and file
  watching are less consistent across desktop platforms.
- Install databases directly: rejected because setup and versions would drift.
- Unix shell scripts: rejected because normal Windows development is required.
