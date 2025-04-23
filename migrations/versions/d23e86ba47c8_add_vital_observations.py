"""add vital observations

Revision ID: d23e86ba47c8
Revises: cc82b6077aee
Create Date: 2025-04-23 15:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd23e86ba47c8'
down_revision = 'cc82b6077aee'
branch_labels = None
depends_on = None


def upgrade():
    # Create vitalsigntype enum type if it doesn't exist
    op.execute("CREATE TYPE IF NOT EXISTS vitalsigntype AS ENUM ('heart_rate', 'blood_pressure', 'oxygen_saturation', 'temperature', 'respiratory_rate', 'glucose', 'weight', 'steps', 'calories', 'distance', 'active_minutes', 'sleep_duration', 'floors_climbed')")
    
    # Create vital_observation table
    op.create_table('vital_observation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('vital_type', sa.Enum('heart_rate', 'blood_pressure', 'oxygen_saturation', 'temperature', 'respiratory_rate', 'glucose', 'weight', 'steps', 'calories', 'distance', 'active_minutes', 'sleep_duration', 'floors_climbed', name='vitalsigntype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctor.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop vital_observation table
    op.drop_table('vital_observation')