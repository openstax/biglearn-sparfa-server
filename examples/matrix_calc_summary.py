import json
import logging

from sparfa_algs.sgd.sgd_cost_drew import SgdCostDrew
from sparfa_server import api
from sparfa_server.api import update_matrix_calculations
from sparfa_server.models import (
    select_ecosystem_exercises,
    select_ecosystem_containers,
    select_ecosystem_responses,
    select_exercise_page_modules,
    ecosystem_matrices,
    upsert_into_do_update)
from sparfa_algs.sgd.sparfa_algs import SparfaAlgs

from sparfa_server.utils import dump_array

logging.basicConfig(level=logging.DEBUG)

__logs__ = logging.getLogger(__name__)


def main():
    alg_name = 'mikea'
    calcs = api.fetch_matrix_calculations(alg_name)

    cost_func = SgdCostDrew(
        lambda_f=1.0,
        lambda_g_H_l2=0.05,
        lambda_g_Hbar_l1=10.00,
        lambda_g_d_l2=0.05,
    )

    if calcs:
        __logs__.info('Processing {} matrix calcs'.format(len(calcs)))
        for calc in calcs:
            ecosystem_uuid = calc['ecosystem_uuid']

            # Q_ids
            eco_exercises = select_ecosystem_exercises(ecosystem_uuid)

            containers = select_ecosystem_containers(ecosystem_uuid)

            # C_ids
            page_modules = [container.uuid for container in containers if
                            container.is_page_module]


            exercise_pmods = select_exercise_page_modules(eco_exercises,
                                                          ecosystem_uuid)
            hints = []
            for mod in exercise_pmods:
                hint = dict(
                    Q_id=mod.exercise_uuid,
                    C_id=mod.container_uuid
                )
                hints.append(hint)

            responses = select_ecosystem_responses(ecosystem_uuid)

            responses = [{'L_id': r.student_uuid, 'Q_id': r.exercise_uuid,
                          'correct?': r.is_correct} for r in responses]
            learner_ids = list(set([r['L_id'] for r in responses]))

            algs, infos = SparfaAlgs.from_Ls_Qs_Cs_Hs_Rs(
                L_ids=learner_ids,
                Q_ids=eco_exercises,
                C_ids=page_modules,
                hints=hints,
                responses=responses,
                cost_func=cost_func
            )


            W_NCxNQ = algs.W_NCxNQ
            d_NQx1 = algs.d_NQx1

            matrix_values = {
                'ecosystem_uuid': ecosystem_uuid,
                'w_matrix': dump_array(W_NCxNQ),
                'd_matrix': dump_array(d_NQx1),
                'C_idx_by_id': json.dumps(algs.C_idx_by_id),
                'Q_idx_by_id': json.dumps(algs.Q_idx_by_id),
                'L_idx_by_id': json.dumps(algs.L_idx_by_id)
            }

            upsert_into_do_update(ecosystem_matrices, matrix_values,
                                  columns=['w_matrix',
                                           'd_matrix',
                                           'C_idx_by_id',
                                           'Q_idx_by_id',
                                           'L_idx_by_id'])

            update_matrix_calculations(alg_name, calc)

        print(algs)


if __name__ == '__main__':
    main()
