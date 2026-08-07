# Contributing

This is a private proprietary project. Contributions require prior authorization
from the rights holder and acceptance of the repository's confidentiality terms.

## Working agreement

1. Branch from `develop` using `feature/*`, `fix/*`, or `chore/*`.
2. Keep each branch focused and short-lived.
3. Write code, comments, identifiers, API contracts, commits, and technical
   documentation in English.
4. Use Conventional Commits, for example `feat(api): add readiness probe`.
5. Add or update tests and documentation with the implementation.
6. Run `pnpm check` and `pnpm compose:validate` before opening a pull request.
7. Open a pull request into `develop`; use a reviewed release pull request from
   `develop` into `main`.
8. Prefer squash merge and delete the merged branch.

## Architectural constraints

- Do not import Python runtime types into TypeScript; use OpenAPI generation.
- Do not couple the deterministic rule engine to AI providers.
- Do not couple the document engine to either user interface.
- Do not introduce a tenant-owned operation without explicit tenant context.
- Do not send repository or user data to external telemetry or AI services without
  explicit approval.
- Do not add legally relevant automation without a mandatory human-review gate.

## Pull-request quality

A pull request must explain scope, security and tenant impact, test evidence,
documentation changes, and intentional non-goals. Generated migrations and lockfile
changes must be reviewable and directly attributable to the change.

See `docs/engineering-handbook/ENGINEERING_HANDBOOK.md` for the complete Definition
of Done.
