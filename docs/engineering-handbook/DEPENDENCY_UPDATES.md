# Dependency update strategy

Dependency updates are reviewed maintenance changes, not automatic merges.

1. Update one ecosystem or tightly related package group per pull request.
2. Read upstream security advisories, release notes, runtime requirements, and
   migration guides.
3. Keep root manifests exact and regenerate the relevant lockfile.
4. Run lint, format checks, tests, builds, API validation, and Compose validation.
5. For container changes, pull and start the local stack and verify health checks.
6. Record breaking configuration or behavior changes in an ADR when architectural.
7. Use a monthly routine update window and expedite credible security fixes.

Major versions require an explicit compatibility review. No workflow automatically
transmits repository metadata to a third-party update service in this foundation.
