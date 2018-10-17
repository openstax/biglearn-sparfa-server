from json import loads, dumps

from sqlalchemy import Column, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, BOOLEAN, FLOAT, INTEGER, TIMESTAMP, UUID
from scipy.sparse import coo_matrix
from numpy import array


class Base(object):
    uuid = Column(UUID, primary_key=True)
    default_conflict_index_elements = ['uuid']
    default_conflict_update_columns = None

    @property
    def dict(self):
        return {column.key: getattr(self, column.key)
                for column in self.__table__.columns
                if getattr(self, column.key) is not None}


Base = declarative_base(cls=Base)


class Course(Base):
    __tablename__ = 'courses'
    sequence_number = Column(INTEGER, nullable=False)


class Ecosystem(Base):
    __tablename__ = 'ecosystems'
    sequence_number = Column(INTEGER, nullable=False)


class Page(Base):
    __tablename__ = 'pages'
    ecosystem_uuid = Column(UUID, nullable=False)
    page_uuid = Column(UUID, nullable=False)
    exercise_uuids = Column(ARRAY(UUID), nullable=False)
    default_conflict_index_elements = ['page_uuid', 'ecosystem_uuid']

    __table_args__ = (
        Index(
            'ix_pages_page_uuid_ecosystem_uuid',
            page_uuid,
            ecosystem_uuid,
            unique=True
        ),
    )


class Response(Base):
    __tablename__ = 'responses'
    course_uuid = Column(UUID, nullable=False, index=True)
    ecosystem_uuid = Column(UUID, nullable=False, index=True)
    trial_uuid = Column(UUID, nullable=False, index=True, unique=True)
    student_uuid = Column(UUID, nullable=False, index=True)
    exercise_uuid = Column(UUID, nullable=False, index=True)
    is_correct = Column(BOOLEAN, nullable=False)
    is_real_response = Column(BOOLEAN, nullable=False)
    responded_at = Column(TIMESTAMP, nullable=False)
    default_conflict_index_elements = ['trial_uuid']
    default_conflict_update_columns = ['uuid', 'is_correct', 'is_real_response', 'responded_at']

    @property
    def dict_for_algs(self):
        return {
            'L_id':         self.student_uuid,
            'Q_id':         self.exercise_uuid,
            'correct?':     self.is_correct,
            'responded_at': self.responded_at
        }


class EcosystemMatrix(Base):
    __tablename__ = 'ecosystem_matrices'
    C_ids = Column(ARRAY(UUID), nullable=False)
    Q_ids = Column(ARRAY(UUID), nullable=False)
    d_data = Column(ARRAY(FLOAT), nullable=False)
    w_data = Column(ARRAY(FLOAT), nullable=False)
    w_row = Column(ARRAY(INTEGER), nullable=False)
    w_col = Column(ARRAY(INTEGER), nullable=False)
    h_mask_data = Column(ARRAY(BOOLEAN), nullable=False)
    h_mask_row = Column(ARRAY(INTEGER), nullable=False)
    h_mask_col = Column(ARRAY(INTEGER), nullable=False)
    default_conflict_update_columns = [
        'C_ids',
        'Q_ids',
        'd_data',
        'w_data',
        'w_row',
        'w_col',
        'h_mask_data',
        'h_mask_row',
        'h_mask_col'
    ]

    @property
    def NC(self):
        return len(self.C_ids)

    @property
    def NQ(self):
        return len(self.Q_ids)

    @property
    def W_NCxNQ(self):
        return coo_matrix(
            (self.w_data,
            (self.w_row, self.w_col)),
            shape=(self.NC, self.NQ)
        ).toarray()

    @W_NCxNQ.setter
    def W_NCxNQ(self, matrix):
        sparse_matrix = coo_matrix(matrix)
        self.w_data = sparse_matrix.data.tolist()
        self.w_row = sparse_matrix.row.tolist()
        self.w_col = sparse_matrix.col.tolist()

    @property
    def H_mask_NCxNQ(self):
        return coo_matrix(
            (self.h_mask_data,
            (self.h_mask_row, self.h_mask_col)),
            shape=(self.NC, self.NQ)
        ).toarray()

    @H_mask_NCxNQ.setter
    def H_mask_NCxNQ(self, matrix):
        sparse_matrix = coo_matrix(matrix)
        self.h_mask_data = sparse_matrix.data.tolist()
        self.h_mask_row = sparse_matrix.row.tolist()
        self.h_mask_col = sparse_matrix.col.tolist()

    @property
    def d_NQx1(self):
        return array(self.d_data, ndmin=2).transpose()

    @d_NQx1.setter
    def d_NQx1(self, arr):
        self.d_data = arr.flatten().tolist()
