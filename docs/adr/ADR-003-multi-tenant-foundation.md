# ADR-003: Multi-tenant isolation is foundational

## Status

Accepted.

## Context

Adding tenant ownership after business tables and repositories exist creates a high
risk of cross-customer access and costly schema corrections.

## Decision

Every future tenant-owned operation must require explicit verified tenant context,
and every tenant-owned table must carry an immutable non-null tenant identifier.
Database-level isolation and cross-tenant tests are mandatory before production
data is stored.

## Consequences

Interfaces and indexes are tenant-aware from their first implementation. Some
queries and administration tasks become more explicit. A complete tenant model,
authentication, and RBAC remain outside this order.

## Rejected alternatives

- Add tenant columns later: rejected as unsafe and migration-heavy.
- One database per tenant from day one: rejected because operational requirements
  are not yet known.
- Application filters only: rejected because a missed filter can expose data.
