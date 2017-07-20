import uuid

from sparfa_server.cli.commands import loaders as loaders_cli


class TestAddCommand(object):
    def test_it_prints_error_message(self, cli):
        result = self._import_ecosystem(cli, self._gen_incorrect_ecosystem_uuid())
        print(result.output)
        assert 'invalid Ecosystem' in result.output

    @staticmethod
    def _gen_incorrect_ecosystem_uuid():
        return 'l;akdja;lksd343434'

    @staticmethod
    def _gen_correct_ecosystem_uuid():
        return uuid.uuid4()

    def _import_ecosystem(self, cli, ecosystem_uuid):
        result = cli.invoke(loaders_cli.load_ecosystem,
                            [u'--ecosystem_uuid', ecosystem_uuid])
        assert result.exit_code == 0
        return result
