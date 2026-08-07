"""Establish the migration baseline without business tables.

Revision ID: 20260804_0001
Revises: None
Create Date: 2026-08-04
"""

from collections.abc import Sequence

revision: str = "20260804_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create no tables; this revision establishes the migration chain."""


def downgrade() -> None:
    """Remove no tables; the baseline contains no schema objects."""
