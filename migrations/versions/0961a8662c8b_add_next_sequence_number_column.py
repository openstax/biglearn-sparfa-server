"""add next sequence number column

Revision ID: 0961a8662c8b
Revises: f980a1b9ede1
Create Date: 2017-10-05 22:30:01.472304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0961a8662c8b'
down_revision = 'f980a1b9ede1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('courses', sa.Column('next_sequence_number', sa.Integer(), nullable=True))
    op.execute('''
        WITH "course_next_sequence_number" AS (
          SELECT
            "course_uuid",
            (coalesce((max("course_events"."sequence_number")), - 1) + 1) AS "next_sequence_number"
          FROM
            "course_events"
          GROUP BY
            "course_uuid"
        )
        UPDATE "courses"
        SET "next_sequence_number" = "course_next_sequence_number"."next_sequence_number"
        FROM "course_next_sequence_number"
        WHERE "course_next_sequence_number"."course_uuid" = "courses"."uuid"
    ''')
    op.alter_column('courses', 'next_sequence_number', nullable=False)
    op.create_index(op.f('ix_courses_next_sequence_number'), 'courses', ['uuid', 'next_sequence_number'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_courses_next_sequence_number'), table_name='courses')
    op.drop_column('courses', 'next_sequence_number')
