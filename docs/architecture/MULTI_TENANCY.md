# Multi-tenant foundation rule

Tenant isolation is a mandatory design invariant, not an optional feature to add
after domain tables exist.

Before any tenant-owned schema or operation is approved, its design must include:

1. an immutable tenant identifier on every tenant-owned record;
2. non-null constraints and tenant-aware unique indexes;
3. repository and service APIs that require explicit `TenantContext`;
4. database-enforced isolation, preferably PostgreSQL row-level security, after its
   connection-pooling and administration behavior is proven;
5. migration tests for cross-tenant uniqueness and isolation;
6. integration tests that attempt cross-tenant reads and writes;
7. background-job and object-storage keys scoped by tenant;
8. audit records that identify the verified tenant without logging private payloads.

No fallback or global tenant is permitted. System-level operations must use a
separate, explicit administrative context and authorization path.
