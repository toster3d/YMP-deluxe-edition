"""create meal type enum

Revision ID: dbfcb77a996b
Revises: a71eab61f4e8
Create Date: 2025-02-14 08:20:31.889872+00:00
"""
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'dbfcb77a996b'
down_revision: str | None = 'a71eab61f4e8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # Najpierw tworzymy typ enum
    op.execute("""
        CREATE TYPE meal_type_enum AS ENUM (
            'breakfast',
            'lunch',
            'dinner',
            'dessert'
        )
    """)
    
    # Potem zmieniamy typ kolumny
    op.alter_column('recipes', 'meal_type',
                    type_=postgresql.ENUM('breakfast', 'lunch', 'dinner', 'dessert', 
                                        name='meal_type_enum'),
                    existing_type=sa.VARCHAR(length=20),
                    postgresql_using="meal_type::meal_type_enum",
                    nullable=False)

def downgrade() -> None:
    # Najpierw zmieniamy typ kolumny z powrotem na varchar
    op.alter_column('recipes', 'meal_type',
                    type_=sa.VARCHAR(length=20),
                    existing_type=postgresql.ENUM('breakfast', 'lunch', 'dinner', 'dessert', 
                                                name='meal_type_enum'),
                    nullable=False)
    
    # Potem usuwamy typ enum
    op.execute("DROP TYPE meal_type_enum")
