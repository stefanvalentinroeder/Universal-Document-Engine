from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from ude_backend_db import (
    AuditEvent,
    AuditEventType,
    AuditTargetType,
    Database,
    Document,
    DocumentState,
    DocumentVersion,
    MembershipRole,
    ProcessingExecutionMode,
    ProcessingRun,
    ProcessingRunState,
    ReviewTask,
    ReviewTaskState,
    RuleSet,
    RuleSetState,
    RuleSetVersion,
    Tenant,
    TenantMembership,
    TenantState,
    User,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INFRA_TESTS") != "1",
        reason="Set RUN_INFRA_TESTS=1 after starting isolated infrastructure",
    ),
]


async def test_database_was_migrated_to_the_core_domain_head() -> None:
    """The isolated volume is empty before the workflow upgrades to Alembic head."""

    database = Database(os.environ["DATABASE_URL"])
    try:
        async with database.engine.connect() as connection:
            revision = await connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )
            table_name = await connection.scalar(
                text("SELECT to_regclass('public.processing_runs')")
            )
        assert revision == "20260805_0002"
        assert table_name == "processing_runs"
    finally:
        await database.close()


async def create_core_graph(
    database: Database,
) -> tuple[DocumentVersion, RuleSetVersion]:
    tenant = Tenant(
        id=uuid4(), slug=f"tenant-{uuid4().hex}", display_name="Integration Tenant"
    )
    user = User(
        id=uuid4(),
        email=f"user-{uuid4().hex}@example.test",
        display_name="Integration User",
    )
    membership = TenantMembership(
        id=uuid4(), tenant=tenant, user=user, role=MembershipRole.OWNER
    )
    document = Document(
        id=uuid4(),
        tenant=tenant,
        identifier="document-001",
        title="Integration document",
    )
    document_version = DocumentVersion(
        id=uuid4(),
        tenant_id=tenant.id,
        document=document,
        version_number=1,
        content_hash="a" * 64,
        content_type="application/pdf",
        storage_key=f"{tenant.id}/document/version-1.pdf",
        content_size_bytes=100,
    )
    rule_set = RuleSet(id=uuid4(), tenant=tenant, name="integration-rule-set")
    rule_set_version = RuleSetVersion(
        id=uuid4(),
        tenant_id=tenant.id,
        rule_set=rule_set,
        version_number=1,
        definition={"rules": []},
        definition_hash="b" * 64,
    )
    run = ProcessingRun(
        id=uuid4(),
        tenant_id=tenant.id,
        document_version=document_version,
        rule_set_version=rule_set_version,
        execution_mode=ProcessingExecutionMode.DETERMINISTIC,
    )
    review_task = ReviewTask(
        id=uuid4(),
        tenant_id=tenant.id,
        processing_run=run,
        assigned_user_id=user.id,
    )
    event = AuditEvent(
        id=uuid4(),
        tenant_id=tenant.id,
        actor_user_id=user.id,
        event_type=AuditEventType.CREATED,
        target_type=AuditTargetType.DOCUMENT,
        target_identifier=document.id,
        metadata_={"source": "integration-test"},
    )
    async with database.session() as session:
        session.add_all(
            [
                tenant,
                user,
                membership,
                document,
                document_version,
                rule_set,
                rule_set_version,
                run,
                review_task,
                event,
            ]
        )
        await session.flush()
    return document_version, rule_set_version


async def test_core_entities_are_created_and_processing_uses_an_exact_version() -> None:
    database = Database(os.environ["DATABASE_URL"])
    try:
        document_version, _ = await create_core_graph(database)
        async with database.session() as session:
            run = await session.scalar(
                select(ProcessingRun).where(
                    ProcessingRun.document_version_id == document_version.id
                )
            )
        assert run is not None
        assert run.document_version_id == document_version.id
    finally:
        await database.close()


async def test_enum_values_round_trip_through_postgresql() -> None:
    """PostgreSQL receives lowercase domain values and SQLAlchemy restores enums."""

    database = Database(os.environ["DATABASE_URL"])
    tenant = Tenant(
        id=uuid4(),
        slug=f"enum-tenant-{uuid4().hex}",
        display_name="Enum Integration Tenant",
        state=TenantState.SUSPENDED,
    )
    user = User(
        id=uuid4(),
        email=f"enum-user-{uuid4().hex}@example.test",
        display_name="Enum Integration User",
    )
    membership = TenantMembership(
        id=uuid4(), tenant=tenant, user=user, role=MembershipRole.ADMIN
    )
    document = Document(
        id=uuid4(),
        tenant=tenant,
        identifier="enum-document-001",
        title="Enum integration document",
        state=DocumentState.ARCHIVED,
    )
    document_version = DocumentVersion(
        id=uuid4(),
        tenant_id=tenant.id,
        document=document,
        version_number=1,
        content_hash="a" * 64,
        content_type="application/pdf",
        storage_key=f"{tenant.id}/enum-document/version-1.pdf",
        content_size_bytes=100,
    )
    rule_set = RuleSet(
        id=uuid4(), tenant=tenant, name="enum-rule-set", state=RuleSetState.ARCHIVED
    )
    rule_set_version = RuleSetVersion(
        id=uuid4(),
        tenant_id=tenant.id,
        rule_set=rule_set,
        version_number=1,
        definition={"rules": []},
        definition_hash="b" * 64,
    )
    processing_run = ProcessingRun(
        id=uuid4(),
        tenant_id=tenant.id,
        document_version=document_version,
        rule_set_version=rule_set_version,
        execution_mode=ProcessingExecutionMode.AI_ASSISTED,
        state=ProcessingRunState.RUNNING,
    )
    review_task = ReviewTask(
        id=uuid4(),
        tenant_id=tenant.id,
        processing_run=processing_run,
        assigned_user_id=user.id,
        state=ReviewTaskState.IN_REVIEW,
    )
    audit_event = AuditEvent(
        id=uuid4(),
        tenant_id=tenant.id,
        actor_user_id=user.id,
        event_type=AuditEventType.REVIEW_REQUESTED,
        target_type=AuditTargetType.RULE_SET_VERSION,
        target_identifier=rule_set_version.id,
        metadata_={"source": "enum-regression-test"},
    )

    try:
        async with database.session() as session:
            session.add_all(
                [
                    tenant,
                    user,
                    membership,
                    document,
                    document_version,
                    rule_set,
                    rule_set_version,
                    processing_run,
                    review_task,
                    audit_event,
                ]
            )
            await session.flush()

        async with database.session() as session:
            persisted_tenant = await session.get(Tenant, tenant.id)
            persisted_membership = await session.get(TenantMembership, membership.id)
            persisted_document = await session.get(Document, document.id)
            persisted_rule_set = await session.get(RuleSet, rule_set.id)
            persisted_run = await session.get(ProcessingRun, processing_run.id)
            persisted_review_task = await session.get(ReviewTask, review_task.id)
            persisted_audit_event = await session.get(AuditEvent, audit_event.id)

            assert persisted_tenant is not None
            assert persisted_membership is not None
            assert persisted_document is not None
            assert persisted_rule_set is not None
            assert persisted_run is not None
            assert persisted_review_task is not None
            assert persisted_audit_event is not None
            assert persisted_tenant.state is TenantState.SUSPENDED
            assert persisted_membership.role is MembershipRole.ADMIN
            assert persisted_document.state is DocumentState.ARCHIVED
            assert persisted_rule_set.state is RuleSetState.ARCHIVED
            assert persisted_run.execution_mode is ProcessingExecutionMode.AI_ASSISTED
            assert persisted_run.state is ProcessingRunState.RUNNING
            assert persisted_review_task.state is ReviewTaskState.IN_REVIEW
            assert persisted_audit_event.event_type is AuditEventType.REVIEW_REQUESTED
            assert persisted_audit_event.target_type is AuditTargetType.RULE_SET_VERSION

            labels = (
                (
                    await session.execute(
                        text(
                            """
                            SELECT
                                tenant.state::text AS tenant_state,
                                membership.role::text AS membership_role,
                                document.state::text AS document_state,
                                rule_set.state::text AS rule_set_state,
                                processing_run.execution_mode::text
                                    AS processing_execution_mode,
                                processing_run.state::text AS processing_run_state,
                                review_task.state::text AS review_task_state,
                                audit_event.event_type::text AS audit_event_type,
                                audit_event.target_type::text AS audit_target_type
                            FROM tenants AS tenant
                            JOIN tenant_memberships AS membership
                                ON membership.id = :membership_id
                            JOIN documents AS document ON document.id = :document_id
                            JOIN rule_sets AS rule_set ON rule_set.id = :rule_set_id
                            JOIN processing_runs AS processing_run
                                ON processing_run.id = :run_id
                            JOIN review_tasks AS review_task
                                ON review_task.id = :review_task_id
                            JOIN audit_events AS audit_event
                                ON audit_event.id = :audit_event_id
                            WHERE tenant.id = :tenant_id
                            """
                        ),
                        {
                            "tenant_id": tenant.id,
                            "membership_id": membership.id,
                            "document_id": document.id,
                            "rule_set_id": rule_set.id,
                            "run_id": processing_run.id,
                            "review_task_id": review_task.id,
                            "audit_event_id": audit_event.id,
                        },
                    )
                )
                .mappings()
                .one()
            )

        assert dict(labels) == {
            "tenant_state": TenantState.SUSPENDED.value,
            "membership_role": MembershipRole.ADMIN.value,
            "document_state": DocumentState.ARCHIVED.value,
            "rule_set_state": RuleSetState.ARCHIVED.value,
            "processing_execution_mode": ProcessingExecutionMode.AI_ASSISTED.value,
            "processing_run_state": ProcessingRunState.RUNNING.value,
            "review_task_state": ReviewTaskState.IN_REVIEW.value,
            "audit_event_type": AuditEventType.REVIEW_REQUESTED.value,
            "audit_target_type": AuditTargetType.RULE_SET_VERSION.value,
        }
    finally:
        await database.close()


async def test_tenant_required_and_scoped_uniqueness_constraints_are_enforced() -> None:
    database = Database(os.environ["DATABASE_URL"])
    tenant = Tenant(
        id=uuid4(), slug=f"tenant-{uuid4().hex}", display_name="Constraint Tenant"
    )
    try:
        async with database.session() as session:
            session.add(tenant)
            await session.flush()
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    session.add_all(
                        [
                            Document(
                                id=uuid4(),
                                tenant_id=tenant.id,
                                identifier="same",
                                title="First",
                            ),
                            Document(
                                id=uuid4(),
                                tenant_id=tenant.id,
                                identifier="same",
                                title="Second",
                            ),
                        ]
                    )
                    await session.flush()
        async with database.session() as session:
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    session.add(
                        Document(
                            id=uuid4(), identifier="missing-tenant", title="Invalid"
                        )
                    )
                    await session.flush()
    finally:
        await database.close()


async def test_cross_tenant_links_are_rejected() -> None:
    database = Database(os.environ["DATABASE_URL"])
    tenant_a = Tenant(
        id=uuid4(), slug=f"tenant-a-{uuid4().hex}", display_name="Tenant A"
    )
    tenant_b = Tenant(
        id=uuid4(), slug=f"tenant-b-{uuid4().hex}", display_name="Tenant B"
    )
    try:
        async with database.session() as session:
            document = Document(
                id=uuid4(), tenant=tenant_a, identifier="document-a", title="Document A"
            )
            session.add_all([tenant_a, tenant_b, document])
            await session.flush()
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    session.add(
                        DocumentVersion(
                            id=uuid4(),
                            tenant_id=tenant_b.id,
                            document_id=document.id,
                            version_number=1,
                            content_hash="a" * 64,
                            content_type="application/pdf",
                            storage_key=f"{tenant_b.id}/invalid.pdf",
                            content_size_bytes=1,
                        )
                    )
                    await session.flush()
            with pytest.raises(DBAPIError):
                async with session.begin_nested():
                    await session.execute(
                        update(Document)
                        .where(Document.id == document.id)
                        .values(tenant_id=tenant_b.id)
                    )
    finally:
        await database.close()


async def test_database_rejects_mutation_of_immutable_versions() -> None:
    database = Database(os.environ["DATABASE_URL"])
    try:
        document_version, rule_set_version = await create_core_graph(database)
        async with database.engine.begin() as connection:
            with pytest.raises(DBAPIError):
                await connection.execute(
                    text(
                        "UPDATE document_versions SET content_hash = :hash "
                        "WHERE id = :id"
                    ),
                    {"hash": "c" * 64, "id": document_version.id},
                )
            with pytest.raises(DBAPIError):
                await connection.execute(
                    text("DELETE FROM rule_set_versions WHERE id = :id"),
                    {"id": rule_set_version.id},
                )
    finally:
        await database.close()
