"""set default next sequence number column value

Revision ID: e38fe662ce30
Revises: 0961a8662c8b
Create Date: 2017-10-24 18:27:49.215212

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e38fe662ce30'
down_revision = '0961a8662c8b'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('courses', 'next_sequence_number', server_default='0')


def downgrade():
    op.alter_column('courses', 'next_sequence_number', server_default=None)
