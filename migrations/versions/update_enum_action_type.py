"""Update action_type enum values

Revision ID: 5fa3c7a8532d
Revises: d23e86ba47c8
Create Date: 2025-04-23 17:07:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5fa3c7a8532d'
down_revision = 'd23e86ba47c8'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new type with all the needed values
    op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'sync'")


def downgrade():
    # Cannot easily remove enum values in PostgreSQL
    pass