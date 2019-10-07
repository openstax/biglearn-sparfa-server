from uuid import uuid4

from pytest import raises

from sparfa_server.orm.sessions import transaction
from sparfa_server.orm.models import Course


class TestBiglearnSession(object):

    def test_upsert_values(self):
        with transaction() as session:
            # Not sent to Postgres at all
            assert session.upsert_values(Course, []) is None

            assert not session.query(Course).all()

        course_uuids = set((str(uuid4()), str(uuid4())))
        course_values = [{
            'uuid': course_uuid, 'metadata_sequence_number': i, 'sequence_number': 0
        } for i, course_uuid in enumerate(course_uuids)]

        with transaction() as session:
            with raises(TypeError):
                # ON CONFLICT DO UPDATE - Not valid without specifying (columns)
                session.upsert_values(Course, course_values,
                                      conflict_index_elements=[],
                                      conflict_update_columns=['sequence_number'])

            assert not session.query(Course).all()

        with transaction() as session:
            assert not session.query(Course).all()

            # ON CONFLICT (columns) DO NOTHING
            session.upsert_values(Course, course_values)

            courses = session.query(Course).all()

        assert len(courses) == 2
        for course in courses:
            assert course.uuid in course_uuids
            assert course.sequence_number == 0
        assert set(course.metadata_sequence_number for course in courses) == set((0, 1))

        course_values[0]['sequence_number'] = 1
        course_values[1]['sequence_number'] = 2

        with transaction() as session:
            # ON CONFLICT DO NOTHING
            session.upsert_values(Course, course_values, conflict_index_elements=[])

            courses = session.query(Course).all()

        assert len(courses) == 2
        for course in courses:
            assert course.uuid in course_uuids
            assert course.sequence_number == 0
        assert set(course.metadata_sequence_number for course in courses) == set((0, 1))

        with transaction() as session:
            # ON CONFLICT (columns) DO UPDATE
            session.upsert_values(Course, course_values,
                                  conflict_update_columns=['sequence_number'])

            courses = session.query(Course).all()

        assert len(courses) == 2
        for course in courses:
            assert course.uuid in course_uuids
            if course.uuid == course_values[0]['uuid']:
                assert course.sequence_number == 1
            else:
                assert course.sequence_number == 2
        assert set(course.metadata_sequence_number for course in courses) == set((0, 1))

    def test_upsert_models(self):
        course_1 = Course(uuid=str(uuid4()), metadata_sequence_number=0, sequence_number=0)
        course_2 = Course(uuid=str(uuid4()), metadata_sequence_number=1, sequence_number=0)
        course_uuids = set((course_1.uuid, course_2.uuid))

        with transaction() as session:
            assert not session.query(Course).all()

            # ON CONFLICT (columns) DO NOTHING
            session.upsert_models(Course, [course_1, course_2])

            courses = session.query(Course).all()

        assert len(courses) == 2
        for course in courses:
            assert course.uuid in course_uuids
            assert course.sequence_number == 0
        assert set(course.metadata_sequence_number for course in courses) == set((0, 1))

        course_1.sequence_number = 1
        course_2.sequence_number = 2

        with transaction() as session:
            # ON CONFLICT (columns) DO NOTHING
            session.upsert_models(Course, [course_1, course_2])

            courses = session.query(Course).all()

        assert len(courses) == 2
        for course in courses:
            assert course.uuid in course_uuids
            assert course.sequence_number == 0
        assert set(course.metadata_sequence_number for course in courses) == set((0, 1))

        with transaction() as session:
            # ON CONFLICT (columns) DO UPDATE
            session.upsert_models(
                Course, [course_1, course_2], conflict_update_columns=['sequence_number']
            )

            courses = session.query(Course).all()

        assert len(courses) == 2
        for course in courses:
            assert course.uuid in course_uuids
            assert course.sequence_number == (1 if course.uuid == course_1.uuid else 2)
        assert set(course.metadata_sequence_number for course in courses) == set((0, 1))


def test_transaction():
    course = Course(uuid=str(uuid4()), metadata_sequence_number=0, sequence_number=0)

    with raises(RuntimeError):
        with transaction() as session:
            assert not session.query(Course).all()

            session.add(course)

            assert session.query(Course).all() == [course]

            raise RuntimeError('rollback test')

    with transaction() as session:
        assert not session.query(Course).all()

        session.add(course)

        assert session.query(Course).all() == [course]

    with transaction() as session:
        assert session.query(Course).all() == [course]
