from json import dumps
from logging import getLogger

import requests

from sparfa_server import exceptions
from sparfa_server.client.session import BiglearnSession

__logs__ = getLogger(__package__)


class ClientCore(object):
    """The base object for all objects that require a session.

    The :class:`ClientCore <ClientCore>` object provides some basic
    attributes and methods to other sub-classes that are useful.
    """

    def __init__(self, json, session=None):
        if hasattr(session, 'session'):
            session = session.session
        elif session is None:
            session = BiglearnSession()
        self.session = session

    def _json(self, response, status_code):
        ret = None
        if self._boolean(response, status_code, 404) and response.content:
            __logs__.info('Attempting to get JSON information from a '
                          'Response with status code %d expecting %d',
                          response.status_code, status_code)
            ret = response.json()
        __logs__.info('JSON was %sreturned', 'not ' if ret is None else '')
        return ret

    def _boolean(self, response, true_code, false_code):
        if response is not None:
            status_code = response.status_code
            if status_code == true_code:
                return True
            if status_code == false_code:
                raise exceptions.error_for(response)
        return False

    def _request(self, method, *args, **kwargs):
        try:
            request_method = getattr(self.session, method)
            return request_method(*args, **kwargs)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as exc:
            raise exceptions.ConnectionError(exc)
        except requests.exceptions.RequestException as exc:
            raise exceptions.TransportError(exc)

    def _post(self, url, data=None, json=True, **kwargs):
        if json:
            data = dumps(data) if data is not None else data
        __logs__.debug('POST %s with %s, %s', url, data, kwargs)
        return self._request('post', url, data, **kwargs)

    def _build_url(self, *args, **kwargs):
        """Builds a new API url from scratch."""
        return self.session.build_url(*args, **kwargs)

    def fetch(self, url, **kwargs):
        response = self._post(url, **kwargs)
        return response


class BiglearnApi(ClientCore):
    """Stores all the session information."""

    def __init__(self):
        super().__init__({})

    def fetch_ecosystem_metadatas(self):
        url = self._build_url('api', 'fetch_ecosystem_metadatas')
        json = self._json(self.fetch(url), 200)
        return json

    def fetch_course_metadatas(self):
        url = self._build_url('api', 'fetch_course_metadatas')
        json = self._json(self.fetch(url), 200)
        return json

    def fetch_ecosystem_event_requests(self, event_request):
        url = self._build_url('api', 'fetch_ecosystem_events')
        json = self._json(self.fetch(url, data=event_request), 200)
        return json

    def fetch_course_event_requests(self, event_request):
        url = self._build_url('api', 'fetch_course_events')
        json = self._json(self.fetch(url, data=event_request), 200)
        return json

    def fetch_matrix_calcs(self, request):
        url = self._build_url('scheduler', 'fetch_ecosystem_matrix_updates')
        json = self._json(self.fetch(url, data=request), 200)
        return json

    def update_matrix_calcs(self, request):
        url = self._build_url('scheduler', 'ecosystem_matrices_updated')
        json = self._json(self.fetch(url, data=request), 200)
        return json

    def fetch_exercise_calcs(self, request):
        url = self._build_url('scheduler', 'fetch_exercise_calculations')
        json = self._json(self.fetch(url, data=request), 200)
        return json




