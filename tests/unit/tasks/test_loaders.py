from uuid import uuid4
from unittest.mock import patch
from datetime import datetime

from sparfa_server.orm import Ecosystem, Page, EcosystemMatrix, Course, Response
from sparfa_server.tasks.loaders import (load_ecosystem_metadata,
                                         load_ecosystem_events,
                                         _load_grouped_ecosystem_events,
                                         load_course_metadata,
                                         load_course_events,
                                         _load_grouped_course_events)
from sparfa_server.orm.sessions import BiglearnSession
from constants import UUID_REGEX


def test_load_ecosystem_metadata(transaction):
    with transaction() as session:
        assert not session.query(Ecosystem).all()

    ecosystem_dicts = [{'uuid': str(uuid4()), 'metadata_sequence_number': i} for i in range(2)]

    with patch(
        'sparfa_server.tasks.loaders.BLAPI.fetch_ecosystem_metadatas', autospec=True
    ) as fetch_ecosystem_metadatas:
        fetch_ecosystem_metadatas.return_value = ecosystem_dicts

        load_ecosystem_metadata()

    fetch_ecosystem_metadatas.assert_called_once_with(
        metadata_sequence_number_offset=0, max_num_metadatas=1000
    )

    with transaction() as session:
        ecosystems = session.query(Ecosystem).all()
        assert set(ecosystem.uuid for ecosystem in ecosystems) == \
            set(dict['uuid'] for dict in ecosystem_dicts)
        assert set(ecosystem.metadata_sequence_number for ecosystem in ecosystems) == set(range(2))


def test_load_ecosystem_events(transaction):
    ecosystem_uuids = sorted(str(uuid4()) for i in range(4))
    ecosystem_1 = Ecosystem(uuid=ecosystem_uuids[0], metadata_sequence_number=0, sequence_number=0)
    ecosystem_2 = Ecosystem(uuid=ecosystem_uuids[1], metadata_sequence_number=1, sequence_number=0)
    ecosystem_3 = Ecosystem(uuid=ecosystem_uuids[2], metadata_sequence_number=2, sequence_number=0)
    ecosystem_4 = Ecosystem(uuid=ecosystem_uuids[3], metadata_sequence_number=3, sequence_number=0)

    with transaction() as session:
        session.add(ecosystem_1)
        session.add(ecosystem_2)
        session.add(ecosystem_3)
        session.add(ecosystem_4)

    with patch(
        'sparfa_server.tasks.loaders._load_grouped_ecosystem_events', autospec=True
    ) as load_grouped_ecosystem_events:
        load_grouped_ecosystem_events.side_effect = [
            [ecosystem_1.uuid], [ecosystem_3.uuid], [], [ecosystem_1.uuid], []
        ]
        load_ecosystem_events(batch_size=2)

    for args in load_grouped_ecosystem_events.call_args_list:
        assert len(args) == 2
        assert len(args[0]) == 2
        assert isinstance(args[0][0], BiglearnSession)
        assert not args[1]
    assert [
        set(ecosystem.uuid for ecosystem in args[0][1])
        for args in load_grouped_ecosystem_events.call_args_list
    ] == [
        set((ecosystem_1.uuid, ecosystem_2.uuid)),
        set((ecosystem_3.uuid, ecosystem_4.uuid)),
        set(),
        set((ecosystem_1.uuid, ecosystem_3.uuid)),
        set((ecosystem_1.uuid,))
    ]


def test_load_grouped_ecosystem_events(transaction):
    with transaction() as session:
        assert _load_grouped_ecosystem_events(session, []) == []

    ecosystem_1 = Ecosystem(uuid=str(uuid4()), metadata_sequence_number=0, sequence_number=0)
    ecosystem_2 = Ecosystem(uuid=str(uuid4()), metadata_sequence_number=1, sequence_number=0)

    with transaction() as session:
        session.add(ecosystem_1)
        session.add(ecosystem_2)

    request_uuid_1 = str(uuid4())
    request_uuid_2 = str(uuid4())

    with patch('sparfa_server.tasks.loaders.uuid4', autospec=True) as uuid:
        uuid.side_effect = [request_uuid_1, request_uuid_2]

        chapter_uuid = str(uuid4())

        page_1_uuid = str(uuid4())
        page_1_exercise_uuids = [str(uuid4()) for i in range(4)]

        page_2_uuid = str(uuid4())
        page_2_exercise_uuids = [str(uuid4()) for i in range(4)]

        all_exercise_uuids = page_1_exercise_uuids + page_2_exercise_uuids

        with patch(
            'sparfa_server.tasks.loaders.BLAPI.fetch_ecosystem_events', autospec=True
        ) as fetch_ecosystem_events:
            fetch_ecosystem_events.return_value = [
                {
                    'request_uuid': request_uuid_1,
                    'ecosystem_uuid': ecosystem_1.uuid,
                    'events': [{
                        'sequence_number': 0,
                        'event_uuid': uuid4(),
                        'event_type': 'create_ecosystem',
                        'event_data': {
                            'ecosystem_uuid': ecosystem_1.uuid,
                            'book': {
                                'contents': [
                                    {
                                        'container_parent_uuid': uuid4(),
                                        'container_uuid': chapter_uuid,
                                        'pools': [{'exercise_uuids': all_exercise_uuids}]
                                    },
                                    {
                                        'container_parent_uuid': chapter_uuid,
                                        'container_uuid': page_1_uuid,
                                        'pools': [
                                            {'exercise_uuids': page_1_exercise_uuids},
                                            {'exercise_uuids': page_1_exercise_uuids[:2]},
                                            {'exercise_uuids': page_1_exercise_uuids[2:]}
                                        ]
                                    },
                                    {
                                        'container_parent_uuid': chapter_uuid,
                                        'container_uuid': page_2_uuid,
                                        'pools': [
                                            {'exercise_uuids': page_2_exercise_uuids},
                                            {'exercise_uuids': page_2_exercise_uuids[:2]},
                                            {'exercise_uuids': page_2_exercise_uuids[2:]}
                                        ]
                                    }
                                ]
                            }
                        }
                    }],
                    'is_gap': True,
                    'is_end': False
                },
                {
                    'request_uuid': request_uuid_2,
                    'ecosystem_uuid': ecosystem_2.uuid,
                    'events': [],
                    'is_gap': False,
                    'is_end': False
                }
            ]

            with transaction() as session:
                ecosystems = session.query(Ecosystem).all()
                assert _load_grouped_ecosystem_events(session, ecosystems) == [ecosystem_2.uuid]

    fetch_ecosystem_events.assert_called_once()
    args = fetch_ecosystem_events.call_args
    assert len(args) == 2
    assert not args[1]
    assert len(args[0]) == 1
    requests = args[0][0]
    for request in requests:
        assert request['sequence_number_offset'] == 0
        assert request['event_types'] == ['create_ecosystem']
        assert UUID_REGEX.match(request['request_uuid'])
    assert set(request['ecosystem_uuid'] for request in requests) == \
        set(ecosystem.uuid for ecosystem in ecosystems)

    with transaction() as session:
        pages = session.query(Page).all()
        ecosystem_matrices = session.query(EcosystemMatrix).all()
        ecosystems = session.query(Ecosystem).all()

    assert len(pages) == 2
    for page in pages:
        assert page.uuid in [page_1_uuid, page_2_uuid]
        assert page.ecosystem_uuid == ecosystem_1.uuid
        if page.uuid == page_1_uuid:
            assert set(page.exercise_uuids) == set(page_1_exercise_uuids)
        else:
            assert set(page.exercise_uuids) == set(page_2_exercise_uuids)

    assert len(ecosystem_matrices) == 1
    ecosystem_matrix = ecosystem_matrices[0]
    assert ecosystem_matrix.uuid == ecosystem_1.uuid
    assert set(ecosystem_matrix.C_ids) == set((page_1_uuid, page_2_uuid))
    assert set(ecosystem_matrix.Q_ids) == set(all_exercise_uuids)
    assert ecosystem_matrix.d_NQx1.shape == (ecosystem_matrix.NQ, 1)
    assert ecosystem_matrix.W_NCxNQ.shape == (ecosystem_matrix.NC, ecosystem_matrix.NQ)
    assert ecosystem_matrix.H_mask_NCxNQ.shape == (ecosystem_matrix.NC, ecosystem_matrix.NQ)

    assert len(ecosystems) == 2
    for ecosystem in ecosystems:
        assert ecosystem.uuid in [ecosystem_1.uuid, ecosystem_2.uuid]
        assert ecosystem.sequence_number == (1 if ecosystem == ecosystem_1 else 0)


def test_load_course_metadata(transaction):
    with transaction() as session:
        assert not session.query(Course).all()

    course_dicts = [{
        'uuid': str(uuid4()),
        'initial_ecosystem_uuid': str(uuid4()),
        'metadata_sequence_number': i
    } for i in range(2)]

    with patch(
        'sparfa_server.tasks.loaders.BLAPI.fetch_course_metadatas', autospec=True
    ) as fetch_course_metadatas:
        fetch_course_metadatas.return_value = course_dicts

        load_course_metadata()

    fetch_course_metadatas.assert_called_once_with(
        metadata_sequence_number_offset=0, max_num_metadatas=1000
    )

    with transaction() as session:
        courses = session.query(Course).all()
        assert set(course.uuid for course in courses) == \
            set(dict['uuid'] for dict in course_dicts)
        assert set(course.metadata_sequence_number for course in courses) == set(range(2))


def test_load_course_events(transaction):
    course_uuids = sorted(str(uuid4()) for i in range(4))
    course_1 = Course(uuid=course_uuids[0], metadata_sequence_number=0, sequence_number=0)
    course_2 = Course(uuid=course_uuids[1], metadata_sequence_number=1, sequence_number=1)
    course_3 = Course(uuid=course_uuids[2], metadata_sequence_number=2, sequence_number=2)
    course_4 = Course(uuid=course_uuids[3], metadata_sequence_number=3, sequence_number=3)

    with transaction() as session:
        session.add(course_1)
        session.add(course_2)
        session.add(course_3)
        session.add(course_4)

    with patch(
        'sparfa_server.tasks.loaders._load_grouped_course_events', autospec=True
    ) as load_grouped_course_events:
        load_grouped_course_events.side_effect = [
            [course_2.uuid], [course_3.uuid], [], [course_3.uuid], []
        ]
        load_course_events(batch_size=2)

    for args in load_grouped_course_events.call_args_list:
        assert len(args) == 2
        assert len(args[0]) == 2
        assert isinstance(args[0][0], BiglearnSession)
        assert not args[1]
    assert [
        set(course.uuid for course in args[0][1])
        for args in load_grouped_course_events.call_args_list
    ] == [
        set((course_1.uuid, course_2.uuid)),
        set((course_3.uuid, course_4.uuid)),
        set(),
        set((course_2.uuid, course_3.uuid,)),
        set((course_3.uuid,))
    ]


def test_load_grouped_course_events(transaction):
    with transaction() as session:
        assert _load_grouped_course_events(session, []) == []

    course_1 = Course(uuid=str(uuid4()), metadata_sequence_number=0, sequence_number=1)
    course_2 = Course(uuid=str(uuid4()), metadata_sequence_number=1, sequence_number=2)

    with transaction() as session:
        session.add(course_1)
        session.add(course_2)

    request_uuid_1 = str(uuid4())
    request_uuid_2 = str(uuid4())

    with patch('sparfa_server.tasks.loaders.uuid4', autospec=True) as uuid:
        uuid.side_effect = [request_uuid_1, request_uuid_2]

        response_1_uuid = str(uuid4())
        ecosystem_1_uuid = str(uuid4())
        trial_1_uuid = str(uuid4())
        student_1_uuid = str(uuid4())
        exercise_uuid = str(uuid4())
        responded_at_1 = datetime.now()

        response_2_uuid = str(uuid4())
        responded_at_2 = datetime.now()

        response_3_uuid = str(uuid4())
        ecosystem_2_uuid = str(uuid4())
        trial_2_uuid = str(uuid4())
        responded_at_3 = datetime.now()

        response_4_uuid = str(uuid4())
        ecosystem_3_uuid = str(uuid4())
        trial_3_uuid = str(uuid4())
        student_2_uuid = str(uuid4())
        responded_at_4 = datetime.now()

        response_5_uuid = str(uuid4())
        trial_4_uuid = str(uuid4())
        student_3_uuid = str(uuid4())
        responded_at_5 = datetime.now()

        with patch(
            'sparfa_server.tasks.loaders.BLAPI.fetch_course_events', autospec=True
        ) as fetch_course_events:
            fetch_course_events.return_value = [
                {
                    'request_uuid': request_uuid_1,
                    'course_uuid': course_1.uuid,
                    'events': [
                        {
                            'sequence_number': 1,
                            'event_uuid': uuid4(),
                            'event_type': 'record_response',
                            'event_data': {
                                'response_uuid': response_1_uuid,
                                'course_uuid': course_1.uuid,
                                'ecosystem_uuid': ecosystem_1_uuid,
                                'trial_uuid': trial_1_uuid,
                                'student_uuid': student_1_uuid,
                                'exercise_uuid': exercise_uuid,
                                'is_correct': False,
                                'is_real_response': True,
                                'responded_at': responded_at_1

                            }
                        },
                        {
                            'sequence_number': 2,
                            'event_uuid': uuid4(),
                            'event_type': 'record_response',
                            'event_data': {
                                'response_uuid': response_2_uuid,
                                'course_uuid': course_1.uuid,
                                'ecosystem_uuid': ecosystem_1_uuid,
                                'trial_uuid': trial_1_uuid,
                                'student_uuid': student_1_uuid,
                                'exercise_uuid': exercise_uuid,
                                'is_correct': True,
                                'is_real_response': True,
                                'responded_at': responded_at_2

                            }
                        },
                        {
                            'sequence_number': 3,
                            'event_uuid': uuid4(),
                            'event_type': 'record_response',
                            'event_data': {
                                'response_uuid': response_3_uuid,
                                'course_uuid': course_1.uuid,
                                'ecosystem_uuid': ecosystem_2_uuid,
                                'trial_uuid': trial_2_uuid,
                                'student_uuid': student_1_uuid,
                                'exercise_uuid': exercise_uuid,
                                'is_correct': False,
                                'is_real_response': True,
                                'responded_at': responded_at_3

                            }
                        }
                    ],
                    'is_gap': False,
                    'is_end': False
                },
                {
                    'request_uuid': request_uuid_2,
                    'course_uuid': course_2.uuid,
                    'events': [
                        {
                            'sequence_number': 2,
                            'event_uuid': uuid4(),
                            'event_type': 'record_response',
                            'event_data': {
                                'response_uuid': response_4_uuid,
                                'course_uuid': course_2.uuid,
                                'ecosystem_uuid': ecosystem_3_uuid,
                                'trial_uuid': trial_3_uuid,
                                'student_uuid': student_2_uuid,
                                'exercise_uuid': exercise_uuid,
                                'is_correct': True,
                                'is_real_response': False,
                                'responded_at': responded_at_4

                            }
                        },
                        {
                            'sequence_number': 3,
                            'event_uuid': uuid4(),
                            'event_type': 'record_response',
                            'event_data': {
                                'response_uuid': response_5_uuid,
                                'course_uuid': course_2.uuid,
                                'ecosystem_uuid': ecosystem_3_uuid,
                                'trial_uuid': trial_4_uuid,
                                'student_uuid': student_3_uuid,
                                'exercise_uuid': exercise_uuid,
                                'is_correct': False,
                                'is_real_response': False,
                                'responded_at': responded_at_5

                            }
                        }
                    ],
                    'is_gap': False,
                    'is_end': True
                }
            ]

            with transaction() as session:
                courses = session.query(Course).all()
                assert _load_grouped_course_events(session, courses) == [course_1.uuid]

    fetch_course_events.assert_called_once()
    args = fetch_course_events.call_args
    assert len(args) == 2
    assert not args[1]
    assert len(args[0]) == 1
    requests = args[0][0]
    for request in requests:
        assert request['sequence_number_offset'] == (
            1 if request['course_uuid'] == course_1.uuid else 2
        )
        assert request['event_types'] == ['record_response']
        assert UUID_REGEX.match(request['request_uuid'])
    assert set(request['course_uuid'] for request in requests) == \
        set(course.uuid for course in courses)

    with transaction() as session:
        responses = session.query(Response).all()
        courses = session.query(Course).all()

    assert len(responses) == 4
    for response in responses:
        assert response.course_uuid in [course_1.uuid, course_2.uuid]
        if response.course_uuid == course_1.uuid:
            assert response.trial_uuid in [trial_1_uuid, trial_2_uuid]
            if response.trial_uuid == trial_1_uuid:
                assert response.uuid == response_2_uuid
                assert response.ecosystem_uuid == ecosystem_1_uuid
                assert response.is_correct
                assert response.responded_at == responded_at_2
            else:
                assert response.uuid == response_3_uuid
                assert response.ecosystem_uuid == ecosystem_2_uuid
                assert not response.is_correct
                assert response.responded_at == responded_at_3

            assert response.student_uuid == student_1_uuid
            assert response.is_real_response
        else:
            assert response.trial_uuid in [trial_3_uuid, trial_4_uuid]
            if response.trial_uuid == trial_3_uuid:
                assert response.uuid == response_4_uuid
                assert response.student_uuid == student_2_uuid
                assert response.is_correct
                assert response.responded_at == responded_at_4
            else:
                assert response.uuid == response_5_uuid
                assert response.student_uuid == student_3_uuid
                assert not response.is_correct
                assert response.responded_at == responded_at_5

            assert response.ecosystem_uuid == ecosystem_3_uuid
            assert not response.is_real_response

        assert response.exercise_uuid == exercise_uuid

    assert len(courses) == 2
    for course in courses:
        assert course.uuid in [course_1.uuid, course_2.uuid]
        assert course.sequence_number == 4
