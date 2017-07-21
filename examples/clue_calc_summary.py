import logging

from sparfa_server.api import fetch_clue_calcs, update_clue_calcs
from sparfa_server.calcs import calc_ecosystem_clues

logging.basicConfig(level=logging.DEBUG)

__logs__ = logging.getLogger(__name__)


def main():
    alg_name = 'mikea'
    calcs = fetch_clue_calcs(alg_name=alg_name)

    if calcs:
        __logs__.info('Processing {} clue calcs'.format(len(calcs)))
        for calc in calcs:
            ecosystem_uuid = calc['ecosystem_uuid']
            calc_uuid = calc['calculation_uuid']
            responses = calc['responses']
            student_uuids = calc['student_uuids']
            exercise_uuids = calc['exercise_uuids']

            clue_mean, clue_min, clue_max = calc_ecosystem_clues(
                ecosystem_uuid=ecosystem_uuid,
                student_uuids=student_uuids,
                exercise_uuids=exercise_uuids,
                responses=responses
            )

            if clue_mean and clue_min and clue_max:

                response = update_clue_calcs(
                    alg_name=alg_name,
                    calc_uuid=calc_uuid,
                    ecosystem_uuid=ecosystem_uuid,
                    clue_min=clue_min,
                    clue_max=clue_max,
                    clue_most_likely=clue_mean,
                    clue_is_real=True
                )
                if response['calculation_status'] == 'calculation_accepted':
                    continue
                else:
                    raise Exception(
                        'Calculation {0} for ecosystem {1} was not accepted'.format(
                            calc_uuid, ecosystem_uuid))
            else:
                return None


if __name__ == '__main__':
    main()
