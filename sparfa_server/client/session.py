import requests

from logging import getLogger

from sparfa_server import __client_version__

__url_cache__ = {}

__logs__ = getLogger(__package__)


class BiglearnSession(requests.Session):
    __attrs__ = requests.Session.__attrs__ + ['base_urls']

    def __init__(self):
        super().__init__()
        self.headers.update({
            # Always send JSON
            'Content-Type': 'application/json',
            # Set our own User-Agent string
            'User-Agent': 'Biglearn-API Python API client {0}'.format(
                __client_version__)
        })

        self.base_urls = dict(
            api='https://biglearn-dev.openstax.org',
            scheduler='https://biglearnworker-dev.openstax.org'
        )

    def token_auth(self, api_token, sched_token):

        if api_token and sched_token:

            self.headers.update({
                'Biglearn-Api-Token': api_token,
                'Biglearn-Scheduler-Token': sched_token
            })
        else:
            return

    def build_url(self, server='api', *args, **kwargs):
        """Builds the url based on if using the Biglearn Api or Scheduler"""
        parts = [kwargs.get('base_url') or self.base_urls.get(server)]
        parts.extend(args)
        parts = [str(p) for p in parts]
        key = tuple(parts)
        __logs__.info('Building a url from {}'.format(key))
        if key not in __url_cache__:
            __logs__.info('Missed the cache building the url')
            __url_cache__[key] = '/'.join(parts)
        return __url_cache__[key]

    def request(self, *args, **kwargs):
        response = super(BiglearnSession, self).request(*args, **kwargs)
        return response
