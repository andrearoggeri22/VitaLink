"""add observation to entity type

Revision ID: add_observation_to_entity_type
Revises: e99b4eeeca29
Create Date: 2025-04-23 17:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_observation_to_entity_type'
down_revision = 'e99b4eeeca29'
branch_labels = None
depends_on = None


def upgrade():
    # Aggiungiamo il valore OBSERVATION all'enum EntityType
    op.execute("ALTER TYPE entitytype ADD VALUE IF NOT EXISTS 'observation'")


def downgrade():
    # Non è possibile rimuovere valori da un enum in PostgreSQL
    pass