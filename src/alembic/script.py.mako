"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def schema_upgrades() -> None:
    """Schema upgrade migrations go here."""
    ${upgrades if upgrades else "pass"}


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    ${downgrades if downgrades else "pass"}


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