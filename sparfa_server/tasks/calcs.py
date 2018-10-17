from collections import defaultdict
from textwrap import dedent
from random import shuffle

from sqlalchemy import text

from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

from .celery import task
from ..api import blsched
from ..sqlalchemy import transaction
from ..models import Ecosystem, Response, Page, EcosystemMatrix


def _sparfa_algs_from_ecosystem_matrix_Ls_Rs(ecosystem_matrix, student_uuids, response_dicts):
    Q_ids = ecosystem_matrix.Q_ids

    G_NQxNL, G_mask_NQxNL = SparfaAlgs.convert_Rs(
        responses=response_dicts,
        L_ids=student_uuids,
        Q_ids=Q_ids
    )

    # All Q's and C's in W and H must also be in Q_ids and C_ids
    # There are no restrictions on L_ids, so they can be downselected ahead of time
    algs, __ = SparfaAlgs.from_W_d(
        W_NCxNQ=ecosystem_matrix.W_NCxNQ,
        d_NQx1=ecosystem_matrix.d_NQx1,
        H_mask_NCxNQ=ecosystem_matrix.H_mask_NCxNQ,
        G_NQxNL=G_NQxNL,
        G_mask_NQxNL=G_mask_NQxNL,
        L_ids=student_uuids,
        Q_ids=Q_ids,
        C_ids=ecosystem_matrix.C_ids
    )

    return algs


@task
def calculate_ecosystem_matrices():
    """Calculate all ecosystem matrices"""
    calculations = blsched.fetch_ecosystem_matrix_updates()
    while calculations:
        calculations_by_ecosystem_uuid = defaultdict(list)
        for calculation in calculations:
            calculations_by_ecosystem_uuid[calculation['ecosystem_uuid']].append(calculation)

        ecosystem_uuids = calculations_by_ecosystem_uuid.keys()
        ecosystem_matrices = []
        ecosystem_matrix_requests = []

        with transaction() as session:
            # Skip unknown ecosystems
            known_ecosystem_uuids = [result.uuid for result in session.query(Ecosystem.uuid).filter(
                Ecosystem.uuid.in_(ecosystem_uuids), Ecosystem.sequence_number > 0
            ).all()]

            if not known_ecosystem_uuids:
                break

            responses = session.query(Response).filter(
                Response.ecosystem_uuid.in_(known_ecosystem_uuids)
            ).all()
            responses_by_ecosystem_uuid = defaultdict(list)
            for response in responses:
                responses_by_ecosystem_uuid[response.ecosystem_uuid].append(response)

            pages = session.query(
                Page.ecosystem_uuid,
                Page.page_uuid,
                Page.exercise_uuids
            ).filter(Page.ecosystem_uuid.in_(known_ecosystem_uuids)).all()
            pages_by_ecosystem_uuid = defaultdict(list)
            for page in pages:
                pages_by_ecosystem_uuid[page.ecosystem_uuid].append(page)

            for ecosystem_uuid in known_ecosystem_uuids:
                responses = responses_by_ecosystem_uuid[ecosystem_uuid]
                pages = pages_by_ecosystem_uuid[ecosystem_uuid]
                hints = [{
                    'Q_id': exercise_uuid,
                    'C_id': page.page_uuid
                } for page in pages for exercise_uuid in page.exercise_uuids]

                algs, __ = SparfaAlgs.from_Ls_Qs_Cs_Hs_Rs(
                    L_ids=set([response.student_uuid for response in responses]),
                    Q_ids=[hint['Q_id'] for hint in hints],
                    C_ids=[hint['C_id'] for hint in hints],
                    hints=hints,
                    responses=[response.dict_for_algs for response in responses]
                )

                ecosystem_matrices.append(
                    EcosystemMatrix(
                        uuid=ecosystem_uuid,
                        W_NCxNQ=algs.W_NCxNQ,
                        d_NQx1=algs.d_NQx1,
                        H_mask_NCxNQ=algs.H_mask_NCxNQ,
                        Q_ids=algs.Q_ids,
                        C_ids=algs.C_ids
                    )
                )

                ecosystem_matrix_requests.extend(
                    [{'calculation_uuid': calculation['calculation_uuid']}
                     for calculation in calculations_by_ecosystem_uuid[ecosystem_uuid]]
                )

            session.upsert_models(EcosystemMatrix, ecosystem_matrices)

        # There is a potential race condition here where another worker might process the same
        # ecosystem matrix update since we end the transaction and release the locks
        # before sending the update back to biglearn-scheduler
        # This is our only option to avoid data loss in case the database connection is lost
        blsched.ecosystem_matrices_updated(ecosystem_matrix_requests)

        calculations = blsched.fetch_ecosystem_matrix_updates()


@task
def calculate_exercises():
    """Calculate all personalized exercises"""
    calculations = blsched.fetch_exercise_calculations()
    while calculations:
        calculations_by_ecosystem_uuid = defaultdict(list)
        for calculation in calculations:
            calculations_by_ecosystem_uuid[calculation['ecosystem_uuid']].append(calculation)

        exercise_calculation_requests = []

        with transaction() as session:
            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(calculations_by_ecosystem_uuid.keys())
            ).all()

            if not ecosystem_matrices:
                break

            known_exercise_uuids_by_calculation_uuid = {}
            unknown_exercise_uuids_by_calculation_uuid = {}
            values = []

            # Skip ecosystems that don't have an ecosystem matrix
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.uuid
                Q_ids_set = set(ecosystem_matrix.Q_ids)

                calculations = calculations_by_ecosystem_uuid[ecosystem_uuid]
                for calculation in calculations:
                    calculation_uuid = calculation['calculation_uuid']

                    # Partition exercise_uuids into known and unknown
                    known_exercise_uuids = []
                    unknown_exercise_uuids = []
                    for exercise_uuid in calculation['exercise_uuids']:
                        if exercise_uuid in Q_ids_set:
                            known_exercise_uuids.append(exercise_uuid)
                        else:
                            unknown_exercise_uuids.append(exercise_uuid)
                    known_exercise_uuids_by_calculation_uuid[calculation_uuid] = \
                        known_exercise_uuids
                    unknown_exercise_uuids_by_calculation_uuid[calculation_uuid] = \
                        unknown_exercise_uuids

                    values.append("('{0}', '{1}', '{2}', ARRAY[{3}])".format(
                        calculation_uuid,
                        ecosystem_uuid,
                        calculation['student_uuid'],
                        ', '.join(["'{}'".format(uuid) for uuid in known_exercise_uuids])
                    ))

            response_dicts_by_calculation_uuid = defaultdict(list)
            if values:
                results = session.query('calculation_uuid', Response).from_statement(text(dedent("""
                    SELECT "values"."calculation_uuid", "responses".*
                    FROM "responses" INNER JOIN (VALUES {}) AS "values"
                        ("calculation_uuid", "ecosystem_uuid", "student_uuid", "exercise_uuids")
                        ON "responses"."student_uuid" = "values"."student_uuid"::uuid
                            AND "responses"."ecosystem_uuid" = "values"."ecosystem_uuid"::uuid
                            AND "values"."exercise_uuids"::uuid[] @>
                                ARRAY["responses"."exercise_uuid"]
                """.format(', '.join(values))).strip())).all()
                for result in results:
                    response_dicts_by_calculation_uuid[result.calculation_uuid].append(
                        result.Response.dict_for_algs
                    )

            exercise_calculation_requests = []
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.uuid
                calculations = calculations_by_ecosystem_uuid[ecosystem_uuid]

                algs = _sparfa_algs_from_ecosystem_matrix_Ls_Rs(
                    ecosystem_matrix=ecosystem_matrix,
                    student_uuids=set([calc['student_uuid'] for calc in calculations]),
                    response_dicts=[
                        resp
                        for calc in calculations
                        for resp in response_dicts_by_calculation_uuid[calc['calculation_uuid']]
                    ]
                )

                for calculation in calculations:
                    calculation_uuid = calculation['calculation_uuid']

                    ordered_Q_infos = algs.tesr(
                        target_L_id=calculation['student_uuid'],
                        target_Q_ids=known_exercise_uuids_by_calculation_uuid[calculation_uuid],
                        target_responses=response_dicts_by_calculation_uuid[calculation_uuid]
                    )
                    ordered_exercise_uuids = [info.Q_id for info in ordered_Q_infos]

                    # Put any unknown exercise uuids at the end of the list in random order
                    unknown_exercise_uuids = \
                        unknown_exercise_uuids_by_calculation_uuid[calculation_uuid].copy()
                    shuffle(unknown_exercise_uuids)
                    ordered_exercise_uuids.extend(unknown_exercise_uuids)

                    exercise_calculation_requests.append({
                        'calculation_uuid': calculation_uuid,
                        'exercise_uuids': ordered_exercise_uuids
                    })

            # There are no updates to the DB in this transaction,
            # so we can perform this request with the transaction still open
            # This way we keep rows locked until the update has been sent to biglearn-scheduler
            blsched.update_exercise_calculations(exercise_calculation_requests)

        calculations = blsched.fetch_exercise_calculations()

@task
def calculate_clues():
    """Calculate all CLUes"""
    calculations = blsched.fetch_clue_calculations()
    while calculations:
        calculations_by_ecosystem_uuid = defaultdict(list)
        for calculation in calculations:
            calculations_by_ecosystem_uuid[calculation['ecosystem_uuid']].append(calculation)

        clue_calculation_requests = []

        with transaction() as session:
            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(calculations_by_ecosystem_uuid.keys())
            ).all()

            if not ecosystem_matrices:
                break

            response_uuids = [response['response_uuid']
                              for calculation in calculations
                              for response in calculation['responses']]
            responses = session.query(Response).filter(Response.uuid.in_(response_uuids)).all()
            response_dicts_by_uuid = {}
            for response in responses:
                response_dicts_by_uuid[response.uuid] = response.dict_for_algs

            # Skip ecosystems that don't have an ecosystem matrix
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.uuid
                Q_ids_set = set(ecosystem_matrix.Q_ids)

                # Skip calculations that refer to responses or exercises we don't know about
                valid_calculations = [
                    calc for calc in calculations_by_ecosystem_uuid[ecosystem_uuid]
                    if all(
                        rr['response_uuid'] in response_dicts_by_uuid for rr in calc['responses']
                    ) and all(uuid in Q_ids_set for uuid in calc['exercise_uuids'])
                ]

                algs = _sparfa_algs_from_ecosystem_matrix_Ls_Rs(
                    ecosystem_matrix=ecosystem_matrix,
                    student_uuids=set([
                        student_uuid
                        for calculation in valid_calculations
                        for student_uuid in calculation['student_uuids']
                    ]),
                    response_dicts=[response_dicts_by_uuid[response['response_uuid']]
                                    for calc in valid_calculations
                                    for response in calc['responses']]
                )

                for calculation in valid_calculations:
                    clue_mean, clue_min, clue_max, clue_is_real = algs.calc_clue_interval(
                        confidence=.5,
                        target_L_ids=calculation['student_uuids'],
                        target_Q_ids=calculation['exercise_uuids']
                    )

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

            if not clue_calculation_requests:
                break

            # There are no updates to the DB in this transaction,
            # so we can perform this request with the transaction still open
            # This way we keep rows locked until the update has been sent to biglearn-scheduler
            blsched.update_clue_calculations(clue_calculation_requests)

        calculations = blsched.fetch_clue_calculations()
