from unittest.mock import patch

from pytest import raises

from sparfa_server.cli.loaders import load, ecosystem, ecosystem_both, course, course_both, all


def test_load():
    assert set(load.commands.keys()) == set(('ecosystem', 'course', 'all'))


def test_ecosystem():
    assert set(ecosystem.commands.keys()) == set(('metadata', 'events', 'both'))


def test_ecosystem_both():
    with patch(
        'sparfa_server.cli.loaders.load_ecosystem_metadata', autospec=True
    ) as load_ecosystem_metadata:
        with patch(
            'sparfa_server.cli.loaders.load_ecosystem_events', autospec=True
        ) as load_ecosystem_events:
            with raises(SystemExit):
                ecosystem_both(())

    load_ecosystem_metadata.assert_called_once()
    load_ecosystem_events.assert_called_once()


def test_course():
    assert set(course.commands.keys()) == set(('metadata', 'events', 'both'))


def test_course_both():
    with patch(
        'sparfa_server.cli.loaders.load_course_metadata', autospec=True
    ) as load_course_metadata:
        with patch(
            'sparfa_server.cli.loaders.load_course_events', autospec=True
        ) as load_course_events:
            with raises(SystemExit):
                course_both(())

    load_course_metadata.assert_called_once()
    load_course_events.assert_called_once()


def test_all():
    with patch(
        'sparfa_server.cli.loaders.load_ecosystem_metadata', autospec=True
    ) as load_ecosystem_metadata:
        with patch(
            'sparfa_server.cli.loaders.load_ecosystem_events', autospec=True
        ) as load_ecosystem_events:
            with patch(
                'sparfa_server.cli.loaders.load_course_metadata', autospec=True
            ) as load_course_metadata:
                with patch(
                    'sparfa_server.cli.loaders.load_course_events', autospec=True
                ) as load_course_events:
                    with raises(SystemExit):
                        all(())

    load_ecosystem_metadata.assert_called_once()
    load_ecosystem_events.assert_called_once()
    load_course_metadata.assert_called_once()
    load_course_events.assert_called_once()
