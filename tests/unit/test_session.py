from sparfa_server.client import session
from sparfa_server import __client_version__


class TestClientSession:
    def build_session(self, base_url=None):
        s = session.BiglearnSession()
        if base_url:
            s.base_url = base_url
        return s

    def test_has_default_headers(self):
        """Assert the default headers are there upon initialization"""
        s = self.build_session()

        assert 'Content-Type' in s.headers
        assert s.headers['Content-Type'] == 'application/json'
        assert 'User-Agent' in s.headers
        assert s.headers[
                   'User-Agent'] == 'Biglearn-API Python API client {0}'.format(
            __client_version__
        )

    def test_build_url(self):
        s = self.build_session()
        url = s.build_url('api', 'fetch_ecosystem_metadatas')
        assert url == 'https://biglearn-api-dev.openstax.org/fetch_ecosystem_metadatas'

    def test_build_url_caches_built_urls(self):
        """Test that building a URL caches it"""
        s = self.build_session()
        url = s.build_url('api', 'fetch_ecosystem_metadatas')
        url_parts = ('https://biglearn-api-dev.openstax.org', 'fetch_ecosystem_metadatas')
        assert url_parts in session.__url_cache__
        assert url in session.__url_cache__.values()

    def test_build_url_uses_a_different_base(self):
        """Test that you can pass in a different base URL to build_url"""
        s = self.build_session()
        url = s.build_url('api','fetch_matrix_calcs', base_url='https://status.openstax.org')
        assert url == 'https://status.openstax.org/fetch_matrix_calcs'

    def test_build_url_defaults_to_api(self):
        s = self.build_session()
        url = s.build_url()
        assert url == 'https://biglearn-api-dev.openstax.org'
