# ADR-002: One codebase for cloud and on-premise deployment

## Status

Accepted.

## Context

UDE must support managed cloud operation and customer-controlled on-premise
operation without divergent product implementations.

## Decision

Maintain one codebase. Infrastructure-specific behavior is supplied through
environment configuration and internal ports. Application and engine code must not
depend directly on a cloud vendor.

## Consequences

Feature behavior can remain consistent across deployments and security fixes have
one source. Provider capabilities must be normalized, deployment configuration is
more explicit, and each supported target will require integration tests.

## Rejected alternatives

- Cloud-only services: rejected because they prevent approved on-premise use.
- Separate cloud and on-premise forks: rejected because they create drift.
- Lowest-common-denominator global APIs: rejected in favor of narrow ports with
  explicit capability checks.
