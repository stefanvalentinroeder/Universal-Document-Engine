# Security policy

## Reporting a vulnerability

Do not open a public issue. Contact `stefan.valentin.roeder@gmail.com` through the private channel
designated by the repository owner. Include the affected version, reproduction
steps, impact, and any safe mitigation you identified. Do not include real client
or personal data.

The repository owner must replace `stefan.valentin.roeder@gmail.com` before inviting external
contributors.

## Supported versions

Only the current `main` branch and explicitly named maintained release branches are
eligible for security fixes.

## Baseline requirements

- Secrets belong in an approved secret manager or local ignored `.env` file.
- Logs must exclude request bodies, tokens, credentials, and personal data.
- Dependencies and container images must remain pinned and reviewed.
- CORS, storage, database, and AI providers are environment configured.
- Every future tenant-owned operation must verify tenant context.
- No user or repository data may be transmitted as telemetry without approval.
