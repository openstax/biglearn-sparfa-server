from logging import getLogger
from json import dumps
from requests import Session

from .about import __version__
from .exceptions import check_status_code
from .config import (BIGLEARN_API_TOKEN,
                     BIGLEARN_API_URL,
                     BIGLEARN_SCHED_ALGORITHM_NAME,
                     BIGLEARN_SCHED_TOKEN,
                     BIGLEARN_SCHED_URL)

__logs__ = getLogger(__name__)

class BiglearnClient(object):
    """The base object for all objects that require a session.

    The :class:`BiglearnClient <BiglearnClient>` object provides some useful
    attributes and methods to Biglearn client classes.
    """

    def __init__(self, base_url, session=None):
        if session is None:
            session = Session()
        elif hasattr(session, 'session'):
            session = session.session()

        session.headers.update({
            # Always send and receive JSON
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        self._base_url = str(base_url)
        self.session = session

    def _url_for(self, api_endpoint):
        """Builds an API url based on the base_url setting and the given endpoint"""
        return '/'.join([self._base_url, str(api_endpoint)])

    def _request(self, method, api_endpoint, data_dict=None, **kwargs):
        """Sends a request to another Biglearn server"""
        url = self._url_for(api_endpoint)
        data = None if data_dict is None else dumps(data_dict)

        __logs__.debug('%s %s with %s, %s', method, url, data, kwargs)
        request_method = getattr(self.session, method)
        response = request_method(url, data, **kwargs)

        check_status_code(response)

        return response.json()

    def post(self, api_endpoint, data_dict=None, **kwargs):
        """Sends a post request to another Biglearn server"""
        return self._request('post', api_endpoint, data_dict=data_dict, **kwargs)


class BiglearnApi(BiglearnClient):
    """Communicates with the biglearn-api server."""

    def __init__(self, token=BIGLEARN_API_TOKEN, session=None):
        super().__init__(base_url=BIGLEARN_API_URL, session=session)

        self.session.headers.update({
            'Biglearn-Api-Token': token,
            'User-Agent': 'Biglearn-API Python API client {}'.format(__version__),
        })

    def fetch_ecosystem_metadatas(self):
        return self.post('fetch_ecosystem_metadatas')['ecosystem_responses']

    def fetch_ecosystem_events(self, ecosystem_event_requests, max_num_events=1000):
        return self.post('fetch_ecosystem_events', {
            'ecosystem_event_requests': ecosystem_event_requests,
            'max_num_events': max_num_events
        })['ecosystem_event_responses']

    def fetch_course_metadatas(self):
        return self.post('fetch_course_metadatas')['course_responses']

    def fetch_course_events(self, course_event_requests, max_num_events=1000):
        return self.post('fetch_course_events', {
            'course_event_requests': course_event_requests,
            'max_num_events': max_num_events
        })['course_event_responses']


class BiglearnScheduler(BiglearnClient):
    """Communicates with the biglearn-scheduler server."""

    def __init__(self,
                 token=BIGLEARN_SCHED_TOKEN,
                 session=None,
                 algorithm_name=BIGLEARN_SCHED_ALGORITHM_NAME):
        super().__init__(base_url=BIGLEARN_SCHED_URL, session=session)

        self.session.headers.update({
            'Biglearn-Scheduler-Token': token,
            'User-Agent': 'Biglearn-Scheduler Python API client {}'.format(__version__),
        })
        self._algorithm_name_dict = {'algorithm_name': algorithm_name}

    def fetch_ecosystem_matrix_updates(self):
        return self.post(
            'fetch_ecosystem_matrix_updates', self._algorithm_name_dict
        )['ecosystem_matrix_updates']

    def ecosystem_matrices_updated(self, ecosystem_matrix_requests):
        for request in ecosystem_matrix_requests:
            request.update(self._algorithm_name_dict)

        return self.post(
            'ecosystem_matrices_updated', {'ecosystem_matrices_updated': ecosystem_matrix_requests}
        )['ecosystem_matrix_updated_responses']

    def fetch_exercise_calculations(self):
        return self.post(
            'fetch_exercise_calculations', self._algorithm_name_dict
        )['exercise_calculations']

    def update_exercise_calculations(self, exercise_calculation_requests):
        for request in exercise_calculation_requests:
            request.update(self._algorithm_name_dict)

        return self.post(
            'update_exercise_calculations',
            {'exercise_calculation_updates': exercise_calculation_requests}
        )['exercise_calculation_update_responses']

    def fetch_clue_calculations(self):
        return self.post(
            'fetch_clue_calculations', self._algorithm_name_dict
        )['clue_calculations']

    def update_clue_calculations(self, clue_calculation_requests):
        for request in clue_calculation_requests:
            request.update(self._algorithm_name_dict)

        return self.post(
            'update_clue_calculations', {'clue_calculation_updates': clue_calculation_requests}
        )['clue_calculation_update_responses']

blapi = BiglearnApi()
blsched = BiglearnScheduler()
