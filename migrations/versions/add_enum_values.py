"""add_enum_values

Revision ID: add_enum_values
Revises: d23e86ba47c8
Create Date: 2025-04-23 16:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_enum_values'
down_revision = 'd23e86ba47c8'
branch_labels = None
depends_on = None


def upgrade():
    # Aggiungiamo il valore SYNC all'enum ActionType
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'sync'")
    
    # Aggiungiamo il valore OBSERVATION all'enum EntityType (anche se già fatto nel codice)
    op.execute("ALTER TYPE entitytype ADD VALUE IF NOT EXISTS 'observation'")


def downgrade():
    # Non è possibile rimuovere valori da un enum in PostgreSQL
    pass