"""merge message-save and rebase heads

Revision ID: bca1d0d39d8e
Revises: 1bee6cced5cd, d9d54e36c69f
Create Date: 2026-06-30 10:46:40.566210

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bca1d0d39d8e'
down_revision = ('1bee6cced5cd', 'd9d54e36c69f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
