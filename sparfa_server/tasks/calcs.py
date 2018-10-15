from logging import getLogger
from json import dumps, loads
from collections import defaultdict

from sqlalchemy import text

from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

from .celery import task
from ..api import blsched
from ..sqlalchemy import transaction


def _dump_sparse_matrix(matrix):
    sparse_matrix = coo_matrix(matrix)
    return dumps({
        "data":     sparse_matrix.data.tolist(),
        "row":      sparse_matrix.row.tolist(),
        "col":      sparse_matrix.col.tolist(),
        "shape":    sparse_matrix.shape
    })


def _load_sparse_matrix(text):
    sparse_json = loads(text)
    sparse_matrix = coo_matrix(
        (sparse_json.get('data'),
        (sparse_json.get('row'), sparse_json.get('col'))),
        shape=sparse_json.get('shape')
    )

    return sparse_matrix.toarray()


def _dump_mapping(mapping):
    return dumps(list(mapping.items()))


def _load_mapping(text):
    return OrderedDict(loads(text))


@task
def calculate_ecosystem_matrices():
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
                PageExercise.page_uuid,
                PageExercise.exercise_uuid
            ).filter(PageExercise.ecosystem_uuid.in_(ecosystem_uuid)).all()
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
                    'ecosystem_uuid': ecosystem_uuid,
                    'W_NCxNQ': _dump_sparse_matrix(algs.W_NCxNQ),
                    'd_NQx1': _dump_sparse_matrix(algs.d_NQx1),
                    'C_idx_by_id': _dump_mapping(algs.C_idx_by_id),
                    'Q_idx_by_id': _dump_mapping(algs.Q_idx_by_id),
                    'H_mask_NCxNQ': _dump_sparse_matrix(algs.H_mask_NCxNQ)
                })

            session.upsert(EcosystemMatrix, ecosystem_matrix_values)

            blsched.ecosystem_matrices_updated(
                [{'calculation_uuid': calculation.uuid} for calculation in calculations]
            )

        calculations = blsched.fetch_ecosystem_matrix_updates()


@task
def calculate_exercises():
    calculations = blsched.fetch_exercise_calculations()
    while calculations:
        exercise_calculation_requests = []

        ecosystem_uuids = [calculation['ecosystem_uuid'] for calculation in calculations]

        with transaction() as session:
            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.ecosystem_uuid.in_(ecosystem_uuids)
            ).all()
            ecosystem_matrices_by_ecosystem_uuid = {}
            for matrix in ecosystem_matrices:
                ecosystem_matrices_by_ecosystem_uuid[matrix.ecosystem_uuid] = matrix

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
                values.append((ecosystem_uuid, calculation['student_uuid'], valid_exercise_uuids))

            if len(values) == 0:
                break

            values_sql = 'VALUES ' + ', '.join([str(value) for value in values])
            responses = session.query(Response).from_statement(text(dedent('''
                SELECT "responses".*, "values"."calculation_uuid"
                FROM "responses" INNER JOIN %s AS "values"
                    ("calculation_uuid", "ecosystem_uuid", "student_uuid", "exercise_uuids")
                    ON "responses"."student_uuid" = "values"."student_uuid"
                        AND "responses"."ecosystem_uuid" = "values"."ecosystem_uuid"
                        AND "responses"."exercise_uuid" IN "values"."exercise_uuids"
            '''.format(values_sql)).strip())).all()
            responses_by_calculation_uuid = defaultdict(list)
            for response in responses:
                responses_by_calculation_uuid[response.calculation_uuid].append(response)

            exercise_calculation_requests = []
            for calculation in calculations:
                ecosystem_uuid = calc['ecosystem_uuid']
                student_uuid = calc['student_uuid']

                ecosystem_matrix = ecosystem_matrices_by_ecosystem_uuid[ecosystem_uuid]

                W_NCxNQ      = _load_sparse_matrix(ecosystem_matrix.W_NCxNQ)
                d_NQx1       = _load_sparse_matrix(ecosystem_matrix.d_NQx1)
                H_mask_NCxNQ = _load_sparse_matrix(ecosystem_matrix.H_mask_NCxNQ)

                C_idx_by_id = _load_mapping(ecosystem_matrix.C_idx_by_id)
                Q_idx_by_id = _load_mapping(ecosystem_matrix.Q_idx_by_id)

                # Construct gradebook
                L_ids       = [student_uuid]
                L_idx_by_id = {L_id: idx for idx, L_id in enumerate(L_ids)}

                NL = len(L_ids)
                NQ = len(Q_idx_by_id)
                NC = len(C_idx_by_id)

                C_id_by_idx = {idx: C_id for C_id,idx in C_idx_by_id.items()}
                Q_id_by_idx = {idx: Q_id for Q_id,idx in Q_idx_by_id.items()}

                C_ids = [C_id_by_idx[idx] for idx in range(NC)]
                Q_ids = [Q_id_by_idx[idx] for idx in range(NQ)]

                valid_exercise_uuids = valid_exercise_uuids_by_calculation_uuid[calculation_uuid]

                responses = responses_by_calculation_uuid[calculation_uuid]

                # TODO make algs.tesr work with responses with dates already parsed
                # as opposed to formatting and parsing multiple times.
                responses = [{
                    'L_id':         response.student_uuid,
                    'Q_id':         response.exercise_uuid,
                    'responded_at': response.responded_at.isoformat(),
                    'correct?':     response.is_correct
                } for response in responses]

                # Create Grade book for the student
                G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(NL=NL,
                                                                     NQ=NQ,
                                                                     L_idx_by_id=L_idx_by_id,
                                                                     Q_idx_by_id=Q_idx_by_id,
                                                                     responses=responses)

                # Create the SparfaAlgs object
                algs, infos = SparfaAlgs.from_W_d(W_NCxNQ=W_NCxNQ,
                                                  d_NQx1=d_NQx1,
                                                  H_mask_NCxNQ=H_mask_NCxNQ,
                                                  G_NQxNL=G_NQxNL,
                                                  G_mask_NQxNL=G_mask_NQxNL,
                                                  L_ids=L_ids,
                                                  Q_ids=Q_ids,
                                                  C_ids=C_ids,
                                                  )

                ordered_Q_infos = algs.tesr(target_L_id=student_uuid,
                                            target_Q_ids=valid_exercise_uuids,
                                            target_responses=responses
                                            )

                ordered_exercise_uuids = [info.Q_id for info in ordered_Q_infos]

                # Put any unknown exercise uuids at the end of the list.
                unknown_exercise_uuids = list(
                    set(calc['exercise_uuids']) - set(ordered_exercise_uuids)
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
    calculations = blsched.fetch_clue_calculations()
    while calculations:
        clue_calculation_requests = []

        ecosystem_uuids = [calculation['ecosystem_uuid'] for calculation in calculations]
        response_uuids = [response['response_uuid']
                          for calculation in calculations for response in calculation['responses']]

        with transaction() as session:
            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.ecosystem_uuid.in_(ecosystem_uuids)
            ).all()
            ecosystem_matrices_by_ecosystem_uuid = {}
            for matrix in ecosystem_matrices:
                ecosystem_matrices_by_ecosystem_uuid[matrix.ecosystem_uuid] = matrix

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
                student_uuids = calculation['student_uuids']

                ecosystem_matrix = ecosystem_matrices_by_ecosystem_uuid[ecosystem_uuid]

                W_NCxNQ      = _load_sparse_matrix(ecosystem_matrix.W_NCxNQ)
                d_NQx1       = _load_sparse_matrix(ecosystem_matrix.d_NQx1)
                H_mask_NCxNQ = _load_sparse_matrix(ecosystem_matrix.H_mask_NCxNQ)

                C_idx_by_id = _load_mapping(ecosystem_matrix.C_idx_by_id)
                Q_idx_by_id = _load_mapping(ecosystem_matrix.Q_idx_by_id)

                # Construct gradebook
                L_idx_by_id = {L_id: idx for idx, L_id in enumerate(student_uuids)}

                NL = len(L_idx_by_id)
                NQ = len(Q_idx_by_id)
                NC = len(C_idx_by_id)

                C_id_by_idx = {idx: C_id for C_id,idx in C_idx_by_id.items()}
                Q_id_by_idx = {idx: Q_id for Q_id,idx in Q_idx_by_id.items()}
                L_id_by_idx = {idx: L_id for L_id,idx in L_idx_by_id.items()}

                C_ids = [C_id_by_idx[idx] for idx in range(NC)]
                Q_ids = [Q_id_by_idx[idx] for idx in range(NQ)]
                L_ids = [L_id_by_idx[idx] for idx in range(NL)]

                valid_responses = [responses_by_uuid[response['response_uuid']]
                                   for response in calculation['responses']
                                   if response.exercise_uuid in Q_idx_by_id]
                response_dicts = [{
                    'L_id':         response.student_uuid,
                    'Q_id':         response.exercise_uuid,
                    'responded_at': response.responded_at,
                    'correct?':     response.is_correct
                } for response in valid_responses]

                # Create Grade book for the student
                G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(
                    NL=NL,
                    NQ=NQ,
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
                    L_ids=student_uuids,
                    Q_ids=Q_ids,
                    C_ids=C_ids
                )

                valid_exercise_uuids = [response['exercise_uuid'] for response in valid_responses]
                clue_mean, clue_min, clue_max, clue_is_real = algs.calc_clue_interval(
                    confidence=.5,
                    target_L_ids=student_uuids,
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
