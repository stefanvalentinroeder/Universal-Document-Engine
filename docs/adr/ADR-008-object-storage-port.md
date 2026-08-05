# ADR-008: Provider-neutral object-storage port

## Status

Accepted.

## Context

Local development uses MinIO, while future cloud and on-premise targets may use AWS
S3 or another implementation. No upload workflow is approved yet.

## Decision

Define a minimal `StorageHealthPort` and a MinIO readiness adapter. Do not introduce
object operations until upload, naming, retention, encryption, and tenant-scoping
requirements are approved.

## Consequences

The local dependency can be checked without committing prematurely to an SDK or
object model. A future storage contract must include tenant-scoped keys and provider
capabilities before document bytes are accepted.

## Rejected alternatives

- Direct MinIO SDK calls in the API: rejected because they couple the platform.
- Implementing a complete storage repository now: rejected as speculative.
- Omitting the boundary: rejected because hybrid deployment requires replaceability.
