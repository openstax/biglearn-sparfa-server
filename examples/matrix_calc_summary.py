import logging

from sparfa_server import api
from sparfa_server.api import update_matrix_calculations
from sparfa_server.calcs import calc_ecosystem_matrices


logging.basicConfig(level=logging.DEBUG)

__logs__ = logging.getLogger(__name__)


def main():
    alg_name = 'mikea'
    calcs = api.fetch_matrix_calculations(alg_name)

    if calcs:
        __logs__.info('Processing {} matrix calcs'.format(len(calcs)))
        for calc in calcs:
            calc_ecosystem_matrices(calc['ecosystem_uuid'])

            update_matrix_calculations(alg_name, calc)


if __name__ == '__main__':
    main()
