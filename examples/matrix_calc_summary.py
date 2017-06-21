from sparfa_algs.sgd.sgd_cost_drew import SgdCostDrew

from sparfa_server import api
from sparfa_server.models import (
    select_ecosystem_exercises,
    select_ecosystem_containers,
    select_ecosystem_responses,
    select_exercise_page_modules)
from sparfa_algs.sgd.sparfa_algs import SparfaAlgs


def main():
    calcs = api.fetch_matrix_calculations('mikea')

    cost_func = SgdCostDrew(
        lambda_f=1.0,
        lambda_g_H_l2=0.05,
        lambda_g_Hbar_l1=10.00,
        lambda_g_d_l2=0.05,
    )

    if calcs:
        for calc in calcs[89:90]:
            calc_uuid = calc['calculation_uuid']
            ecosystem_uuid = calc['ecosystem_uuid']

            # Q_ids
            eco_exercises = select_ecosystem_exercises(ecosystem_uuid)

            containers = select_ecosystem_containers(ecosystem_uuid)

            # C_ids
            page_modules = [container.uuid for container in containers if
                            container.is_page_module]

            hints = []

            for exercise_uuid in eco_exercises:
                exercise_pmods = select_exercise_page_modules(exercise_uuid,
                                                              ecosystem_uuid)
                for module in exercise_pmods:
                    hint = dict(
                        Q_id=exercise_uuid,
                        C_id=module.container_uuid
                    )
                    hints.append(hint)
            print(hints)

            responses = select_ecosystem_responses(ecosystem_uuid)

            responses = [{'L_id': r.student_uuid, 'Q_id': r.exercise_uuid,
                          'correct?': r.is_correct} for r in responses]
            learner_ids = list(set([r['L_id'] for r in responses]))

            print(responses)

            algs, infos = SparfaAlgs.from_Ls_Qs_Cs_Hs_Rs(
                L_ids=learner_ids,
                Q_ids=eco_exercises,
                C_ids=page_modules,
                hints=hints,
                responses=responses,
                cost_func=cost_func
            )
            print(algs)
            print(infos)


if __name__ == '__main__':
    main()
