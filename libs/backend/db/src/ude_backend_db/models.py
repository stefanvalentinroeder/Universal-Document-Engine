"""SQLAlchemy persistence models for the Universal Document Engine core domain.

The models intentionally describe persistence only. API schemas and business
workflows belong to their respective layers and must not be coupled to these
database records.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    and_,
    event,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, foreign, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Base metadata for all UDE persistence records."""


JsonValue = dict[str, Any]
JsonType = JSON().with_variant(JSONB, "postgresql")


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for application-created records."""

    return datetime.now(UTC)


class TenantState(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class MembershipRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class DocumentState(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProcessingExecutionMode(str, Enum):
    DETERMINISTIC = "deterministic"
    AI_ASSISTED = "ai_assisted"
    HYBRID = "hybrid"


class ProcessingRunState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RuleSetState(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ReviewTaskState(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AuditEventType(str, Enum):
    CREATED = "created"
    STATE_CHANGED = "state_changed"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_COMPLETED = "review_completed"


class AuditTargetType(str, Enum):
    TENANT = "tenant"
    USER = "user"
    TENANT_MEMBERSHIP = "tenant_membership"
    DOCUMENT = "document"
    DOCUMENT_VERSION = "document_version"
    PROCESSING_RUN = "processing_run"
    RULE_SET = "rule_set"
    RULE_SET_VERSION = "rule_set_version"
    REVIEW_TASK = "review_task"


class ImmutableVersionMutationError(ValueError):
    """Raised before an immutable version record can be changed or removed."""


class TimestampedRecord:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )


class Tenant(TimestampedRecord, Base):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[TenantState] = mapped_column(
        SqlEnum(TenantState, name="tenant_state"),
        nullable=False,
        default=TenantState.ACTIVE,
        server_default=TenantState.ACTIVE.value,
    )

    memberships: Mapped[list[TenantMembership]] = relationship(back_populates="tenant")
    documents: Mapped[list[Document]] = relationship(back_populates="tenant")
    rule_sets: Mapped[list[RuleSet]] = relationship(back_populates="tenant")


class User(TimestampedRecord, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255))

    memberships: Mapped[list[TenantMembership]] = relationship(back_populates="user")


class TenantMembership(TimestampedRecord, Base):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"
        ),
        UniqueConstraint("tenant_id", "id", name="uq_tenant_memberships_tenant_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[MembershipRole] = mapped_column(
        SqlEnum(MembershipRole, name="membership_role"),
        nullable=False,
        default=MembershipRole.MEMBER,
        server_default=MembershipRole.MEMBER.value,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class Document(TimestampedRecord, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_documents_tenant_id"),
        UniqueConstraint(
            "tenant_id", "identifier", name="uq_documents_tenant_identifier"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    identifier: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    state: Mapped[DocumentState] = mapped_column(
        SqlEnum(DocumentState, name="document_state"),
        nullable=False,
        default=DocumentState.ACTIVE,
        server_default=DocumentState.ACTIVE.value,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(back_populates="document")


class DocumentVersion(TimestampedRecord, Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["documents.tenant_id", "documents.id"],
            name="fk_document_versions_tenant_document",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_document_versions_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "document_id",
            "version_number",
            name="uq_document_versions_tenant_document_version",
        ),
        CheckConstraint(
            "version_number > 0", name="ck_document_versions_positive_number"
        ),
        CheckConstraint(
            "content_size_bytes >= 0", name="ck_document_versions_nonnegative_size"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    content_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    document: Mapped[Document] = relationship(back_populates="versions")
    processing_runs: Mapped[list[ProcessingRun]] = relationship(
        back_populates="document_version",
        primaryjoin=lambda: and_(
            DocumentVersion.tenant_id == ProcessingRun.tenant_id,
            DocumentVersion.id == foreign(ProcessingRun.document_version_id),
        ),
        foreign_keys=lambda: [ProcessingRun.document_version_id],
    )


class RuleSet(TimestampedRecord, Base):
    __tablename__ = "rule_sets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_rule_sets_tenant_id"),
        UniqueConstraint("tenant_id", "name", name="uq_rule_sets_tenant_name"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    state: Mapped[RuleSetState] = mapped_column(
        SqlEnum(RuleSetState, name="rule_set_state"),
        nullable=False,
        default=RuleSetState.ACTIVE,
        server_default=RuleSetState.ACTIVE.value,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="rule_sets")
    versions: Mapped[list[RuleSetVersion]] = relationship(back_populates="rule_set")


class RuleSetVersion(TimestampedRecord, Base):
    __tablename__ = "rule_set_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "rule_set_id"],
            ["rule_sets.tenant_id", "rule_sets.id"],
            name="fk_rule_set_versions_tenant_rule_set",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_rule_set_versions_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "rule_set_id",
            "version_number",
            name="uq_rule_set_versions_tenant_rule_set_version",
        ),
        CheckConstraint(
            "version_number > 0", name="ck_rule_set_versions_positive_number"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    rule_set_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[JsonValue] = mapped_column(
        JsonType, nullable=False, default=dict
    )
    definition_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    rule_set: Mapped[RuleSet] = relationship(back_populates="versions")
    processing_runs: Mapped[list[ProcessingRun]] = relationship(
        back_populates="rule_set_version",
        primaryjoin=lambda: and_(
            RuleSetVersion.tenant_id == ProcessingRun.tenant_id,
            RuleSetVersion.id == foreign(ProcessingRun.rule_set_version_id),
        ),
        foreign_keys=lambda: [ProcessingRun.rule_set_version_id],
    )


class ProcessingRun(TimestampedRecord, Base):
    __tablename__ = "processing_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "document_version_id"],
            ["document_versions.tenant_id", "document_versions.id"],
            name="fk_processing_runs_tenant_document_version",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rule_set_version_id"],
            ["rule_set_versions.tenant_id", "rule_set_versions.id"],
            name="fk_processing_runs_tenant_rule_set_version",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_processing_runs_tenant_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    document_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    rule_set_version_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), index=True
    )
    execution_mode: Mapped[ProcessingExecutionMode] = mapped_column(
        SqlEnum(ProcessingExecutionMode, name="processing_execution_mode"),
        nullable=False,
    )
    state: Mapped[ProcessingRunState] = mapped_column(
        SqlEnum(ProcessingRunState, name="processing_run_state"),
        nullable=False,
        default=ProcessingRunState.PENDING,
        server_default=ProcessingRunState.PENDING.value,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    document_version: Mapped[DocumentVersion] = relationship(
        back_populates="processing_runs",
        primaryjoin=lambda: and_(
            DocumentVersion.tenant_id == ProcessingRun.tenant_id,
            DocumentVersion.id == foreign(ProcessingRun.document_version_id),
        ),
        foreign_keys=lambda: [ProcessingRun.document_version_id],
    )
    rule_set_version: Mapped[RuleSetVersion | None] = relationship(
        back_populates="processing_runs",
        primaryjoin=lambda: and_(
            RuleSetVersion.tenant_id == ProcessingRun.tenant_id,
            RuleSetVersion.id == foreign(ProcessingRun.rule_set_version_id),
        ),
        foreign_keys=lambda: [ProcessingRun.rule_set_version_id],
    )
    review_tasks: Mapped[list[ReviewTask]] = relationship(
        back_populates="processing_run"
    )


class ReviewTask(TimestampedRecord, Base):
    __tablename__ = "review_tasks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "processing_run_id"],
            ["processing_runs.tenant_id", "processing_runs.id"],
            name="fk_review_tasks_tenant_processing_run",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assigned_user_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.user_id"],
            name="fk_review_tasks_tenant_assigned_user",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_review_tasks_tenant_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    processing_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    assigned_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), index=True
    )
    state: Mapped[ReviewTaskState] = mapped_column(
        SqlEnum(ReviewTaskState, name="review_task_state"),
        nullable=False,
        default=ReviewTaskState.OPEN,
        server_default=ReviewTaskState.OPEN.value,
    )
    review_instructions: Mapped[str | None] = mapped_column(Text)

    processing_run: Mapped[ProcessingRun] = relationship(back_populates="review_tasks")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "actor_user_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.user_id"],
            name="fk_audit_events_tenant_actor",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    event_type: Mapped[AuditEventType] = mapped_column(
        SqlEnum(AuditEventType, name="audit_event_type"), nullable=False
    )
    target_type: Mapped[AuditTargetType] = mapped_column(
        SqlEnum(AuditTargetType, name="audit_target_type"), nullable=False
    )
    target_identifier: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    metadata_: Mapped[JsonValue] = mapped_column(
        "metadata", JsonType, nullable=False, default=dict
    )


def reject_immutable_version_mutation(*_: object) -> None:
    raise ImmutableVersionMutationError(
        "DocumentVersion and RuleSetVersion records are immutable; "
        "create a new version instead."
    )


for _version_model in (DocumentVersion, RuleSetVersion):
    event.listen(_version_model, "before_update", reject_immutable_version_mutation)
    event.listen(_version_model, "before_delete", reject_immutable_version_mutation)
