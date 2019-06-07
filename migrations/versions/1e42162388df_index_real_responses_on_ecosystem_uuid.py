"""index real responses on ecosystem_uuid

Revision ID: 1e42162388df
Revises: 1d8b24e3a7de
Create Date: 2019-06-07 10:28:14.374256

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e42162388df'
down_revision = '1d8b24e3a7de'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_real_responses_ecosystem_uuid', 'responses', ['ecosystem_uuid'], unique=False, postgresql_where=sa.text('is_real_response'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_real_responses_ecosystem_uuid', table_name='responses')
    # ### end Alembic commands ###
