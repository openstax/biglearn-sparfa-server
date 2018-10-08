"""initial schema

Revision ID: 308ec807c85e
Revises: 
Create Date: 2018-10-11 14:38:19.857424

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '308ec807c85e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('courses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), nullable=False),
    sa.Column('sequence_number', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_uuid'), 'courses', ['uuid'], unique=True)
    op.create_table('ecosystem_matrices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), nullable=False),
    sa.Column('ecosystem_uuid', postgresql.UUID(), nullable=False),
    sa.Column('question_concept_matrix', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('question_difficulty_matrix', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('concepts_by_uuid', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('questions_by_uuid', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('learners_by_uuid', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('hints_mask_matrix', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ecosystem_matrices_ecosystem_uuid'), 'ecosystem_matrices', ['ecosystem_uuid'], unique=True)
    op.create_index(op.f('ix_ecosystem_matrices_uuid'), 'ecosystem_matrices', ['uuid'], unique=True)
    op.create_table('ecosystems',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), nullable=False),
    sa.Column('sequence_number', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ecosystems_uuid'), 'ecosystems', ['uuid'], unique=True)
    op.create_table('page_exercises',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), nullable=False),
    sa.Column('ecosystem_uuid', postgresql.UUID(), nullable=False),
    sa.Column('page_uuid', postgresql.UUID(), nullable=False),
    sa.Column('exercise_uuid', postgresql.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_page_exercises_ecosystem_uuid'), 'page_exercises', ['ecosystem_uuid'], unique=False)
    op.create_index('ix_page_exercises_on_exercise_uuid_and_ecosystem_uuid', 'page_exercises', ['exercise_uuid', 'ecosystem_uuid'], unique=True)
    op.create_index(op.f('ix_page_exercises_page_uuid'), 'page_exercises', ['page_uuid'], unique=False)
    op.create_index(op.f('ix_page_exercises_uuid'), 'page_exercises', ['uuid'], unique=True)
    op.create_table('responses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), nullable=False),
    sa.Column('course_uuid', postgresql.UUID(), nullable=False),
    sa.Column('ecosystem_uuid', postgresql.UUID(), nullable=False),
    sa.Column('trial_uuid', postgresql.UUID(), nullable=False),
    sa.Column('student_uuid', postgresql.UUID(), nullable=False),
    sa.Column('exercise_uuid', postgresql.UUID(), nullable=False),
    sa.Column('is_correct', sa.Boolean(), nullable=False),
    sa.Column('is_real_response', sa.Boolean(), nullable=False),
    sa.Column('responded_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_responses_course_uuid'), 'responses', ['course_uuid'], unique=False)
    op.create_index(op.f('ix_responses_ecosystem_uuid'), 'responses', ['ecosystem_uuid'], unique=False)
    op.create_index(op.f('ix_responses_exercise_uuid'), 'responses', ['exercise_uuid'], unique=False)
    op.create_index(op.f('ix_responses_student_uuid'), 'responses', ['student_uuid'], unique=False)
    op.create_index(op.f('ix_responses_trial_uuid'), 'responses', ['trial_uuid'], unique=False)
    op.create_index(op.f('ix_responses_uuid'), 'responses', ['uuid'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_responses_uuid'), table_name='responses')
    op.drop_index(op.f('ix_responses_trial_uuid'), table_name='responses')
    op.drop_index(op.f('ix_responses_student_uuid'), table_name='responses')
    op.drop_index(op.f('ix_responses_exercise_uuid'), table_name='responses')
    op.drop_index(op.f('ix_responses_ecosystem_uuid'), table_name='responses')
    op.drop_index(op.f('ix_responses_course_uuid'), table_name='responses')
    op.drop_table('responses')
    op.drop_index(op.f('ix_page_exercises_uuid'), table_name='page_exercises')
    op.drop_index(op.f('ix_page_exercises_page_uuid'), table_name='page_exercises')
    op.drop_index('ix_page_exercises_on_exercise_uuid_and_ecosystem_uuid', table_name='page_exercises')
    op.drop_index(op.f('ix_page_exercises_ecosystem_uuid'), table_name='page_exercises')
    op.drop_table('page_exercises')
    op.drop_index(op.f('ix_ecosystems_uuid'), table_name='ecosystems')
    op.drop_table('ecosystems')
    op.drop_index(op.f('ix_ecosystem_matrices_uuid'), table_name='ecosystem_matrices')
    op.drop_index(op.f('ix_ecosystem_matrices_ecosystem_uuid'), table_name='ecosystem_matrices')
    op.drop_table('ecosystem_matrices')
    op.drop_index(op.f('ix_courses_uuid'), table_name='courses')
    op.drop_table('courses')
    # ### end Alembic commands ###
