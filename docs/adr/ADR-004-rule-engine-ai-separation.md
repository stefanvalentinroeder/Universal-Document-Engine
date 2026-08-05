# ADR-004: Deterministic rules decide; AI assists

## Status

Accepted.

## Context

Document workflows may benefit from AI-assisted extraction, but legally relevant
decisions require predictable, explainable, and testable behavior.

## Decision

The rule engine is deterministic and has no dependency on an AI provider. AI output
is treated as untrusted evidence or a suggestion. Validated inputs feed rules, and
legally relevant results require human review.

## Consequences

Approved decisions can be reproduced without provider availability. The platform
must retain evidence and validation status. AI cannot silently change a rule result,
which may require explicit reconciliation user interfaces later.

## Rejected alternatives

- AI-authored final decisions: rejected as non-deterministic and insufficiently
  reviewable.
- Embedding provider calls in rules: rejected because it couples correctness to an
  external service.
- Excluding AI permanently: rejected because assisted extraction may add value.
