from json import loads, dumps

from sqlalchemy import Column, Index
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, BOOLEAN, FLOAT, INTEGER, TIMESTAMP, UUID
from scipy.sparse import coo_matrix
from numpy import array

from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

__all__ = ('Course', 'Ecosystem', 'Page', 'Response', 'EcosystemMatrix')


class BaseBase(object):
    uuid = Column(UUID, primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.clock_timestamp(), nullable=False)
    updated_at = Column(
      TIMESTAMP,
      server_default=func.clock_timestamp(),
      nullable=False,
      onupdate=func.clock_timestamp()
    )
    default_conflict_index_elements = ['uuid']
    default_conflict_update_columns = None

    @property
    def dict(self):
        return {column.key: getattr(self, column.key)
                for column in self.__table__.columns
                if getattr(self, column.key) is not None}


Base = declarative_base(cls=BaseBase)


class Course(Base):
    __tablename__ = 'courses'
    metadata_sequence_number = Column(INTEGER, nullable=False, index=True, unique=True)
    sequence_number = Column(INTEGER, nullable=False)


class Ecosystem(Base):
    __tablename__ = 'ecosystems'
    metadata_sequence_number = Column(INTEGER, nullable=False, index=True, unique=True)
    sequence_number = Column(INTEGER, nullable=False)
    last_ecosystem_matrix_update_calculation_uuid = Column(UUID)


class Page(Base):
    __tablename__ = 'pages'
    ecosystem_uuid = Column(UUID, nullable=False, index=True)
    exercise_uuids = Column(ARRAY(UUID), nullable=False)


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
    __table_args__ = (Index('ix_real_responses_ecosystem_uuid',
                            ecosystem_uuid,
                            postgresql_where=is_real_response),)
    default_conflict_index_elements = ['trial_uuid']
    default_conflict_update_columns = ['uuid', 'is_correct', 'is_real_response', 'responded_at']

    @property
    def dict_for_algs(self):
        return {
            'L_id':         str(self.student_uuid),
            'Q_id':         str(self.exercise_uuid),
            'correct?':     self.is_correct,
            'responded_at': str(self.responded_at)
        }


class EcosystemMatrix(Base):
    __tablename__ = 'ecosystem_matrices'
    Q_ids = Column(ARRAY(UUID), nullable=False)
    C_ids = Column(ARRAY(UUID), nullable=False)
    d_data = Column(ARRAY(FLOAT), nullable=False)
    w_data = Column(ARRAY(FLOAT), nullable=False)
    w_row = Column(ARRAY(INTEGER), nullable=False)
    w_col = Column(ARRAY(INTEGER), nullable=False)
    h_mask_data = Column(ARRAY(BOOLEAN), nullable=False)
    h_mask_row = Column(ARRAY(INTEGER), nullable=False)
    h_mask_col = Column(ARRAY(INTEGER), nullable=False)

    @property
    def NC(self):
        return len(self.C_ids)

    @property
    def NQ(self):
        return len(self.Q_ids)

    @property
    def W_NCxNQ(self):
        return coo_matrix(
            (self.w_data, (self.w_row, self.w_col)),
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
            (self.h_mask_data, (self.h_mask_row, self.h_mask_col)),
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

    @staticmethod
    def _response_dicts_for_algs_from_responses(responses):
        return [resp if isinstance(resp, dict) else resp.dict_for_algs for resp in responses]

    @classmethod
    def from_ecosystem_uuid_pages_responses(cls, ecosystem_uuid, pages, responses):
        page_dicts = [page if isinstance(page, dict) else page.dict for page in pages]
        response_dicts = cls._response_dicts_for_algs_from_responses(responses)

        hints = [{
            'Q_id': exercise_uuid, 'C_id': page['uuid']
        } for page in page_dicts for exercise_uuid in page['exercise_uuids']]

        algs, __ = SparfaAlgs.from_Ls_Qs_Cs_Hs_Rs(
            L_ids=[response['L_id'] for response in response_dicts],
            Q_ids=[hint['Q_id'] for hint in hints],
            C_ids=[page['uuid'] for page in page_dicts],
            hints=hints,
            responses=response_dicts
        )

        return cls(
            uuid=ecosystem_uuid,
            Q_ids=algs.Q_ids,
            C_ids=algs.C_ids,
            d_NQx1=algs.d_NQx1,
            W_NCxNQ=algs.W_NCxNQ,
            H_mask_NCxNQ=algs.H_mask_NCxNQ
        )

    def to_sparfa_algs_with_student_uuids_responses(self, student_uuids, responses):
        G_NQxNL, G_mask_NQxNL = SparfaAlgs.convert_Rs(
            responses=self._response_dicts_for_algs_from_responses(responses),
            L_ids=student_uuids,
            Q_ids=self.Q_ids
        )

        # All Q's and C's in W and H must also be in Q_ids and C_ids
        # There are no restrictions on L_ids, so they can be downselected ahead of time
        algs, __ = SparfaAlgs.from_W_d(
            W_NCxNQ=self.W_NCxNQ,
            d_NQx1=self.d_NQx1,
            H_mask_NCxNQ=self.H_mask_NCxNQ,
            G_NQxNL=G_NQxNL,
            G_mask_NQxNL=G_mask_NQxNL,
            L_ids=student_uuids,
            Q_ids=self.Q_ids,
            C_ids=self.C_ids
        )

        return algs
