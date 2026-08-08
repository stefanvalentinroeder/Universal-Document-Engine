# Engineering Handbook

## Project principles

The Universal Document Engine is built for correctness, reviewability, replacement
of infrastructure providers, and long-term maintainability. Business behavior must
be explicit and deterministic where it makes an approved decision. AI may extract,
classify, or suggest, but it may not silently decide legally relevant outcomes.

Prefer narrow modules with observable behavior over speculative frameworks. Every
change must preserve one codebase for cloud and on-premise operation.

## Modular architecture boundaries

- User interfaces consume published API contracts and never import backend code.
- The API coordinates transport and platform concerns but does not own document
  domain behavior.
- The future document engine has no dependency on `apps/web` or `apps/admin`.
- The future rule engine has no dependency on any AI-provider adapter.
- Provider adapters implement internal ports for storage, databases, and AI.
- Shared libraries expose the smallest contract required by known consumers.
- Cross-boundary calls must be covered by contract or integration tests.

Nx project tags communicate intended boundaries. Static module-boundary enforcement
will be tightened when engine source packages are introduced.

## Code language

Code, comments, identifiers, API contracts, commits, pull requests, ADRs, and
technical documentation are written in English. User-facing content may be
localized later through an approved localization mechanism.

## Coding standards

TypeScript uses strict mode, explicit type-only imports, and no unchecked indexed
access. React components remain focused and accessible. Python uses complete type
annotations, Ruff, mypy strict mode, and asynchronous I/O for API infrastructure.

Formatting is mechanical: Prettier for supported workspace text and Ruff for
Python. Never disable a rule globally to hide a local design problem without an ADR
or a narrowly documented exception.

## Testing expectations

- Pure rules require exhaustive deterministic unit tests.
- API routes require success, failure, and safe error-contract tests.
- Database changes require migration and integration tests.
- Tenant-owned features require explicit cross-tenant isolation attempts.
- Generated documents will require golden-file and visual verification tests.
- Defects receive a regression test before or with the fix.

Tests must not require real customer data, production credentials, or external AI
services. CI runs TypeScript and Python tests from lockfiles. Foundation
integration tests use a separately named Compose project, isolated volumes, and
dynamically allocated ports. They must always remove only those isolated resources
and must emit container status and logs before cleanup when a live check fails.

The required foundation verification command is:

```bash
pnpm verify:foundation
```

It is not permissible to describe the foundation, CI, the migration, or live
infrastructure as passing unless the corresponding command actually completed in
an environment with Docker available. Static Compose inspection is not a
substitute for running the pinned images and their health checks.

## Documentation expectations

Update the README when setup or commands change. Update API documentation and
generated contracts with endpoints. Create or supersede an ADR for consequential,
hard-to-reverse decisions. Document security, tenant, deployment, and operational
effects in the pull request.

Comments explain constraints and intent rather than restating code.

## Git workflow

`main` is the protected release branch. `develop` is the protected integration
branch. Work occurs on short-lived `feature/*`, `fix/*`, and `chore/*` branches.
Pull requests, successful CI, resolved discussion, Conventional Commits, and squash
merge are the default. At least one review becomes mandatory when a team exists.

## Definition of Done

A change is done when:

1. acceptance criteria and explicit non-goals are satisfied;
2. architectural boundaries remain intact;
3. code is typed, linted, formatted, and free of unexplained critical warnings;
4. relevant unit, integration, contract, and build checks pass;
5. tenant isolation and security impacts are reviewed;
6. logging avoids bodies, credentials, tokens, and personal data;
7. migrations are reversible where practical and reviewed;
8. documentation, ADRs, environment examples, and lockfiles are current;
9. no secret or confidential test fixture is committed;
10. a reviewer can reproduce the result from the documented commands.

For foundation changes, Definition of Done additionally requires PostgreSQL and
MinIO health, migration to Alembic `head`, marked integration tests, and live API
smoke checks for `/health`, `/ready`, and `/openapi.json` through
`pnpm verify:foundation` or the equivalent CI integration job.

## Security by design

- Deny by default at authorization and tenant boundaries.
- Keep secrets outside source control and rotate exposed values immediately.
- Pin dependencies and review updates.
- Validate untrusted input at ingress and again at critical domain boundaries.
- Do not log request bodies or sensitive values.
- Configure CORS with explicit origins.
- Use request identifiers for traceability without treating them as identity.
- Do not enable telemetry or external data transmission without approval.
- Keep generated files and parsers isolated from privileged execution contexts.

## Multi-tenant design rule

Every future tenant-owned call requires a verified `TenantContext`; every future
tenant-owned table requires an immutable, non-null tenant key. There is no implicit
default tenant. Database-level isolation and explicit cross-tenant tests are
required before tenant data is admitted. The core schema enforces tenant-scoped
foreign keys and uniqueness constraints, but RLS remains deliberately deferred
until authenticated request, service, and background-job identities have an
approved design. The complete baseline is documented in
`docs/architecture/MULTI_TENANCY.md` and the active schema is documented in
`docs/architecture/CORE_DOMAIN_MODEL.md`.

## Rule engine and AI separation

Deterministic rules make approved business decisions from validated inputs. AI
adapters may return evidence, extracted candidates, confidence, or suggestions.
Rule packages do not import AI packages, and an unavailable AI provider cannot
alter an already approved deterministic result. AI output is untrusted input until
validated.

## Human review

Every legally relevant output remains a draft until an authorized human reviews
the source evidence, validations, deterministic decisions, and rendered result and
then explicitly approves it. The system must preserve that review status and may
not describe an unreviewed artifact as final.

The initial `ReviewTask` persistence model remains separate from `ProcessingRun`.
It represents review work without adding review policy or processing behavior to
the engine. Document and rule-set versions are immutable at both the SQLAlchemy
and PostgreSQL layers; creating a replacement revision is the only permitted
change path.
