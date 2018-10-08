from sqlalchemy import Column, Index, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON, UUID

class Base(object):
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, nullable=False, index=True, unique=True)
    default_conflict_index_elements = ['uuid']
    default_conflict_update_columns = None


Base = declarative_base(cls=Base)


class Course(Base):
    __tablename__ = 'courses'
    sequence_number = Column(Integer, nullable=False)


class Ecosystem(Base):
    __tablename__ = 'ecosystems'
    sequence_number = Column(Integer, nullable=False)


class PageExercise(Base):
    __tablename__ = 'page_exercises'
    ecosystem_uuid = Column(UUID, nullable=False, index=True)
    page_uuid = Column(UUID, nullable=False, index=True)
    exercise_uuid = Column(UUID, nullable=False)

    __table_args__ = (
        Index(
            'ix_page_exercises_on_exercise_uuid_and_ecosystem_uuid',
            exercise_uuid,
            ecosystem_uuid,
            unique=True
        ),
    )


class EcosystemMatrix(Base):
    __tablename__ = 'ecosystem_matrices'
    ecosystem_uuid = Column(UUID, nullable=False, index=True, unique=True)
    question_concept_matrix = Column(JSON, nullable=False)
    question_difficulty_matrix = Column(JSON, nullable=False)
    concepts_by_uuid = Column(JSON, nullable=False)
    questions_by_uuid = Column(JSON, nullable=False)
    learners_by_uuid = Column(JSON, nullable=True)
    hints_mask_matrix = Column(JSON, nullable=True)
    default_conflict_index_elements = [ecosystem_uuid]
    default_conflict_update_columns = [
          question_concept_matrix,
          question_difficulty_matrix,
          concepts_by_uuid,
          questions_by_uuid,
          learners_by_uuid,
          hints_mask_matrix
    ]


class Response(Base):
    __tablename__ = 'responses'
    course_uuid = Column(UUID, nullable=False, index=True)
    ecosystem_uuid = Column(UUID, nullable=False, index=True)
    trial_uuid = Column(UUID, nullable=False, index=True)
    student_uuid = Column(UUID, nullable=False, index=True)
    exercise_uuid = Column(UUID, nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    is_real_response = Column(Boolean, nullable=False)
    responded_at = Column(DateTime, nullable=False)
