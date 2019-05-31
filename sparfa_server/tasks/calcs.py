from collections import defaultdict
from textwrap import dedent
from random import shuffle

from sqlalchemy import text

from ..biglearn import BLSCHED
from ..orm import transaction, Ecosystem, Page, Response, EcosystemMatrix
from .celery import task

__all__ = ('calculate_ecosystem_matrices', 'calculate_exercises', 'calculate_clues')

ECOSYSTEM_BATCH_SIZE = 1


@task
def calculate_ecosystem_matrices():
    """Calculate all ecosystem matrices"""
    calculations = BLSCHED.fetch_ecosystem_matrix_updates()
    while calculations:
        calculations_by_ecosystem_uuid = defaultdict(list)
        for calculation in calculations:
            calculations_by_ecosystem_uuid[calculation['ecosystem_uuid']].append(calculation)

        ecosystem_uuids = calculations_by_ecosystem_uuid.keys()

        with transaction() as session:
            # Skip unknown ecosystems
            known_ecosystem_uuids = [result.uuid for result in session.query(Ecosystem.uuid).filter(
                Ecosystem.uuid.in_(ecosystem_uuids), Ecosystem.sequence_number > 0
            ).with_for_update(key_share=True, skip_locked=True).limit(ECOSYSTEM_BATCH_SIZE).all()]

            if not known_ecosystem_uuids:
                break

            responses = session.query(Response).filter(
                Response.ecosystem_uuid.in_(known_ecosystem_uuids)
            ).all()
            responses_by_ecosystem_uuid = defaultdict(list)
            for response in responses:
                responses_by_ecosystem_uuid[response.ecosystem_uuid].append(response)

            pages = session.query(Page).filter(Page.ecosystem_uuid.in_(known_ecosystem_uuids)).all()
            pages_by_ecosystem_uuid = defaultdict(list)
            for page in pages:
                pages_by_ecosystem_uuid[page.ecosystem_uuid].append(page)

            ecosystem_matrix_requests = [
               {'calculation_uuid': calculation['calculation_uuid']}
               for ecosystem_uuid in known_ecosystem_uuids
               for calculation in calculations_by_ecosystem_uuid[ecosystem_uuid]
            ]

            session.upsert_models(
                EcosystemMatrix,
                [EcosystemMatrix.from_ecosystem_uuid_pages_responses(
                    ecosystem_uuid=ecosystem_uuid,
                    pages=pages_by_ecosystem_uuid[ecosystem_uuid],
                    responses=responses_by_ecosystem_uuid[ecosystem_uuid]
                ) for ecosystem_uuid in known_ecosystem_uuids],
                conflict_update_columns=[
                    'Q_ids',
                    'C_ids',
                    'd_data',
                    'w_data',
                    'w_row',
                    'w_col',
                    'h_mask_data',
                    'h_mask_row',
                    'h_mask_col'
                ]
            )

        # There is a potential race condition here where another worker might process the same
        # ecosystem matrix update since we end the transaction and release the locks
        # before sending the update back to biglearn-scheduler
        # This is our only option to avoid data loss in case the database connection is lost
        BLSCHED.ecosystem_matrices_updated(ecosystem_matrix_requests)

        calculations = BLSCHED.fetch_ecosystem_matrix_updates()


@task
def calculate_exercises():
    """Calculate all personalized exercises"""
    calculations = BLSCHED.fetch_exercise_calculations()
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

                    values.append(
                        "(UUID('{0}'), UUID('{1}'), UUID('{2}'), ARRAY[{3}]::UUID[])".format(
                            calculation_uuid,
                            ecosystem_uuid,
                            calculation['student_uuid'],
                            ', '.join("UUID('{}')".format(uuid) for uuid in known_exercise_uuids)
                        )
                    )

            response_dicts_by_calculation_uuid = defaultdict(list)
            if values:
                results = session.query('calculation_uuid', Response).from_statement(text(dedent("""
                    SELECT "values"."calculation_uuid", "responses".*
                    FROM "responses" INNER JOIN (VALUES {}) AS "values"
                        ("calculation_uuid", "ecosystem_uuid", "student_uuid", "exercise_uuids")
                        ON "responses"."student_uuid" = "values"."student_uuid"
                            AND "responses"."ecosystem_uuid" = "values"."ecosystem_uuid"
                            AND "values"."exercise_uuids" @> ARRAY["responses"."exercise_uuid"]
                """.format(', '.join(values))).strip())).all()
                for result in results:
                    response_dicts_by_calculation_uuid[result.calculation_uuid].append(
                        result.Response.dict_for_algs
                    )

            exercise_calculation_requests = []
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.uuid
                calculations = calculations_by_ecosystem_uuid[ecosystem_uuid]

                algs = ecosystem_matrix.to_sparfa_algs_with_student_uuids_responses(
                    student_uuids=[calc['student_uuid'] for calc in calculations],
                    responses=[
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
            BLSCHED.update_exercise_calculations(exercise_calculation_requests)

        calculations = BLSCHED.fetch_exercise_calculations()


@task
def calculate_clues():
    """Calculate all CLUes"""
    calculations = BLSCHED.fetch_clue_calculations()
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
            responses_by_uuid = {}
            for response in responses:
                responses_by_uuid[response.uuid] = response

            # Skip ecosystems that don't have an ecosystem matrix
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.uuid

                # Skip calculations that refer to responses we don't know about
                valid_calculations = [
                    calc for calc in calculations_by_ecosystem_uuid[ecosystem_uuid] if all(
                        rr['response_uuid'] in responses_by_uuid for rr in calc['responses']
                    )
                ]
                if not valid_calculations:
                    continue

                algs = ecosystem_matrix.to_sparfa_algs_with_student_uuids_responses(
                    student_uuids=[
                        student_uuid
                        for calculation in valid_calculations
                        for student_uuid in calculation['student_uuids']
                    ],
                    responses=[responses_by_uuid[response['response_uuid']]
                               for calc in valid_calculations
                               for response in calc['responses']]
                )

                Q_ids_set = set(ecosystem_matrix.Q_ids)

                for calculation in valid_calculations:
                    clue_mean, clue_min, clue_max, clue_is_real = algs.calc_clue_interval(
                        confidence=.5,
                        target_L_ids=calculation['student_uuids'],
                        target_Q_ids=[uuid for uuid in calculation['exercise_uuids']
                                      if uuid in Q_ids_set]
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
            BLSCHED.update_clue_calculations(clue_calculation_requests)

        calculations = BLSCHED.fetch_clue_calculations()
