from celery import group

from sparfa_server import api, update_matrix_calculations, fetch_exercise_calcs
from sparfa_server.api import update_exercise_calcs, fetch_clue_calcs, \
    update_clue_calcs
from sparfa_server.db import update_ecosystem_matrix
from sparfa_server.calcs import calc_ecosystem_matrices, calc_ecosystem_pe, \
    calc_ecosystem_clues
from sparfa_server.celery import celery


alg_name = 'biglearn-sparfa'


@celery.task
def run_ecosystem_matrix_calc(calc_uuid, alg_name):
    result = calc_ecosystem_matrices(calc_uuid['ecosystem_uuid'])
    update_ecosystem_matrix(result)
    update_matrix_calculations(alg_name, calc_uuid['calculation_uuid'])


@celery.task
def run_matrix_calc_task():
    calc_uuids = api.fetch_matrix_calculations(alg_name)

    if calc_uuids:
        results = group(run_ecosystem_matrix_calc.s(calc_uuid, alg_name) for calc_uuid in calc_uuids)
        results.apply_async()


@celery.task
def run_pe_calc(calc):
    ecosystem_uuid = calc['ecosystem_uuid']
    calc_uuid = calc['calculation_uuid']
    Q_ids = calc['exercise_uuids']
    student_uuid = calc['student_uuid']

    ordered_Q_infos = calc_ecosystem_pe(ecosystem_uuid=ecosystem_uuid,
                                        student_uuid=student_uuid,
                                        exercise_uuids=Q_ids)

    if ordered_Q_infos:

        exercise_uuids = [info.Q_id for info in ordered_Q_infos]

        response = update_exercise_calcs(alg_name, calc_uuid,
                                         exercise_uuids)

        if response['calculation_status'] == 'calculation_accepted':
            return response
        else:
            raise Exception(
                'Calculation {0} for ecosystem {1} was not accepted'.format(
                    calc_uuid, ecosystem_uuid))


@celery.task
def run_pe_calc_task():
    calcs = fetch_exercise_calcs(alg_name)

    if calcs:
        results = group(run_pe_calc.s(calc) for calc in calcs)
        results.apply_async()


@celery.task
def run_clue_calc(calc):
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
        return response
    else:
        raise Exception(
            'Calculation {0} for ecosystem {1} was not accepted'.format(
                calc_uuid, ecosystem_uuid))


@celery.task
def run_clue_calc_task():
    calcs = fetch_clue_calcs(alg_name=alg_name)

    if calcs:
        results = group(run_clue_calc.s(calc) for calc in calcs)
        results.apply_async()

