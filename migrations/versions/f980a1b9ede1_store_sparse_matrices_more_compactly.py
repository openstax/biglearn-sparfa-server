"""store sparse matrices more compactly

Revision ID: f980a1b9ede1
Revises: 401aba1f3839
Create Date: 2017-08-17 21:45:41.272149

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f980a1b9ede1'
down_revision = '401aba1f3839'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE ecosystem_matrices ALTER COLUMN "w_matrix" TYPE JSON USING "w_matrix"::json')
    op.execute('ALTER TABLE ecosystem_matrices ALTER COLUMN "d_matrix" TYPE JSON USING "d_matrix"::json')
    op.execute('ALTER TABLE ecosystem_matrices ALTER COLUMN "H_mask_NCxNQ" TYPE JSON USING "H_mask_NCxNQ"::json')


def downgrade():
    op.alter_column('ecosystem_matrices', 'w_matrix',
    type_=sa.String(),
    existing_type=postgresql.JSON(astext_type=sa.Text())
    )
    op.alter_column('ecosystem_matrices', 'd_matrix',
    type_=sa.String(),
    existing_type=postgresql.JSON(astext_type=sa.Text())
    )
    op.alter_column('ecosystem_matrices', 'H_mask_NCxNQ',
    type_=sa.String(),
    existing_type=postgresql.JSON(astext_type=sa.Text())
    )
