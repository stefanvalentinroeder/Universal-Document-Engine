# Universal Document Engine

Universal Document Engine (UDE) is an industry-neutral foundation for converting
structured case data, reusable templates, deterministic rules, and assisted
extraction into reviewable documents. Development Order 001 contains platform
infrastructure and application shells only. It contains no document-generation or
specialist notarial logic.

## Architecture at a glance

- `apps/web`: Next.js main application shell on port `3000`.
- `apps/admin`: separate Next.js administration shell on port `3001`.
- `apps/api`: FastAPI application factory on port `8000`.
- `libs/frontend`: shared UI and the future generated API-client boundary.
- `libs/backend`: configuration-independent backend utilities, asynchronous
  database access, and explicit tenant context.
- `libs/engine`: documented boundaries for the future document, rule, parser, AI,
  validation, and generation components.
- `infra`: local infrastructure documentation and future deployment scripts.
- `docs`: architecture, API, ADR, and engineering documentation.

PostgreSQL and MinIO run in Docker. Application processes run on the host for fast,
cross-platform development. The same source boundaries are suitable for later
cloud and on-premise packaging.

## Prerequisites

| Tool                    |            Pinned version | Purpose                           |
| ----------------------- | ------------------------: | --------------------------------- |
| Node.js                 |                 `24.14.0` | JavaScript runtime                |
| pnpm                    |                  `11.7.0` | JavaScript workspace dependencies |
| Python                  |                 `3.13.14` | Backend runtime                   |
| uv                      |                 `0.11.33` | Python environment and lockfile   |
| Docker Desktop / Engine | current supported release | PostgreSQL and MinIO              |
| Docker Compose          |  v2 with `--wait` support | Local orchestration               |

On Windows, use Docker Desktop with Linux containers and PowerShell or Windows
Terminal. No Unix-only shell is required by the normal workflow.

## First setup

```bash
pnpm install --frozen-lockfile
pnpm setup
pnpm dev
```

`pnpm setup` performs the following idempotent steps:

1. creates `.env` from `.env.example` if it does not exist;
2. synchronizes the pinned Python environment;
3. validates and starts PostgreSQL and MinIO;
4. waits for infrastructure health checks;
5. upgrades the database to the Alembic head revision.

The safe values in `.env.example` are for an isolated local workstation only.
Replace them for every shared, test, staging, or production environment.

## Normal development

```bash
pnpm dev
```

Open:

- main application: <http://localhost:3000>
- administration: <http://localhost:3001>
- API documentation: <http://localhost:8000/docs>
- OpenAPI document: <http://localhost:8000/openapi.json>
- MinIO console: <http://localhost:9001>

Individual services can be started with `pnpm dev:web`, `pnpm dev:admin`, or
`pnpm dev:api`. Local infrastructure can be controlled with `pnpm infra:up`,
`pnpm infra:down`, and `pnpm infra:logs`. `pnpm dev` starts the three application
processes as one managed process group. `Ctrl+C` or a termination signal is
forwarded to the complete group so web, admin, and API do not remain orphaned.
Infrastructure containers intentionally remain available for the next development
session and can be stopped explicitly with `pnpm infra:down`.

## Validation commands

```bash
pnpm lint
pnpm format:check
pnpm test
pnpm build
pnpm api:validate
pnpm compose:validate
pnpm check:secrets
pnpm test:infra
pnpm verify:foundation
```

`pnpm test:infra` creates an isolated Compose project with isolated PostgreSQL and
MinIO volumes and dynamically allocated host ports. It validates Compose, waits
for healthy containers, migrates to Alembic `head`, runs the marked infrastructure
tests, starts the API, and verifies `/health`, `/ready`, and `/openapi.json`. On
failure it prints container status and logs. It removes only its own containers,
network, and volumes on both success and failure; normal development data is never
targeted.

`pnpm verify:foundation` is the complete local foundation gate. It runs formatting,
linting, unit tests, builds, OpenAPI validation, the secret scan, Compose validation,
and the complete isolated live-infrastructure workflow. Docker is required.

`pnpm check` remains the faster application-level gate without Docker. Marked
integration tests are intentionally excluded from `pnpm test` and run through the
isolated workflow:

```bash
pnpm test:infra
```

The phrase **CI is green** means that every required automated check completed
successfully. It does not refer to the visual color scheme.

## Database migrations

Apply committed migrations:

```bash
pnpm db:migrate
```

Create a reviewed migration after intentionally changing SQLAlchemy metadata:

```bash
pnpm db:revision -- -m "describe the schema change"
```

The core-domain migration creates tenant, user, membership, document,
document-version, processing-run, rule-set, rule-set-version, review-task, and
audit-event tables. The integration workflow verifies a clean upgrade, downgrade
to the baseline, and repeat upgrade on isolated PostgreSQL volumes. See
`docs/architecture/CORE_DOMAIN_MODEL.md` and
`docs/architecture/MULTI_TENANCY.md` before changing the schema.

## API and contracts

Operational endpoints are intentionally outside the future versioned business API:

- `GET /health`: process liveness;
- `GET /ready`: readiness, requiring both PostgreSQL and object storage;
- `/api/v1`: reserved prefix for future application routes.

`GET /ready` returns `200` only when both dependency checks are up. It returns
`503` if either or both are unavailable. The response reports separate
`database` and `object_storage` states without exposing connection strings,
credentials, endpoints, exception text, or other internal details.

Python runtime types are not imported into TypeScript. OpenAPI is the contract
source for a generated TypeScript client in a later order.

## Git workflow

Use `main` for protected releases, `develop` for integration, and short-lived
`feature/*`, `fix/*`, or `chore/*` branches. All merges use pull requests;
Conventional Commits and squash merge are preferred. See `CONTRIBUTING.md`.

### Manual GitHub repository setup

Repository-owner access is required for these settings:

1. create a private repository named `universal-document-engine`;
2. push the initial code to `main`, then create `develop` from `main`;
3. set squash merge as the preferred merge method;
4. protect `main` and `develop` with pull requests required;
5. require both `CI / quality` and `CI / integration` status checks before merge;
6. require conversation resolution and prevent force pushes and deletion;
7. require one approving review when a second team member exists;
8. replace `@replace-with-repository-owner` in `.github/CODEOWNERS` with the
   actual GitHub user or team;
9. configure environment secrets only in GitHub or the approved deployment
   secret manager, never in repository files.

Branch protection is not configured automatically because no repository-owner
identity or administration authority is assumed.

## Security and privacy

Request bodies, credentials, personal data, and tokens must not be logged. CORS is
an explicit environment-owned allow-list. No telemetry or external AI provider is
enabled. Report vulnerabilities through the private process in `SECURITY.md`.

## Dependency updates

Versions are exact in the manifests and resolved by `pnpm-lock.yaml` and `uv.lock`.
Container images use immutable release tags rather than `latest`. Follow
`docs/engineering-handbook/DEPENDENCY_UPDATES.md` for reviewed updates.

## License

Proprietary and confidential. See `LICENSE`. The legal owner and year placeholders
must be replaced by the repository owner before external distribution.
