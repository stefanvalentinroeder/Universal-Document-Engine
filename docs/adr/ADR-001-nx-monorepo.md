# ADR-001: Nx monorepo

## Status

Accepted.

## Context

UDE contains two TypeScript applications, shared frontend libraries, a Python API,
and future engine packages. Changes must be reproducible and selectively testable
without splitting the product prematurely across repositories.

## Decision

Use one Nx monorepo with pnpm for JavaScript workspaces. Nx project targets
orchestrate Next.js, TypeScript, and Python commands while language-native tools
remain authoritative for builds, linting, and tests.

## Consequences

Developers receive one dependency graph and command surface. CI can use affected
execution and caching. Cross-language targets require explicit `run-commands`
definitions, and the repository must avoid confusing Nx orchestration with shared
runtime types.

## Rejected alternatives

- Separate repositories: rejected because foundation changes span all components.
- Turborepo: rejected because Nx project modeling and affected execution are the
  approved standard.
- An unstructured pnpm workspace: rejected because it lacks the required task and
  dependency graph.
