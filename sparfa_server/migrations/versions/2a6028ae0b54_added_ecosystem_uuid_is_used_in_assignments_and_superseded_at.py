"""added ecosystem_uuid, is_used_in_assignments and
   superseded_at columns to ecosystem_matrices table

Revision ID: 2a6028ae0b54
Revises: 1fd4e54a1638
Create Date: 2019-10-04 16:55:05.361473

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2a6028ae0b54'
down_revision = '1fd4e54a1638'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('courses', 'created_at', server_default=None)
    op.alter_column('courses', 'updated_at', server_default=None)
    op.alter_column('ecosystem_matrices', 'created_at', server_default=None)
    op.alter_column('ecosystem_matrices', 'updated_at', server_default=None)
    op.alter_column('ecosystems', 'created_at', server_default=None)
    op.alter_column('ecosystems', 'updated_at', server_default=None)
    op.alter_column('pages', 'created_at', server_default=None)
    op.alter_column('pages', 'updated_at', server_default=None)
    op.alter_column('responses', 'created_at', server_default=None)
    op.alter_column('responses', 'updated_at', server_default=None)

    op.alter_column('ecosystem_matrices', 'w_data', new_column_name='W_data')
    op.alter_column('ecosystem_matrices', 'w_row', new_column_name='W_row')
    op.alter_column('ecosystem_matrices', 'w_col', new_column_name='W_col')
    op.alter_column('ecosystem_matrices', 'h_mask_data', new_column_name='H_mask_data')
    op.alter_column('ecosystem_matrices', 'h_mask_row', new_column_name='H_mask_row')
    op.alter_column('ecosystem_matrices', 'h_mask_col', new_column_name='H_mask_col')

    op.add_column('ecosystem_matrices', sa.Column('ecosystem_uuid', postgresql.UUID(), nullable=True))
    op.add_column('ecosystem_matrices', sa.Column('is_used_in_assignments', sa.BOOLEAN(), server_default='FALSE', nullable=False))
    op.alter_column('ecosystem_matrices', 'is_used_in_assignments', server_default=None)
    op.add_column('ecosystem_matrices', sa.Column('superseded_at', postgresql.TIMESTAMP(), nullable=True))
    op.execute('UPDATE "ecosystem_matrices" SET "ecosystem_uuid" = "uuid"')
    op.alter_column('ecosystem_matrices', 'ecosystem_uuid', nullable=False)
    op.create_index(op.f('ix_ecosystem_matrices_ecosystem_uuid'), 'ecosystem_matrices', ['ecosystem_uuid'], unique=False)
    op.create_index('ix_deletable_ecosystem_matrices_superseded_at', 'ecosystem_matrices', ['superseded_at'], unique=False, postgresql_where=sa.text('NOT is_used_in_assignments'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_deletable_ecosystem_matrices_superseded_at', table_name='ecosystem_matrices')
    op.drop_index(op.f('ix_ecosystem_matrices_ecosystem_uuid'), table_name='ecosystem_matrices')
    op.drop_column('ecosystem_matrices', 'superseded_at')
    op.drop_column('ecosystem_matrices', 'is_used_in_assignments')
    op.drop_column('ecosystem_matrices', 'ecosystem_uuid')

    op.alter_column('ecosystem_matrices', 'H_mask_col', new_column_name='h_mask_col')
    op.alter_column('ecosystem_matrices', 'H_mask_row', new_column_name='h_mask_row')
    op.alter_column('ecosystem_matrices', 'H_mask_data', new_column_name='h_mask_data')
    op.alter_column('ecosystem_matrices', 'W_col', new_column_name='w_col')
    op.alter_column('ecosystem_matrices', 'W_row', new_column_name='w_row')
    op.alter_column('ecosystem_matrices', 'W_data', new_column_name='w_data')

    op.alter_column('courses', 'created_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('courses', 'updated_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('ecosystem_matrices', 'created_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('ecosystem_matrices', 'updated_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('ecosystems', 'created_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('ecosystems', 'updated_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('pages', 'created_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('pages', 'updated_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('responses', 'created_at', server_default=sa.text('clock_timestamp()'))
    op.alter_column('responses', 'updated_at', server_default=sa.text('clock_timestamp()'))
    # ### end Alembic commands ###
