# ADR-007: Asynchronous SQLAlchemy with Alembic

## Status

Accepted.

## Context

FastAPI must perform non-blocking database readiness and future persistence while
retaining explicit session ownership and mature migrations.

## Decision

Use SQLAlchemy's asynchronous engine with asyncpg and an explicit `Database`
session boundary. Use Alembic for schema migration. The first migration is an empty
baseline and creates no business table.

## Consequences

Database I/O fits the API execution model and can be replaced in tests through
narrow probes. Callers must manage asynchronous sessions deliberately. Alembic
autogeneration requires reviewed metadata when domain tables are later approved.

## Rejected alternatives

- Synchronous access inside request handlers: rejected because it can block the
  event loop.
- A bespoke migration system: rejected as unnecessary risk.
- Creating a speculative tenant schema now: rejected as outside this order.
