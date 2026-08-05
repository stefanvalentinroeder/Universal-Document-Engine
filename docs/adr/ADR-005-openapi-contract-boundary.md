# ADR-005: OpenAPI is the TypeScript/Python contract boundary

## Status

Accepted.

## Context

The frontend uses TypeScript and the API uses Python. Directly duplicated or shared
runtime types would drift or create language coupling.

## Decision

FastAPI-generated OpenAPI is the contract source. A future build step will generate
the TypeScript API client under `libs/frontend/api-client`. Handwritten endpoint
types in that library are prohibited.

## Consequences

Contract changes are reviewable and client generation is repeatable. OpenAPI
quality becomes a build concern, and generation tooling must be selected before the
first business endpoint.

## Rejected alternatives

- Handwritten TypeScript interfaces: rejected because they drift.
- Importing Python model definitions into TypeScript: rejected as runtime coupling.
- GraphQL: rejected because the approved transport foundation is FastAPI/OpenAPI.
