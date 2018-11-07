from unittest.mock import patch

from pytest import raises

from sparfa_server.cli.calcs import calc, all


def test_calc():
    assert set(calc.commands.keys()) == set(('matrices', 'exercises', 'clues', 'all'))


def test_all():
    with patch(
        'sparfa_server.cli.calcs.calculate_ecosystem_matrices', autospec=True
    ) as calculate_ecosystem_matrices:
        with patch(
            'sparfa_server.cli.calcs.calculate_exercises', autospec=True
        ) as calculate_exercises:
            with patch(
                'sparfa_server.cli.calcs.calculate_clues', autospec=True
            ) as calculate_clues:
                with raises(SystemExit):
                    all(())

    calculate_ecosystem_matrices.assert_called_once()
    calculate_exercises.assert_called_once()
    calculate_clues.assert_called_once()
