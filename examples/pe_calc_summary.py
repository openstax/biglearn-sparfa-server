import logging

from sparfa_server.api import fetch_exercise_calcs, update_exercise_calcs
from sparfa_server.calcs import calc_ecosystem_pe

logging.basicConfig(level=logging.DEBUG)

__logs__ = logging.getLogger(__name__)


def main():
    alg_name = 'mikea'

    calcs = fetch_exercise_calcs(alg_name)

    if calcs:
        __logs__.info('Processing {} exercise calcs'.format(len(calcs)))
        for calc in calcs:
            ecosystem_uuid = calc['ecosystem_uuid']
            calc_uuid = calc['calculation_uuid']
            Q_ids = calc['exercise_uuids']
            student_uuid = calc['student_uuid']

            ordered_Q_infos = calc_ecosystem_pe(ecosystem_uuid=ecosystem_uuid,
                                                student_uuid=student_uuid,
                                                exercise_uuids=Q_ids)
            exercise_uuids = [info.Q_id for info in ordered_Q_infos]

            response = update_exercise_calcs(alg_name, calc_uuid,
                                             exercise_uuids)

            if response['calculation_status'] == 'calculation_accepted':
                __logs__.info(
                    'Calculation {0} for ecosystem {1} was accepted'.format(
                        calc_uuid, ecosystem_uuid))
            else:
                raise Exception(
                    'Calculation {0} for ecosystem {1} was not accepted'.format(
                        calc_uuid, ecosystem_uuid))


if __name__ == '__main__':
    main()
