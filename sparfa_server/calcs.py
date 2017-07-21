import json

from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

from sparfa_server.models import (
    ecosystem_matrices)
from sparfa_server.db import (
    upsert_into_do_update,
    select_ecosystem_exercises,
    select_ecosystem_responses,
    select_exercise_page_modules,
    select_ecosystem_page_modules,
    select_student_responses,
    select_ecosystem_matrices, select_responses_by_response_uuids)
from sparfa_server.utils import (
    dump_matrix,
    load_matrix,
    load_mapping)


def gen_ecosystem_hints(ecosystem_uuid, exercise_uuids):
    page_modules = select_exercise_page_modules(exercise_uuids,
                                                ecosystem_uuid)
    hints = []
    for mod in page_modules:
        hint = dict(
            Q_id=mod.exercise_uuid,
            C_id=mod.container_uuid
        )
        hints.append(hint)
    return hints


def gen_ecosystem_responses(ecosystem_uuid):
    responses = select_ecosystem_responses(ecosystem_uuid)

    return [{'L_id': r.student_uuid, 'Q_id': r.exercise_uuid,
             'correct?': r.is_correct} for r in responses]


def calc_ecosystem_matrices(ecosystem_uuid):
    Q_ids = select_ecosystem_exercises(ecosystem_uuid)

    C_ids = select_ecosystem_page_modules(ecosystem_uuid)

    hints = gen_ecosystem_hints(ecosystem_uuid, Q_ids)

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
        'w_matrix': dump_matrix(algs.W_NCxNQ),
        'd_matrix': dump_matrix(algs.d_NQx1),
        'C_idx_by_id': json.dumps(algs.C_idx_by_id),
        'Q_idx_by_id': json.dumps(algs.Q_idx_by_id),
        'L_idx_by_id': json.dumps(algs.L_idx_by_id),
        'H_mask_NCxNQ': dump_matrix(algs.H_mask_NCxNQ)
    }

    upsert_into_do_update(ecosystem_matrices, matrix_values,
                          columns=['w_matrix',
                                   'd_matrix',
                                   'C_idx_by_id',
                                   'Q_idx_by_id',
                                   'L_idx_by_id',
                                   'H_mask_NCxNQ'
                                   ])
    return


def calc_ecosystem_pe(ecosystem_uuid, student_uuid, exercise_uuids):
    # Select matrices data from the db
    m = select_ecosystem_matrices(ecosystem_uuid)

    if m:

        # Load matrices from db
        W_NCxNQ = load_matrix(m.w_matrix)
        d_NQx1 = load_matrix(m.d_matrix)
        H_mask_NCxNQ = load_matrix(m.H_mask_NCxNQ)

        # Load mappings
        C_idx_by_id = load_mapping(m.C_idx_by_id)
        Q_idx_by_id = load_mapping(m.Q_idx_by_id)

        responses = select_student_responses(ecosystem_uuid,
                                             student_uuid,
                                             exercise_uuids)

        responses = [
            {
                'L_id': r.student_uuid,
                'Q_id': r.exercise_uuid,
                'responded_at': r.responded_at,
                'correct?': r.is_correct
            } for r in responses]

        L_ids = list(set([r['L_id'] for r in responses]))

        G_L_idx_by_id = {L_id: idx for idx, L_id in enumerate(L_ids)}
        G_Q_idx_by_id = {Q_id: idx for idx, Q_id in enumerate(exercise_uuids)}

        NQ = len(exercise_uuids)
        NL = len(L_ids)

        # Create Grade book for the student
        G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(NL=NL,
                                                             NQ=NQ,
                                                             L_idx_by_id=G_L_idx_by_id,
                                                             Q_idx_by_id=G_Q_idx_by_id,
                                                             responses=responses)

        # Create the SparfaAlgs object
        algs, infos = SparfaAlgs.from_W_d(W_NCxNQ=W_NCxNQ,
                                          d_NQx1=d_NQx1,
                                          H_mask_NCxNQ=H_mask_NCxNQ,
                                          G_NQxNL=G_NQxNL,
                                          G_mask_NQxNL=G_mask_NQxNL,
                                          L_ids=[student_uuid],
                                          Q_ids=list(Q_idx_by_id.keys()),
                                          C_ids=list(C_idx_by_id.keys()),
                                          )
        ordered_Q_ids = algs.tesr(target_L_id=student_uuid,
                                  target_Q_ids=exercise_uuids,
                                  target_responses=responses
                                  )

        return ordered_Q_ids
    else:
        return None


def calc_ecosystem_clues(ecosystem_uuid,
                         student_uuids,
                         exercise_uuids,
                         responses):
    m = select_ecosystem_matrices(ecosystem_uuid)

    if m:

        # Load matrices from db
        W_NCxNQ = load_matrix(m.w_matrix)
        d_NQx1 = load_matrix(m.d_matrix)
        H_mask_NCxNQ = load_matrix(m.H_mask_NCxNQ)

        # Get mappings
        C_idx_by_id = load_mapping(m.C_idx_by_id)
        Q_idx_by_id = load_mapping(m.Q_idx_by_id)

        # Construct gradebook
        response_uuids = [r['response_uuid'] for r in responses]

        responses = select_responses_by_response_uuids(response_uuids)

        # Quick sanity check that the length of responses is the same
        if len(response_uuids) != len(responses):
            raise Exception('The responses returned by the db are not the same '
                            'length as the responses from the scheduler for the '
                            'clue calculation.')
        else:
            responses = [
                {
                    'L_id': r.student_uuid,
                    'Q_id': r.exercise_uuid,
                    'responded_at': r.responded_at,
                    'correct?': r.is_correct
                } for r in responses]

        NQ = len(Q_idx_by_id)
        NL = len(student_uuids)

        G_L_idx_by_id = {L_id: idx for idx, L_id in enumerate(student_uuids)}
        G_Q_idx_by_id = {Q_id: idx for idx, Q_id in enumerate(exercise_uuids)}

        # Create Grade book for the student
        G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(NL=NL,
                                                             NQ=NQ,
                                                             L_idx_by_id=G_L_idx_by_id,
                                                             Q_idx_by_id=G_Q_idx_by_id,
                                                             responses=responses)

        # Create matrices
        algs, infos = SparfaAlgs.from_W_d(W_NCxNQ=W_NCxNQ,
                                          d_NQx1=d_NQx1,
                                          H_mask_NCxNQ=H_mask_NCxNQ,
                                          G_NQxNL=G_NQxNL,
                                          G_mask_NQxNL=G_mask_NQxNL,
                                          L_ids=student_uuids,
                                          Q_ids=list(Q_idx_by_id.keys()),
                                          C_ids=list(C_idx_by_id.keys()),
                                          )

        clue_mean, clue_min, clue_max = algs.calc_clue_interval(confidence=.5,
                                                                target_L_ids=student_uuids,
                                                                target_Q_ids=exercise_uuids)

        return clue_mean, clue_min, clue_max
    else:
        return None, None, None
