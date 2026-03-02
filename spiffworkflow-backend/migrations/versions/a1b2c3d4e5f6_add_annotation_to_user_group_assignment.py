"""add annotation to user_group_assignment tables

Revision ID: a1b2c3d4e5f6
Revises: d98926e63d38
Create Date: 2026-03-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd98926e63d38'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_group_assignment', sa.Column('annotation', sa.Text(), nullable=True))
    op.add_column('user_group_assignment_waiting', sa.Column('annotation', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('user_group_assignment_waiting', 'annotation')
    op.drop_column('user_group_assignment', 'annotation')
