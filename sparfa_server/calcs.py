import json

from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

from .db import (
    select_ecosystem_responses,
    select_exercise_page_modules,
    select_ecosystem_page_modules,
    select_student_responses,
    select_ecosystem_matrices, select_responses_by_response_uuids)
from .utils import (
    dump_sparse_matrix,
    load_sparse_matrix,
    load_mapping)

from logging import getLogger

__logs__ = getLogger(__package__)


def gen_ecosystem_responses(ecosystem_uuid):
    responses = session.query(Response).filter(Response.ecosystem_uuid == ecosystem_uuid).all()

    return [{'L_id': r.student_uuid, 'Q_id': r.exercise_uuid,
             'correct?': r.is_correct} for r in responses]


def calc_ecosystem_matrices(ecosystem_uuid):
    page_exercises = session.query(
        PageExercise.page_uuid,
        PageExercise.exercise_uuid
    ).filter(PageExercise.ecosystem_uuid == ecosystem_uuid).all()

    C_ids = [page_exercise.page_uuid for page_exercise in page_exercises]
    Q_ids = [page_exercise.exercise_uuid for page_exercise in page_exercises]

    hints = [{
        'Q_id': page_exercise.exercise_uuid,
        'C_id': page_exercise.book_container_uuid
    } for page_exercise in page_exercises]

    responses = gen_ecosystem_responses(ecosystem_uuid)

    L_ids = list(set([r['L_id'] for r in responses]))

    algs, infos = SparfaAlgs.from_Ls_Qs_Cs_Hs_Rs(
        L_ids=L_ids,
        Q_ids=Q_ids,
        C_ids=C_ids,
        hints=hints,
        responses=responses,
    )

    matrix_values = {
        'ecosystem_uuid': ecosystem_uuid,
        'w_matrix': dump_sparse_matrix(algs.W_NCxNQ),
        'd_matrix': dump_sparse_matrix(algs.d_NQx1),
        'C_idx_by_id': json.dumps(algs.C_idx_by_id),
        'Q_idx_by_id': json.dumps(algs.Q_idx_by_id),
        'L_idx_by_id': json.dumps(algs.L_idx_by_id),
        'H_mask_NCxNQ': dump_sparse_matrix(algs.H_mask_NCxNQ)
    }

    return matrix_values


def get_ecosystem_matrix_by_ecosystem_uuid(ecosystem_uuid):
    return session.query(EcosystemMatrix).filter(
        EcosystemMatrix.ecosystem_uuid == ecosystem_uuid
    ).first()


def calc_ecosystem_pe(ecosystem_uuid, student_uuid, exercise_uuids):
    # Select matrices data from the db
    m = select_ecosystem_matrices(ecosystem_uuid)

    if m:

        # Load matrices from db
        W_NCxNQ      = load_sparse_matrix(m.w_matrix)
        d_NQx1       = load_sparse_matrix(m.d_matrix)
        H_mask_NCxNQ = load_sparse_matrix(m.H_mask_NCxNQ)

        # Load mappings
        C_idx_by_id = load_mapping(m.C_idx_by_id)
        Q_idx_by_id = load_mapping(m.Q_idx_by_id)

        L_ids       = [student_uuid]
        L_idx_by_id = {L_id: idx for idx,L_id in enumerate(L_ids)}

        NL = len(L_ids)
        NQ = len(Q_idx_by_id)
        NC = len(C_idx_by_id)

        C_id_by_idx = {idx: C_id for C_id,idx in C_idx_by_id.items()}
        Q_id_by_idx = {idx: Q_id for Q_id,idx in Q_idx_by_id.items()}

        C_ids = [C_id_by_idx[idx] for idx in range(NC)]
        Q_ids = [Q_id_by_idx[idx] for idx in range(NQ)]

        valid_exercise_uuids = [uuid for uuid in exercise_uuids if uuid in Q_idx_by_id]

        responses = session.query(Response).filter(
            Response.ecosystem_uuid == ecosystem_uuid,
            Response.student_uuid == student_uuid,
            Response.exercise_uuid.in_(valid_exercise_uuids)
        ).all()


        # TODO make algs.tesr work with responses with dates already parsed
        # as opposed to formatting and parsing multiple times.
        responses = [
            {
                'L_id':         r.student_uuid,
                'Q_id':         r.exercise_uuid,
                'responded_at': r.responded_at.isoformat(),
                'correct?':     r.is_correct
            } for r in responses]


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

        ## Put any unknown exercise uuids at the end of the list.
        unknown_exercise_uuids = list(set(exercise_uuids) - set(ordered_exercise_uuids))
        ordered_exercise_uuids.extend(unknown_exercise_uuids)

        return ordered_exercise_uuids
    else:
        return None


def calc_ecosystem_clues(ecosystem_uuid,
                         student_uuids,
                         exercise_uuids,
                         responses):

    clue_mean, clue_min, clue_max, clue_is_real = None, None, None, None

    m = select_ecosystem_matrices(ecosystem_uuid)

    if m:

        # Load matrices from db
        W_NCxNQ      = load_sparse_matrix(m.w_matrix)
        d_NQx1       = load_sparse_matrix(m.d_matrix)
        H_mask_NCxNQ = load_sparse_matrix(m.H_mask_NCxNQ)

        # Get mappings
        C_idx_by_id = load_mapping(m.C_idx_by_id)
        Q_idx_by_id = load_mapping(m.Q_idx_by_id)

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

        response_uuids = [r['response_uuid'] for r in responses]

        responses = session.query(Response).filter(Response.uuid.in_(response_uuids)).all()

        # Quick sanity check that the length of responses is the same
        if len(response_uuids) != len(responses):
            raise Exception('The responses returned by the db are not the same '
                            'length as the responses from the scheduler for the '
                            'clue calculation.')
        else:
            responses = [
                {
                    'L_id':         r.student_uuid,
                    'Q_id':         r.exercise_uuid,
                    'responded_at': r.responded_at,
                    'correct?':     r.is_correct
                } for r in responses if r.exercise_uuid in Q_idx_by_id]

        # Create Grade book for the student
        G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(NL=NL,
                                                             NQ=NQ,
                                                             L_idx_by_id=L_idx_by_id,
                                                             Q_idx_by_id=Q_idx_by_id,
                                                             responses=responses)

        # Create matrices
        algs, infos = SparfaAlgs.from_W_d(W_NCxNQ=W_NCxNQ,
                                          d_NQx1=d_NQx1,
                                          H_mask_NCxNQ=H_mask_NCxNQ,
                                          G_NQxNL=G_NQxNL,
                                          G_mask_NQxNL=G_mask_NQxNL,
                                          L_ids=student_uuids,
                                          Q_ids=Q_ids,
                                          C_ids=C_ids,
                                          )

        valid_exercise_uuids = [uuid for uuid in exercise_uuids if uuid in Q_idx_by_id]
        clue_mean, clue_min, clue_max, clue_is_real = algs.calc_clue_interval(
            confidence=.5,
            target_L_ids=student_uuids,
            target_Q_ids=valid_exercise_uuids
        )

    return clue_mean, clue_min, clue_max, clue_is_real
