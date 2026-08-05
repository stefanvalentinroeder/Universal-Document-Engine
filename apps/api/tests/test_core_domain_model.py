from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import ForeignKeyConstraint, Table, UniqueConstraint

from ude_backend_db import (
    AuditEvent,
    Base,
    Document,
    DocumentVersion,
    ImmutableVersionMutationError,
    ProcessingExecutionMode,
    ProcessingRun,
    ProcessingRunState,
    ReviewTask,
    RuleSet,
    RuleSetVersion,
    Tenant,
    TenantMembership,
    User,
    reject_immutable_version_mutation,
)


def constraint_names(model: type[Base], constraint_type: type[object]) -> set[str]:
    table = cast(Table, model.__table__)
    names: set[str] = set()
    for constraint in table.constraints:
        if isinstance(constraint, constraint_type) and isinstance(constraint.name, str):
            names.add(constraint.name)
    return names


def test_tenant_owned_models_require_non_null_tenant_ids() -> None:
    tenant_owned_models = (
        TenantMembership,
        Document,
        DocumentVersion,
        ProcessingRun,
        RuleSet,
        RuleSetVersion,
        ReviewTask,
        AuditEvent,
    )

    for model in tenant_owned_models:
        assert model.__table__.c.tenant_id.nullable is False


def test_tenant_scoped_unique_constraints_and_composite_foreign_keys_exist() -> None:
    assert "uq_tenant_memberships_tenant_user" in constraint_names(
        TenantMembership, UniqueConstraint
    )
    assert "uq_documents_tenant_identifier" in constraint_names(
        Document, UniqueConstraint
    )
    assert "uq_rule_sets_tenant_name" in constraint_names(RuleSet, UniqueConstraint)
    assert "fk_document_versions_tenant_document" in constraint_names(
        DocumentVersion, ForeignKeyConstraint
    )
    assert "fk_processing_runs_tenant_document_version" in constraint_names(
        ProcessingRun, ForeignKeyConstraint
    )
    assert "fk_processing_runs_tenant_rule_set_version" in constraint_names(
        ProcessingRun, ForeignKeyConstraint
    )
    assert "fk_review_tasks_tenant_processing_run" in constraint_names(
        ReviewTask, ForeignKeyConstraint
    )
    assert "fk_audit_events_tenant_actor" in constraint_names(
        AuditEvent, ForeignKeyConstraint
    )


def test_entities_express_the_expected_relationships_and_execution_mode() -> None:
    tenant = Tenant(slug="tenant-a", display_name="Tenant A")
    user = User(email="user@example.test")
    membership = TenantMembership(tenant=tenant, user=user)
    document = Document(tenant=tenant, identifier="case-001", title="Case 001")
    document_version = DocumentVersion(
        tenant_id=tenant.id or uuid4(),
        document=document,
        version_number=1,
        content_hash="a" * 64,
        content_type="application/pdf",
        storage_key="tenant-a/document-1/version-1.pdf",
        content_size_bytes=42,
    )
    rule_set = RuleSet(tenant=tenant, name="validation")
    rule_set_version = RuleSetVersion(
        tenant_id=tenant.id or uuid4(),
        rule_set=rule_set,
        version_number=1,
        definition={"steps": []},
        definition_hash="b" * 64,
    )
    run = ProcessingRun(
        tenant_id=tenant.id or uuid4(),
        document_version=document_version,
        rule_set_version=rule_set_version,
        execution_mode=ProcessingExecutionMode.HYBRID,
        state=ProcessingRunState.AWAITING_REVIEW,
    )
    task = ReviewTask(tenant_id=tenant.id or uuid4(), processing_run=run)

    assert membership.tenant is tenant
    assert document_version.document is document
    assert run.document_version is document_version
    assert run.rule_set_version is rule_set_version
    assert task.processing_run is run
    assert run.execution_mode is ProcessingExecutionMode.HYBRID


@pytest.mark.parametrize("model", [DocumentVersion, RuleSetVersion])
def test_version_mutations_are_rejected_at_the_application_layer(
    model: type[DocumentVersion] | type[RuleSetVersion],
) -> None:
    with pytest.raises(ImmutableVersionMutationError):
        reject_immutable_version_mutation(None, None, model())
