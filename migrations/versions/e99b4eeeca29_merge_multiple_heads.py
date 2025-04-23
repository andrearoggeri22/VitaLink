"""merge multiple heads

Revision ID: e99b4eeeca29
Revises: add_enum_values, 5fa3c7a8532d
Create Date: 2025-04-23 17:07:28.349755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e99b4eeeca29'
down_revision = ('add_enum_values', '5fa3c7a8532d')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
