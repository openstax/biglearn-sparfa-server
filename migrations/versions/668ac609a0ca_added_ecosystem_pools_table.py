"""added ecosystem_pools table

Revision ID: 668ac609a0ca
Revises: defaa94f1f59
Create Date: 2017-05-31 10:54:47.267667

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '668ac609a0ca'
down_revision = 'defaa94f1f59'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ecosystem_pools',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ecosystem_id', sa.Integer(), nullable=False),
    sa.Column('exercise_uuids', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('container_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['container_id'], ['containers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ecosystem_pools')
    # ### end Alembic commands ###