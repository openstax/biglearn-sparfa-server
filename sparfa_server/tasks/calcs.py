from collections import defaultdict
from uuid import UUID
from textwrap import dedent
from random import shuffle

from sqlalchemy import text
from sqlalchemy.sql.expression import func

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
        # biglearn-scheduler is guaranteed to only send 1 matrix calculation per ecosystem at a time
        calculation_by_ecosystem_uuid = {}
        for calculation in calculations:
            calculation_by_ecosystem_uuid[calculation['ecosystem_uuid']] = calculation

        calc_ecosystem_uuids = calculation_by_ecosystem_uuid.keys()

        with transaction() as session:
            # Skip unknown ecosystems and ecosystems we can't lock immediately
            known_ecosystems = session.query(Ecosystem).filter(
                Ecosystem.uuid.in_(calc_ecosystem_uuids), Ecosystem.sequence_number > 0
            ).with_for_update(key_share=True, skip_locked=True).limit(ECOSYSTEM_BATCH_SIZE).all()

            if not known_ecosystems:
                break

            ecosystems = []
            ecosystem_matrix_requests = []
            for eco in known_ecosystems:
                calc = calculation_by_ecosystem_uuid[eco.uuid]
                # Skip ecosystems we already calculated
                if eco.last_ecosystem_matrix_update_calculation_uuid != calc['calculation_uuid']:
                    eco.last_ecosystem_matrix_update_calculation_uuid = calc['calculation_uuid']
                    ecosystems.append(eco)
                # Tell biglearn-scheduler we calculated all ecosystems,
                # even ones we skipped because we had already calculated them
                ecosystem_matrix_requests.append({'calculation_uuid': calc['calculation_uuid']})

            if ecosystems:
                ecosystem_uuids = [ecosystem.uuid for ecosystem in ecosystems]

                pages = session.query(Page).filter(Page.ecosystem_uuid.in_(ecosystem_uuids)).all()
                pages_by_ecosystem_uuid = defaultdict(list)
                for page in pages:
                    pages_by_ecosystem_uuid[page.ecosystem_uuid].append(page)

                responses = session.query(Response).filter(
                    Response.ecosystem_uuid.in_(ecosystem_uuids),
                    Response.is_real_response.is_(True)
                ).all()
                responses_by_ecosystem_uuid = defaultdict(list)
                for response in responses:
                    responses_by_ecosystem_uuid[response.ecosystem_uuid].append(response)

                session.upsert_models(Ecosystem, ecosystems)

                old_ecosystem_matrices = session.query(EcosystemMatrix).filter(
                    EcosystemMatrix.ecosystem_uuid.in_(ecosystem_uuids),
                    EcosystemMatrix.superseded_by_uuid.is_(None)
                ).all()

                old_matrices_by_ecosystem_uuid = defaultdict(list)
                for matrix in old_ecosystem_matrices:
                    old_matrices_by_ecosystem_uuid[matrix.ecosystem_uuid].append(matrix)

                new_ecosystem_matrices = [EcosystemMatrix.from_ecosystem_uuid_pages_responses(
                    ecosystem_uuid=ecosystem_uuid,
                    pages=pages_by_ecosystem_uuid[ecosystem_uuid],
                    responses=responses_by_ecosystem_uuid[ecosystem_uuid]
                ) for ecosystem_uuid in ecosystem_uuids]

                for ecosystem_matrix in new_ecosystem_matrices:
                    for matrix in old_matrices_by_ecosystem_uuid[ecosystem_matrix.ecosystem_uuid]:
                        matrix.superseded_by_uuid = ecosystem_matrix.uuid

                session.upsert_models(
                    EcosystemMatrix,
                    old_ecosystem_matrices + new_ecosystem_matrices,
                    conflict_update_columns=['superseded_by_uuid']
                )

        # There is a potential race condition where another worker might process the same
        # ecosystem matrix update since we end the transaction and release the locks
        # before sending the update back to biglearn-scheduler
        # This is why we store the last calculation_uuid in the ecosystem
        # and skip the actual work if it matches
        BLSCHED.ecosystem_matrices_updated(ecosystem_matrix_requests)

        calculations = BLSCHED.fetch_ecosystem_matrix_updates()


@task
def calculate_exercises():
    """Calculate all personalized exercises"""
    calculations = BLSCHED.fetch_exercise_calculations()
    while calculations:
        calculation_by_uuid = {}
        for calculation in calculations:
            calculation_by_uuid[calculation['calculation_uuid']] = calculation

        with transaction() as session:
            # Attempt to advisory lock calculations received
            # https://stackoverflow.com/a/3530326
            query = [func.pg_try_advisory_xact_lock(
                (UUID(uuid).int >> 64) - 2**63
            ).label(uuid) for uuid in calculation_by_uuid]
            result = session.execute(session.query(*query).statement).first()
            locked_calculations = [
              calculation_by_uuid[uuid] for uuid, locked in result.items() if locked
            ]

            # Process only calculations that we successfully locked
            if not locked_calculations:
                break

            calculations_by_ecosystem_uuid = defaultdict(list)
            for calculation in locked_calculations:
                calculations_by_ecosystem_uuid[calculation['ecosystem_uuid']].append(calculation)

            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.ecosystem_uuid.in_(calculations_by_ecosystem_uuid.keys()),
                EcosystemMatrix.superseded_by_uuid.is_(None)
            ).all()

            if not ecosystem_matrices:
                break

            known_exercise_uuids_by_calculation_uuid = defaultdict(set)
            unknown_exercise_uuids_by_calculation_uuid = defaultdict(set)
            calculation_values = []
            # Skip calculations that don't have an ecosystem matrix
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.ecosystem_uuid
                Q_ids_set = set(ecosystem_matrix.Q_ids)

                ecosystem_calculations = calculations_by_ecosystem_uuid[ecosystem_uuid]
                for calculation in ecosystem_calculations:
                    calc_uuid = calculation['calculation_uuid']

                    # Partition exercise_uuids into known and unknown
                    for exercise_uuid in calculation['exercise_uuids']:
                        if exercise_uuid in Q_ids_set:
                            known_exercise_uuids_by_calculation_uuid[calc_uuid].add(exercise_uuid)
                        else:
                            unknown_exercise_uuids_by_calculation_uuid[calc_uuid].add(exercise_uuid)

                    calculation_values.append(
                        "(UUID('{0}'), UUID('{1}'), UUID('{2}'))".format(
                            calc_uuid,
                            ecosystem_uuid,
                            calculation['student_uuid']
                        )
                    )

            response_dicts_by_calculation_uuid = defaultdict(list)
            # Beware that uuid columns return UUID objects (not strings) when using from_statement()
            for result in session.query('calculation_uuid', Response).from_statement(text(dedent("""
                SELECT "values"."calculation_uuid", "responses".*
                FROM "responses" INNER JOIN (VALUES {}) AS "values"
                    ("calculation_uuid", "ecosystem_uuid", "student_uuid")
                    ON "responses"."student_uuid" = "values"."student_uuid"
                        AND "responses"."ecosystem_uuid" = "values"."ecosystem_uuid"
            """.format(', '.join(calculation_values))).strip())).all():
                calc_uuid = str(result.calculation_uuid)
                response = result.Response
                if str(
                    response.exercise_uuid
                ) in known_exercise_uuids_by_calculation_uuid[calc_uuid]:
                    response_dicts_by_calculation_uuid[calc_uuid].append(response.dict_for_algs)

            exercise_calculation_requests = []
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.ecosystem_uuid
                ecosystem_calculations = calculations_by_ecosystem_uuid[ecosystem_uuid]

                algs = ecosystem_matrix.to_sparfa_algs_with_student_uuids_responses(
                    student_uuids=[calc['student_uuid'] for calc in ecosystem_calculations],
                    responses=[
                        resp
                        for calc in ecosystem_calculations
                        for resp in response_dicts_by_calculation_uuid[calc['calculation_uuid']]
                    ]
                )

                for calculation in ecosystem_calculations:
                    calculation_uuid = calculation['calculation_uuid']

                    ordered_Q_infos = algs.tesr(
                        target_L_id=calculation['student_uuid'],
                        target_Q_ids=known_exercise_uuids_by_calculation_uuid[calculation_uuid],
                        target_responses=response_dicts_by_calculation_uuid[calculation_uuid]
                    )
                    ordered_exercise_uuids = [info.Q_id for info in ordered_Q_infos]

                    # Put any unknown exercise uuids at the end of the list in random order
                    unknown_exercise_uuids = list(
                        unknown_exercise_uuids_by_calculation_uuid[calculation_uuid]
                    )
                    shuffle(unknown_exercise_uuids)
                    ordered_exercise_uuids.extend(unknown_exercise_uuids)

                    exercise_calculation_requests.append({
                        'calculation_uuid': calculation_uuid,
                        'recommendation_uuid': ecosystem_matrix.uuid,
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
        trial_uuids = set(response['trial_uuid']
                          for calculation in calculations
                          for response in calculation['responses'])

        with transaction() as session:
            # Skip calculations with unknown responses and responses that we can't lock immediately
            responses = session.query(Response).filter(
                Response.trial_uuid.in_(trial_uuids)
            ).with_for_update(key_share=True, skip_locked=True).all()
            responses_by_trial_uuid = {}
            for response in responses:
                responses_by_trial_uuid[response.trial_uuid] = response

            calculations_by_ecosystem_uuid = defaultdict(list)
            for calc in calculations:
                if all(resp['trial_uuid'] in responses_by_trial_uuid for resp in calc['responses']):
                    calculations_by_ecosystem_uuid[calc['ecosystem_uuid']].append(calc)

            if not calculations_by_ecosystem_uuid:
                break

            ecosystem_matrices = session.query(EcosystemMatrix).filter(
                EcosystemMatrix.ecosystem_uuid.in_(calculations_by_ecosystem_uuid.keys()),
                EcosystemMatrix.superseded_by_uuid.is_(None)
            ).all()

            if not ecosystem_matrices:
                break

            clue_calculation_requests = []
            # Skip calculations that don't have an ecosystem matrix
            for ecosystem_matrix in ecosystem_matrices:
                ecosystem_uuid = ecosystem_matrix.ecosystem_uuid
                ecosystem_calculations = calculations_by_ecosystem_uuid[ecosystem_uuid]

                algs = ecosystem_matrix.to_sparfa_algs_with_student_uuids_responses(
                    student_uuids=[
                        student_uuid
                        for calculation in ecosystem_calculations
                        for student_uuid in calculation['student_uuids']
                    ],
                    responses=[responses_by_trial_uuid[response['trial_uuid']]
                               for calculation in ecosystem_calculations
                               for response in calculation['responses']]
                )

                Q_ids_set = set(ecosystem_matrix.Q_ids)

                for calculation in ecosystem_calculations:
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

            # There are no updates to the DB in this transaction,
            # so we can perform this request with the transaction still open
            # This way we keep rows locked until the update has been sent to biglearn-scheduler
            BLSCHED.update_clue_calculations(clue_calculation_requests)

        calculations = BLSCHED.fetch_clue_calculations()
