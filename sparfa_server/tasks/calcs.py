import os

from celery import group

from sparfa_server import api, update_matrix_calculations, fetch_exercise_calcs
from sparfa_server.api import update_exercise_calcs, fetch_clue_calcs, \
    update_clue_calcs
from sparfa_server.db import update_ecosystem_matrix
from sparfa_server.calcs import calc_ecosystem_matrices, calc_ecosystem_pe, \
    calc_ecosystem_clues
from sparfa_server.celery import task

from sparfa_server.utils import try_log_all

alg_name = os.environ.get('BIGLEARN_ALGORITHM_NAME', 'biglearn-sparfa')


@task
def run_ecosystem_matrix_calc(calc, alg_name):
    result = calc_ecosystem_matrices(calc['ecosystem_uuid'])
    update_ecosystem_matrix(result)
    update_matrix_calculations(alg_name, calc['calculation_uuid'])


@task
def run_matrix_calcs_task():
    calcs = api.fetch_matrix_calculations(alg_name)

    if calcs:
        results = group(run_ecosystem_matrix_calc.si(calc, alg_name) for calc in calcs)
        results.apply_async(queue='calculate-matrices')


@task
def run_ecosystem_matrix_calc_simple(ecosystem_uuid, alg_name):
    result = calc_ecosystem_matrices(ecosystem_uuid)
    update_ecosystem_matrix(result)


@task
def run_matrix_all_ecosystems_task():
    all_ecosystem_uuids = session.query(Ecosystem.uuid).all()

    results = group(run_ecosystem_matrix_calc_simple.si(ecosystem_uuid, alg_name) for ecosystem_uuid in all_ecosystem_uuids)
    results.apply_async()


@try_log_all
def run_clue_calc(calc):
    ecosystem_uuid = calc['ecosystem_uuid']
    calc_uuid = calc['calculation_uuid']
    responses = calc['responses']
    student_uuids = calc['student_uuids']
    exercise_uuids = calc['exercise_uuids']

    clue_mean, clue_min, clue_max, clue_is_real = calc_ecosystem_clues(
        ecosystem_uuid=ecosystem_uuid,
        student_uuids=student_uuids,
        exercise_uuids=exercise_uuids,
        responses=responses
    )

    if (clue_mean and clue_min and clue_max) is not None:

        response = update_clue_calcs(
            alg_name=alg_name,
            calc_uuid=calc_uuid,
            ecosystem_uuid=ecosystem_uuid,
            clue_min=clue_min,
            clue_max=clue_max,
            clue_most_likely=clue_mean,
            clue_is_real=clue_is_real
        )
        if response['calculation_status'] == 'calculation_accepted':
            return response
        else:
            raise Exception(
                'Calculation {0} for ecosystem {1} was not accepted'.format(
                    calc_uuid, ecosystem_uuid))


@try_log_all
def run_pe_calc(calc):
    ecosystem_uuid = calc['ecosystem_uuid']
    calc_uuid = calc['calculation_uuid']
    Q_ids = calc['exercise_uuids']
    student_uuid = calc['student_uuid']

    exercise_uuids = calc_ecosystem_pe(ecosystem_uuid=ecosystem_uuid,
                                       student_uuid=student_uuid,
                                       exercise_uuids=Q_ids)

    if exercise_uuids:

        response = update_exercise_calcs(alg_name, calc_uuid,
                                         exercise_uuids)

        if response['calculation_status'] == 'calculation_accepted':
            return response
        else:
            raise Exception(
                'Calculation {0} for ecosystem {1} was not accepted'.format(
                    calc_uuid, ecosystem_uuid))


@task
def run_pe_calc_task(calc):
    return run_pe_calc(calc)


@task
def run_pe_calcs_task():
    calcs = fetch_exercise_calcs(alg_name)

    if calcs:
        results = group(run_pe_calc_task.si(calc) for calc in calcs)
        results.apply_async(queue='calculate-exercises')


@task
def run_clue_calc_task(calc):
    return run_clue_calc(calc)


@task
def run_clue_calcs_task():
    calcs = fetch_clue_calcs(alg_name=alg_name)

    if calcs:
        results = group(run_clue_calc_task.si(calc) for calc in calcs)
        results.apply_async(queue='calculate-clues')
