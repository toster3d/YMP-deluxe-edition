"""Merge heads

Revision ID: a71eab61f4e8
Revises: 16592c293992, 75cfc3bed192
Create Date: 2025-02-14 08:04:15.645133+00:00

"""
from typing import Sequence

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a71eab61f4e8'
down_revision: str | None = ('16592c293992', '75cfc3bed192')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def schema_upgrades() -> None:
    """Schema upgrade migrations go here."""
    pass


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    pass


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""
    pass


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
    pass


def upgrade() -> None:
    """Upgrade database to this revision."""
    schema_upgrades()


def downgrade() -> None:
    """Downgrade database from this revision."""
    schema_downgrades() 