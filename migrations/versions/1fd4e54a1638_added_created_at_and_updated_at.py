"""added created_at and updated_at columns to all tables

Revision ID: 1fd4e54a1638
Revises: 1e42162388df
Create Date: 2019-09-27 13:42:38.964928

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1fd4e54a1638'
down_revision = '1e42162388df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('courses', sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('courses', 'created_at', server_default=None)
    op.add_column('courses', sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('courses', 'updated_at', server_default=None)
    op.add_column('ecosystem_matrices', sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('ecosystem_matrices', 'created_at', server_default=None)
    op.add_column('ecosystem_matrices', sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('ecosystem_matrices', 'updated_at', server_default=None)
    op.add_column('ecosystems', sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('ecosystems', 'created_at', server_default=None)
    op.add_column('ecosystems', sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('ecosystems', 'updated_at', server_default=None)
    op.add_column('pages', sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('pages', 'created_at', server_default=None)
    op.add_column('pages', sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('pages', 'updated_at', server_default=None)
    op.add_column('responses', sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('responses', 'created_at', server_default=None)
    op.add_column('responses', sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('clock_timestamp()'), nullable=False))
    op.alter_column('responses', 'updated_at', server_default=None)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('responses', 'updated_at')
    op.drop_column('responses', 'created_at')
    op.drop_column('pages', 'updated_at')
    op.drop_column('pages', 'created_at')
    op.drop_column('ecosystems', 'updated_at')
    op.drop_column('ecosystems', 'created_at')
    op.drop_column('ecosystem_matrices', 'updated_at')
    op.drop_column('ecosystem_matrices', 'created_at')
    op.drop_column('courses', 'updated_at')
    op.drop_column('courses', 'created_at')
    # ### end Alembic commands ###
