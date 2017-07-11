import logging

from sparfa_algs.sgd.sgd_cost_drew import SgdCostDrew
from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

from sparfa_server.api import fetch_exercise_calcs
from sparfa_server.models import (
    select_ecosystem_matrices,
    select_ecosystem_containers,
    select_ecosystem_responses,
    select_exercise_page_modules)

from sparfa_server.utils import load_matrix, load_mapping

logging.basicConfig(level=logging.DEBUG)

__logs__ = logging.getLogger(__name__)


def main():
    alg_name = 'mikea'

    cost_func = SgdCostDrew(
        lambda_f=1.0,
        lambda_g_H_l2=0.05,
        lambda_g_Hbar_l1=10.00,
        lambda_g_d_l2=0.05,
    )

    calcs = fetch_exercise_calcs(alg_name)

    if calcs:
        __logs__.info('Processing {} exercise calcs'.format(len(calcs)))
        for calc in calcs:
            ecosystem_uuid = calc['ecosystem_uuid']
            Q_ids = calc['exercise_uuids']
            learner_uuid = calc['student_uuid']

            m = select_ecosystem_matrices(ecosystem_uuid)

            # w_matrix
            W_NCxNQ = load_matrix(m.w_matrix)

            # d_matrix
            d_NQx1 = load_matrix(m.d_matrix)

            # Get mappings
            C_idx_by_id = load_mapping(m.C_idx_by_id)
            Q_idx_by_id = load_mapping(m.Q_idx_by_id)
            L_idx_by_id = load_mapping(m.L_idx_by_id)

            NQ = len(Q_idx_by_id)
            NL = len(L_idx_by_id)

            responses = select_ecosystem_responses(ecosystem_uuid)

            responses = [{'L_id': r.student_uuid, 'Q_id': r.exercise_uuid,
                          'correct?': r.is_correct} for r in responses]
            L_ids = list(set([r['L_id'] for r in responses]))

            # Grade Book
            G_NQxNL, G_mask_NQxNL = SparfaAlgs._G_from_responses(NL,
                                                                 NQ,
                                                                 L_idx_by_id,
                                                                 Q_idx_by_id,
                                                                 responses)
            # Get C_ids
            containers = select_ecosystem_containers(ecosystem_uuid)

            C_ids = [container.uuid for container in containers if
                     container.is_page_module]

            exercise_pmods = select_exercise_page_modules(Q_ids,
                                                          ecosystem_uuid)
            hints = []
            for mod in exercise_pmods:
                hint = dict(
                    Q_id=mod.exercise_uuid,
                    C_id=mod.container_uuid
                )
                hints.append(hint)

            H_mask_NCxNQ = SparfaAlgs.convert_Hs(hints,
                                                 Q_ids,
                                                 C_ids)

            algs, infos = SparfaAlgs.from_W_d(W_NCxNQ,
                                              d_NQx1,
                                              H_mask_NCxNQ,
                                              G_NQxNL,
                                              G_mask_NQxNL,
                                              L_ids,
                                              Q_ids,
                                              C_ids,
                                              cost_func)
            print(algs)

    print(calcs)


if __name__ == '__main__':
    main()
