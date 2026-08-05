"""Create the multi-tenant core domain schema.

Revision ID: 20260805_0002
Revises: 20260804_0001
Create Date: 2026-08-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260805_0002"
down_revision: str | None = "20260804_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def utc_timestamp_column() -> sa.Column[object]:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def upgrade() -> None:
    tenant_state = postgresql.ENUM(
        "active", "suspended", "archived", name="tenant_state", create_type=False
    )
    membership_role = postgresql.ENUM(
        "owner", "admin", "member", name="membership_role", create_type=False
    )
    document_state = postgresql.ENUM(
        "active", "archived", name="document_state", create_type=False
    )
    processing_execution_mode = postgresql.ENUM(
        "deterministic", "ai_assisted", "hybrid", name="processing_execution_mode", create_type=False
    )
    processing_run_state = postgresql.ENUM(
        "pending",
        "running",
        "awaiting_review",
        "completed",
        "failed",
        "cancelled",
        name="processing_run_state",
        create_type=False,
    )
    rule_set_state = postgresql.ENUM(
        "active", "archived", name="rule_set_state", create_type=False
    )
    review_task_state = postgresql.ENUM(
        "open", "in_review", "approved", "rejected", "cancelled", name="review_task_state", create_type=False
    )
    audit_event_type = postgresql.ENUM(
        "created", "state_changed", "review_requested", "review_completed", name="audit_event_type", create_type=False
    )
    audit_target_type = postgresql.ENUM(
        "tenant",
        "user",
        "tenant_membership",
        "document",
        "document_version",
        "processing_run",
        "rule_set",
        "rule_set_version",
        "review_task",
        name="audit_target_type",
        create_type=False,
    )

    bind = op.get_bind()
    for enum_type in (
        tenant_state,
        membership_role,
        document_state,
        processing_execution_mode,
        processing_run_state,
        rule_set_state,
        review_task_state,
        audit_event_type,
        audit_target_type,
    ):
        enum_type.create(bind, checkfirst=False)

    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("state", tenant_state, server_default="active", nullable=False),
        utc_timestamp_column(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        utc_timestamp_column(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", membership_role, server_default="member", nullable=False),
        utc_timestamp_column(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_tenant_memberships_tenant_id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("identifier", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("state", document_state, server_default="active", nullable=False),
        utc_timestamp_column(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_documents_tenant_id"),
        sa.UniqueConstraint("tenant_id", "identifier", name="uq_documents_tenant_identifier"),
    )
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])
    op.create_table(
        "document_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("content_size_bytes", sa.Integer(), nullable=False),
        utc_timestamp_column(),
        sa.CheckConstraint("content_size_bytes >= 0", name="ck_document_versions_nonnegative_size"),
        sa.CheckConstraint("version_number > 0", name="ck_document_versions_positive_number"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["documents.tenant_id", "documents.id"],
            name="fk_document_versions_tenant_document",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_document_versions_tenant_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "document_id",
            "version_number",
            name="uq_document_versions_tenant_document_version",
        ),
    )
    op.create_index("ix_document_versions_tenant_id", "document_versions", ["tenant_id"])
    op.create_index("ix_document_versions_document_id", "document_versions", ["document_id"])
    op.create_table(
        "rule_sets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("state", rule_set_state, server_default="active", nullable=False),
        utc_timestamp_column(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_rule_sets_tenant_id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_rule_sets_tenant_name"),
    )
    op.create_index("ix_rule_sets_tenant_id", "rule_sets", ["tenant_id"])
    op.create_table(
        "rule_set_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rule_set_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("definition_hash", sa.String(length=128), nullable=False),
        utc_timestamp_column(),
        sa.CheckConstraint("version_number > 0", name="ck_rule_set_versions_positive_number"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "rule_set_id"],
            ["rule_sets.tenant_id", "rule_sets.id"],
            name="fk_rule_set_versions_tenant_rule_set",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_rule_set_versions_tenant_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "rule_set_id",
            "version_number",
            name="uq_rule_set_versions_tenant_rule_set_version",
        ),
    )
    op.create_index("ix_rule_set_versions_tenant_id", "rule_set_versions", ["tenant_id"])
    op.create_index("ix_rule_set_versions_rule_set_id", "rule_set_versions", ["rule_set_id"])
    op.create_table(
        "processing_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("rule_set_version_id", sa.Uuid(), nullable=True),
        sa.Column("execution_mode", processing_execution_mode, nullable=False),
        sa.Column("state", processing_run_state, server_default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        utc_timestamp_column(),
        sa.ForeignKeyConstraint(
            ["tenant_id", "document_version_id"],
            ["document_versions.tenant_id", "document_versions.id"],
            name="fk_processing_runs_tenant_document_version",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "rule_set_version_id"],
            ["rule_set_versions.tenant_id", "rule_set_versions.id"],
            name="fk_processing_runs_tenant_rule_set_version",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_processing_runs_tenant_id"),
    )
    op.create_index("ix_processing_runs_tenant_id", "processing_runs", ["tenant_id"])
    op.create_index("ix_processing_runs_document_version_id", "processing_runs", ["document_version_id"])
    op.create_index("ix_processing_runs_rule_set_version_id", "processing_runs", ["rule_set_version_id"])
    op.create_table(
        "review_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("processing_run_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_user_id", sa.Uuid(), nullable=True),
        sa.Column("state", review_task_state, server_default="open", nullable=False),
        sa.Column("review_instructions", sa.Text(), nullable=True),
        utc_timestamp_column(),
        sa.ForeignKeyConstraint(
            ["tenant_id", "processing_run_id"],
            ["processing_runs.tenant_id", "processing_runs.id"],
            name="fk_review_tasks_tenant_processing_run",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assigned_user_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.user_id"],
            name="fk_review_tasks_tenant_assigned_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_review_tasks_tenant_id"),
    )
    op.create_index("ix_review_tasks_tenant_id", "review_tasks", ["tenant_id"])
    op.create_index("ix_review_tasks_processing_run_id", "review_tasks", ["processing_run_id"])
    op.create_index("ix_review_tasks_assigned_user_id", "review_tasks", ["assigned_user_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("target_type", audit_target_type, nullable=False),
        sa.Column("target_identifier", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_user_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.user_id"],
            name="fk_audit_events_tenant_actor",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index("ix_audit_events_target_identifier", "audit_events", ["target_identifier"])

    op.execute(
        """
        CREATE FUNCTION ude_reject_immutable_version_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Immutable version records cannot be updated or deleted';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE FUNCTION ude_reject_tenant_id_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id THEN
                RAISE EXCEPTION 'Tenant ownership cannot be reassigned';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE TRIGGER document_versions_are_immutable BEFORE UPDATE OR DELETE "
        "ON document_versions FOR EACH ROW EXECUTE FUNCTION "
        "ude_reject_immutable_version_mutation();"
    )
    op.execute(
        "CREATE TRIGGER rule_set_versions_are_immutable BEFORE UPDATE OR DELETE "
        "ON rule_set_versions FOR EACH ROW EXECUTE FUNCTION "
        "ude_reject_immutable_version_mutation();"
    )
    for table_name in (
        "tenant_memberships",
        "documents",
        "rule_sets",
        "processing_runs",
        "review_tasks",
        "audit_events",
    ):
        op.execute(
            f"CREATE TRIGGER {table_name}_tenant_id_is_immutable "
            f"BEFORE UPDATE OF tenant_id ON {table_name} FOR EACH ROW "
            "EXECUTE FUNCTION ude_reject_tenant_id_mutation();"
        )


def downgrade() -> None:
    for table_name in (
        "audit_events",
        "review_tasks",
        "processing_runs",
        "rule_sets",
        "documents",
        "tenant_memberships",
    ):
        op.execute(f"DROP TRIGGER {table_name}_tenant_id_is_immutable ON {table_name}")
    op.execute("DROP TRIGGER rule_set_versions_are_immutable ON rule_set_versions")
    op.execute("DROP TRIGGER document_versions_are_immutable ON document_versions")
    op.execute("DROP FUNCTION ude_reject_tenant_id_mutation")
    op.execute("DROP FUNCTION ude_reject_immutable_version_mutation")
    op.drop_index("ix_audit_events_target_identifier", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_user_id", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_review_tasks_assigned_user_id", table_name="review_tasks")
    op.drop_index("ix_review_tasks_processing_run_id", table_name="review_tasks")
    op.drop_index("ix_review_tasks_tenant_id", table_name="review_tasks")
    op.drop_table("review_tasks")
    op.drop_index("ix_processing_runs_rule_set_version_id", table_name="processing_runs")
    op.drop_index("ix_processing_runs_document_version_id", table_name="processing_runs")
    op.drop_index("ix_processing_runs_tenant_id", table_name="processing_runs")
    op.drop_table("processing_runs")
    op.drop_index("ix_rule_set_versions_rule_set_id", table_name="rule_set_versions")
    op.drop_index("ix_rule_set_versions_tenant_id", table_name="rule_set_versions")
    op.drop_table("rule_set_versions")
    op.drop_index("ix_rule_sets_tenant_id", table_name="rule_sets")
    op.drop_table("rule_sets")
    op.drop_index("ix_document_versions_document_id", table_name="document_versions")
    op.drop_index("ix_document_versions_tenant_id", table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index("ix_documents_tenant_id", table_name="documents")
    op.drop_table("documents")
    op.drop_table("tenant_memberships")
    op.drop_table("users")
    op.drop_table("tenants")

    bind = op.get_bind()
    for enum_name in (
        "audit_target_type",
        "audit_event_type",
        "review_task_state",
        "rule_set_state",
        "processing_run_state",
        "processing_execution_mode",
        "document_state",
        "membership_role",
        "tenant_state",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=False)
