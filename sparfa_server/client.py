import json
import os

import requests
from requests import RequestException

from sparfa_server.exceptions import RequestError

__version__ = 'v1'

API_URL = 'https://biglearn-dev.openstax.org'
HTTP_USER_AGENT = 'Biglearn-API Python API client {0}'.format(__version__)


class BaseClient(object):
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


class BiglearnAPI(object):
    """
    The main class used to encapsulate the Biglearn API and Biglearn Scheduler
    Scheduler tasks.
    """

    def __init__(self):
        # Favoring composition over inheritance.
        # This also allows monkeypatching for testing.
        self.client = BaseClient()

    def _create_ecosystem_event_request(self, ecosystem_uuid):
        data = {
            'ecosystem_event_requests': [],
        }

        event_request = {
            'request_uuid': str(uuid.uuid4()),
            'event_types': ['create_ecosystem'],
            'ecosystem_uuid': ecosystem_uuid,
            'sequence_number_offset': 0,
            'max_num_events': 10,
        }

        data['ecosystem_event_requests'].append(event_request)

        return data

    def fetch_ecosystem_metadatas(self):
        ecosystem_metadas = self.client.post('/fetch_ecosystem_metadatas')
        return ecosystem_metadas

    def fetch_ecosystem_events(self, ecosystem_uuid):
        event_request = self._create_ecosystem_event_request(ecosystem_uuid)
        ecosystem_events = self.client.post('/fetch_ecosystem_events',
                                            **event_request)
        return ecosystem_events

    def fetch_course_metadatas(self):
        course_metadatas = self.client.post('/fetch_course_metadatas')
        return course_metadatas
