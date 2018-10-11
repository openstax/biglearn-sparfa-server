from uuid import uuid4

from .cli.loaders import load_ecosystem


class TestAddCommand(object):
    def test_import_ecoystem_prints_error_message(self, cli):
        result = self._import_ecosystem(cli, self._gen_incorrect_ecosystem_uuid())
        print(result.output)
        assert 'invalid ecosystem' in result.output

    @staticmethod
    def _gen_incorrect_ecosystem_uuid():
        return 'l;akdja;lksd343434'

    @staticmethod
    def _gen_correct_ecosystem_uuid():
        return uuid4()

    def _import_ecosystem(self, cli, ecosystem_uuid):
        result = cli.invoke(load_ecosystem, [u'--ecosystem_uuid', ecosystem_uuid])
        assert result.exit_code == 0
        return result
