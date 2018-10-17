from json import dumps, loads
from collections import defaultdict
from textwrap import dedent

from scipy.sparse import coo_matrix
from sqlalchemy import text

from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

from .celery import task
from ..api import blsched
from ..sqlalchemy import transaction
from ..models import Response, PageExercise, EcosystemMatrix


def _dump_sparse_matrix(matrix):
    sparse_matrix = coo_matrix(matrix)
    return dumps({
        "data":     sparse_matrix.data.tolist(),
        "row":      sparse_matrix.row.tolist(),
        "col":      sparse_matrix.col.tolist(),
        "shape":    sparse_matrix.shape
    })


def _load_sparse_matrix(string):
    sparse_json = loads(string)
    return coo_matrix(
        (sparse_json.get('data'),
        (sparse_json.get('row'), sparse_json.get('col'))),
        shape=sparse_json.get('shape')
    ).toarray()


@task
def calculate_ecosystem_matrices():
    """Calculate all ecosystem matrices"""
    calculations = blsched.fetch_ecosystem_matrix_updates()
    while calculations:
        ecosystem_matrix_values = []

        with transaction() as session:
            ecosystem_uuids = [calculation['ecosystem_uuid'] for calculation in calculations]

            responses = session.query(Response).filter(
                Response.ecosystem_uuid.in_(ecosystem_uuids)
            ).all()
            responses_by_ecosystem_uuid = defaultdict(list)
            for response in responses:
                responses_by_ecosystem_uuid[response.ecosystem_uuid].append(response)

            page_exercises = session.query(
                PageExercise.ecosystem_uuid,
                PageExercise.page_uuid,
                PageExercise.exercise_uuid
            ).filter(PageExercise.ecosystem_uuid.in_(ecosystem_uuids)).all()
            page_exercises_by_ecosystem_uuid = defaultdict(list)
            for page_exercise in page_exercises:
                page_exercises_by_ecosystem_uuid[page_exercise.ecosystem_uuid].append(page_exercise)

            for calculation in calculations:
                ecosystem_uuid = calculation['ecosystem_uuid']

                responses = responses_by_ecosystem_uuid[ecosystem_uuid]
                L_ids = list(set([response.student_uuid for response in responses]))
                response_dicts = [{'L_id': response.student_uuid, 'Q_id': response.exercise_uuid,
                                   'correct?': response.is_correct} for response in responses]

                page_exercises = page_exercises_by_ecosystem_uuid[ecosystem_uuid]
                C_ids = [page_exercise.page_uuid for page_exercise in page_exercises]
                Q_ids = [page_exercise.exercise_uuid for page_exercise in page_exercises]
                hints = [{
                    'Q_id': page_exercise.exercise_uuid,
                    'C_id': page_exercise.page_uuid
                } for page_exercise in page_exercises]

                algs, __ = SparfaAlgs.from_Ls_Qs_Cs_Hs_Rs(
                    L_ids=L_ids,
                    Q_ids=Q_ids,
                    C_ids=C_ids,
                    hints=hints,
                    responses=response_dicts
                )

                ecosystem_matrix_values.append({
                    'uuid': ecosystem_uuid,
                    'W_NCxNQ': _dump_sparse_matrix(algs.W_NCxNQ),
                    'd_NQx1': _dump_sparse_matrix(algs.d_NQx1),
                    'C_idx_by_id': dumps(algs.C_idx_by_id),
                    'Q_idx_by_id': dumps(algs.Q_idx_by_id),
                    'H_mask_NCxNQ': _dump_sparse_matrix(algs.H_mask_NCxNQ)
                })

            session.upsert(EcosystemMatrix, ecosystem_matrix_values)

            blsched.ecosystem_matrices_updated([{
                'calculation_uuid': calculation['calculation_uuid']
            } for calculation in calculations])

        calculations = blsched.fetch_ecosystem_matrix_updates()


@task
def calculate_exercises():
    """Calculate all personalized exercises"""
    calculations = blsched.fetch_exercise_calculations()
    while calculations:
        exercise_calculation_requests = []

        ecosystem_uuids = [calculation['ecosystem_uuid'] for calculation in calculations]

        with transaction() as session:
            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(ecosystem_uuids)
            ).all()
            ecosystem_matrices_by_ecosystem_uuid = {}
            for matrix in ecosystem_matrices:
                ecosystem_matrices_by_ecosystem_uuid[matrix.uuid] = matrix

            # Skip calculations that don't have an ecosystem matrix
            calculations = [calc for calc in calculations
                            if calc['ecosystem_uuid'] in ecosystem_matrices_by_ecosystem_uuid]

            valid_exercise_uuids_by_calculation_uuid = {}
            values = []
            for calculation in calculations:
                ecosystem_uuid = calculation['ecosystem_uuid']

                ecosystem_matrix = ecosystem_matrices_by_ecosystem_uuid[ecosystem_uuid]

                calculation_uuid = calculation['calculation_uuid']
                valid_exercise_uuids = [uuid for uuid in calculation['exercise_uuids']
                                        if uuid in ecosystem_matrix.Q_idx_by_id]
                valid_exercise_uuids_by_calculation_uuid[calculation_uuid] = valid_exercise_uuids
                values.append("('{0}', '{1}', '{2}', ARRAY[{3}])".format(
                    calculation_uuid,
                    ecosystem_uuid,
                    calculation['student_uuid'],
                    ', '.join(["'{}'".format(uuid) for uuid in valid_exercise_uuids])
                ))

            if len(values) == 0:
                break

            results = session.query('calculation_uuid', Response).from_statement(text(dedent('''
                SELECT "values"."calculation_uuid", "responses".*
                FROM "responses" INNER JOIN (VALUES {}) AS "values"
                    ("calculation_uuid", "ecosystem_uuid", "student_uuid", "exercise_uuids")
                    ON "responses"."student_uuid" = "values"."student_uuid"::uuid
                        AND "responses"."ecosystem_uuid" = "values"."ecosystem_uuid"::uuid
                        AND "values"."exercise_uuids"::uuid[] @> ARRAY["responses"."exercise_uuid"]
            '''.format(', '.join(values))).strip())).all()
            responses_by_calculation_uuid = defaultdict(list)
            for result in results:
                responses_by_calculation_uuid[result.calculation_uuid].append(result.Response)

            exercise_calculation_requests = []
            for calculation in calculations:
                ecosystem_uuid = calculation['ecosystem_uuid']
                calculation_uuid = calculation['calculation_uuid']

                ecosystem_matrix = ecosystem_matrices_by_ecosystem_uuid[ecosystem_uuid]

                W_NCxNQ      = _load_sparse_matrix(ecosystem_matrix.W_NCxNQ)
                d_NQx1       = _load_sparse_matrix(ecosystem_matrix.d_NQx1)
                H_mask_NCxNQ = _load_sparse_matrix(ecosystem_matrix.H_mask_NCxNQ)

                C_idx_by_id = loads(ecosystem_matrix.C_idx_by_id)
                Q_idx_by_id = loads(ecosystem_matrix.Q_idx_by_id)

                # Construct gradebook
                L_id        = calculation['student_uuid']
                L_idx_by_id = {L_id: 0}

                C_ids = C_idx_by_id.keys()
                Q_ids = Q_idx_by_id.keys()

                valid_exercise_uuids = valid_exercise_uuids_by_calculation_uuid[calculation_uuid]

                # TODO: downselect Q_idx_by_id using the valid_exercise_uuids

                responses = responses_by_calculation_uuid[calculation_uuid]

                # TODO make algs.tesr work with responses with dates already parsed
                # as opposed to formatting and parsing multiple times.
                response_dicts = [{
                    'L_id':         response.student_uuid,
                    'Q_id':         response.exercise_uuid,
                    'responded_at': response.responded_at.isoformat(),
                    'correct?':     response.is_correct
                } for response in responses]

                # Create Grade book for the student
                G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(
                    NL=1,
                    NQ=len(Q_ids),
                    L_idx_by_id=L_idx_by_id,
                    Q_idx_by_id=Q_idx_by_id,
                    responses=response_dicts
                )

                # Create the SparfaAlgs object
                algs, infos = SparfaAlgs.from_W_d(
                    W_NCxNQ=W_NCxNQ,
                    d_NQx1=d_NQx1,
                    H_mask_NCxNQ=H_mask_NCxNQ,
                    G_NQxNL=G_NQxNL,
                    G_mask_NQxNL=G_mask_NQxNL,
                    L_ids=[L_id],
                    Q_ids=Q_ids,
                    C_ids=C_ids
                )

                ordered_Q_infos = algs.tesr(
                    target_L_id=L_id,
                    target_Q_ids=valid_exercise_uuids,
                    target_responses=response_dicts
                )
                ordered_exercise_uuids = [info.Q_id for info in ordered_Q_infos]

                # Put any unknown exercise uuids at the end of the list
                unknown_exercise_uuids = list(
                    set(calculation['exercise_uuids']) - set(ordered_exercise_uuids)
                )
                ordered_exercise_uuids.extend(unknown_exercise_uuids)

                exercise_calculation_requests.append({
                    'calculation_uuid': calculation_uuid,
                    'exercise_uuids': ordered_exercise_uuids
                })

            blsched.update_exercise_calculations(exercise_calculation_requests)

        calculations = blsched.fetch_exercise_calculations()

@task
def calculate_clues():
    """Calculate all CLUes"""
    calculations = blsched.fetch_clue_calculations()
    while calculations:
        clue_calculation_requests = []

        ecosystem_uuids = [calculation['ecosystem_uuid'] for calculation in calculations]
        response_uuids = [response['response_uuid']
                          for calculation in calculations for response in calculation['responses']]

        with transaction() as session:
            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(ecosystem_uuids)
            ).all()
            ecosystem_matrices_by_ecosystem_uuid = {}
            for matrix in ecosystem_matrices:
                ecosystem_matrices_by_ecosystem_uuid[matrix.uuid] = matrix

            responses = session.query(Response).filter(Response.uuid.in_(response_uuids)).all()
            responses_by_uuid = {}
            for response in responses:
                responses_by_uuid[response.uuid] = response

            # Skip calculations that don't have an ecosystem matrix
            # or that contain responses we have not received yet
            calculations = [
                calc for calc in calculations
                if calc['ecosystem_uuid'] in ecosystem_matrices_by_ecosystem_uuid
                and all(resp['response_uuid'] in responses_by_uuid for resp in calc['responses'])
            ]

            for calculation in calculations:
                ecosystem_uuid = calculation['ecosystem_uuid']

                ecosystem_matrix = ecosystem_matrices_by_ecosystem_uuid[ecosystem_uuid]

                W_NCxNQ      = _load_sparse_matrix(ecosystem_matrix.W_NCxNQ)
                d_NQx1       = _load_sparse_matrix(ecosystem_matrix.d_NQx1)
                H_mask_NCxNQ = _load_sparse_matrix(ecosystem_matrix.H_mask_NCxNQ)

                C_idx_by_id = loads(ecosystem_matrix.C_idx_by_id)
                Q_idx_by_id = loads(ecosystem_matrix.Q_idx_by_id)

                # Construct gradebook
                L_ids = calculation['student_uuids']
                L_idx_by_id = {L_id: idx for idx, L_id in enumerate(calculation['student_uuids'])}

                C_ids = C_idx_by_id.keys()
                Q_ids = Q_idx_by_id.keys()

                # TODO: downselect Q_id_by_idx using the exercise_uuids in responses

                responses = [responses_by_uuid[response['response_uuid']]
                             for response in calculation['responses']]
                valid_responses = [resp for resp in responses if resp.exercise_uuid in Q_idx_by_id]
                response_dicts = [{
                    'L_id':         response.student_uuid,
                    'Q_id':         response.exercise_uuid,
                    'responded_at': response.responded_at,
                    'correct?':     response.is_correct
                } for response in valid_responses]

                # Create Grade book for the student
                G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(
                    NL=len(L_ids),
                    NQ=len(Q_ids),
                    L_idx_by_id=L_idx_by_id,
                    Q_idx_by_id=Q_idx_by_id,
                    responses=response_dicts
                )

                # Create matrices
                algs, infos = SparfaAlgs.from_W_d(
                    W_NCxNQ=W_NCxNQ,
                    d_NQx1=d_NQx1,
                    H_mask_NCxNQ=H_mask_NCxNQ,
                    G_NQxNL=G_NQxNL,
                    G_mask_NQxNL=G_mask_NQxNL,
                    L_ids=L_ids,
                    Q_ids=Q_ids,
                    C_ids=C_ids
                )

                valid_exercise_uuids = [response.exercise_uuid for response in valid_responses]
                clue_mean, clue_min, clue_max, clue_is_real = algs.calc_clue_interval(
                    confidence=.5,
                    target_L_ids=L_ids,
                    target_Q_ids=valid_exercise_uuids
                )

                if clue_mean and clue_min and clue_max and clue_is_real is not None:
                    clue_calculation_requests.append({
                        'calculation_uuid': calculation['calculation_uuid'],
                        'clue_data': {
                            'minimum': clue_min,
                            'most_likely': clue_mean,
                            'maximum': clue_max,
                            'is_real': clue_is_real,
                            'ecosystem_uuid': ecosystem_uuid
                        }
                    })

            blsched.update_clue_calculations(clue_calculation_requests)

        calculations = blsched.fetch_clue_calculations()
