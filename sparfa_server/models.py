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
    W_NCxNQ = Column(JSON, nullable=False)
    d_NQx1 = Column(JSON, nullable=False)
    C_idx_by_id = Column(JSON, nullable=False)
    Q_idx_by_id = Column(JSON, nullable=False)
    H_mask_NCxNQ = Column(JSON, nullable=True)
    default_conflict_index_elements = [ecosystem_uuid]
    default_conflict_update_columns = [
          W_NCxNQ,
          d_NQx1,
          C_idx_by_id,
          Q_idx_by_id,
          H_mask_NCxNQ
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
