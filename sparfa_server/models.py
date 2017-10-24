import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    JSON,
    UUID
)

metadata = sa.MetaData()

ecosystems = sa.Table('ecosystems', metadata,
                      sa.Column('id', sa.Integer, primary_key=True),
                      sa.Column('uuid', UUID, nullable=False, unique=True)
                      )

exercises = sa.Table('exercises', metadata,
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('uuid', UUID, unique=True),
                     sa.Column('group_uuid', UUID, nullable=False),
                     sa.Column('los', ARRAY(sa.String()), nullable=False),
                     sa.Column('version', sa.Integer, nullable=False)
                     )

containers = sa.Table('containers', metadata,
                      sa.Column('id',
                                sa.Integer,
                                primary_key=True),
                      sa.Column('uuid',
                                UUID,
                                unique=True),
                      sa.Column('ecosystem_uuid', UUID, nullable=False),
                      sa.Column('container_cnx_identity',
                                sa.String(50)),
                      sa.Column('container_parent_uuid',
                                UUID),
                      sa.Column('is_page_module', sa.Boolean, default=False,
                                nullable=False)
                      )

container_exercises = sa.Table('container_exercises', metadata,
                               sa.Column('id',
                                         sa.Integer,
                                         primary_key=True),
                               sa.Column('container_uuid',
                                         UUID,
                                         nullable=False,
                                         index=True),
                               sa.Column('exercise_uuid',
                                         UUID,
                                         nullable=False,
                                         index=True),
                               sa.Column('ecosystem_uuid',
                                         UUID,
                                         nullable=False),
                               sa.UniqueConstraint('container_uuid',
                                                   'ecosystem_uuid',
                                                   'exercise_uuid')
                               )

courses = sa.Table('courses', metadata,
                   sa.Column('id',
                             sa.Integer,
                             primary_key=True),
                   sa.Column('uuid',
                             UUID,
                             unique=True),
                   sa.Column('ecosystem_uuid',
                             UUID,
                             nullable=False),
                   sa.Column('next_sequence_number',
                             sa.Integer,
                             nullable=False,
                             server_default=0)
                   )

course_events = sa.Table('course_events', metadata,
                         sa.Column('id',
                                   sa.Integer,
                                   primary_key=True),
                         sa.Column('event_type',
                                   sa.String(100),
                                   nullable=False),
                         sa.Column('uuid',
                                   UUID,
                                   unique=True),
                         sa.Column('course_uuid',
                                   UUID,
                                   nullable=False),
                         sa.Column('sequence_number',
                                   sa.Integer,
                                   nullable=False),
                         sa.Column('event_data',
                                   JSON,
                                   nullable=False)
                         )

ecosystem_exercises = sa.Table('ecosystem_exercises', metadata,
                               sa.Column('id',
                                         sa.Integer,
                                         primary_key=True),
                               sa.Column('ecosystem_uuid',
                                         UUID,
                                         nullable=False,
                                         index=True),
                               sa.Column('exercise_uuid',
                                         UUID,
                                         nullable=False),
                               sa.UniqueConstraint('ecosystem_uuid',
                                                   'exercise_uuid')
                               )

responses = sa.Table('responses', metadata,
                     sa.Column('id',
                               sa.Integer,
                               primary_key=True
                               ),
                     sa.Column('uuid',
                               UUID,
                               unique=True),
                     sa.Column('ecosystem_uuid',
                               UUID,
                               nullable=False,
                               index=True),
                     sa.Column('course_uuid',
                               UUID,
                               nullable=False),
                     sa.Column('exercise_uuid',
                               UUID,
                               nullable=False),
                     sa.Column('student_uuid',
                               UUID,
                               nullable=False),
                     sa.Column('is_correct',
                               sa.Boolean,
                               nullable=False),
                     sa.Column('responded_at',
                               sa.DateTime,
                               nullable=False),
                     sa.Column('is_real_response',
                               sa.Boolean,
                               nullable=False),
                     sa.Column('sequence_number',
                               sa.Integer,
                               nullable=False),
                     sa.Column('trial_uuid',
                               UUID,
                               nullable=False)
                     )

ecosystem_matrices = sa.Table('ecosystem_matrices', metadata,
                              sa.Column('id',
                                        sa.Integer,
                                        primary_key=True
                                        ),
                              sa.Column('ecosystem_uuid',
                                        UUID,
                                        nullable=False,
                                        unique=True),
                              sa.Column('w_matrix',
                                        JSON,
                                        nullable=False),
                              sa.Column('d_matrix',
                                        JSON,
                                        nullable=False),
                              sa.Column('C_idx_by_id',
                                        JSON,
                                        nullable=False),
                              sa.Column('Q_idx_by_id',
                                        JSON,
                                        nullable=False),
                              sa.Column('L_idx_by_id',
                                        JSON,
                                        nullable=True),
                              sa.Column('H_mask_NCxNQ',
                                        JSON,
                                        nullable=True)
                              )
