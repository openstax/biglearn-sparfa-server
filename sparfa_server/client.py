import json
import os

import requests
from requests import RequestException

from sparfa_server.exceptions import RequestError

__version__ = 'v1'

API_URL = 'https://biglearn-dev.openstax.org'
HTTP_USER_AGENT = 'Biglearn-API Python API client {0}'.format(__version__)


class Client(object):
    """Base API client"""

    def __init__(self, url=None, version=__version__):
        self.url = url or os.environ.get('BIGLEARN_API_URL') or API_URL
        self.version = version

    def _do_request(self, request, url, **kwargs):
        try:
            response = request(url, **kwargs)
        except RequestException as e:
            raise RequestError(e)
        else:
            if response.status_code >= 400:
                raise RequestError('Bad request')

        try:
            return response.json()
        except (TypeError, ValueError):
            return response.text

    def _request(self, method, endpoint, id=None, **kwargs):
        request = getattr(requests, method, None)
        if not callable(request):
            raise RequestError('Invalid method %s' % method)

        data = kwargs.get('data', {})
        headers = {'Content-Type': 'application/json',
                   'User-Agent': HTTP_USER_AGENT}

        url = self.url + endpoint

        kwargs.setdefault('headers', headers)

        if data:
            kwargs['data']=json.dumps(data)

        return self._do_request(request, url, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def get(self, endpoint, id=None, **kwargs):
        return self._request('get', endpoint, id=id, params=kwargs)

    def put(self, endpoint, id=None, **kwargs):
        return self._request('put', endpoint, id=id, data=kwargs)

    def post(self, endpoint, id=None, **kwargs):
        return self._request('post', endpoint, id=id, data=kwargs)

    def delete(self, endpoint, id=None, **kwargs):
        return self._request('delete', endpoint, id=id, data=kwargs)
