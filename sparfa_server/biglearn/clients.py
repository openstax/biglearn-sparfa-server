from logging import getLogger
from requests import Session

from .. import __version__
from ..config import (BIGLEARN_API_TOKEN,
                      BIGLEARN_API_URL,
                      BIGLEARN_SCHED_ALGORITHM_NAME,
                      BIGLEARN_SCHED_TOKEN,
                      BIGLEARN_SCHED_URL)
from .exceptions import raise_if_response_is_http_error

__all__ = ('BiglearnApi', 'BiglearnScheduler', 'BLAPI', 'BLSCHED')

LOGGER = getLogger(__name__)


class BiglearnClient(object):
    """The base object for all objects that require a session.

    The :class:`BiglearnClient <BiglearnClient>` object provides some useful
    attributes and methods to Biglearn client classes.
    """

    def __init__(self, base_url):
        self._base_url = str(base_url)
        self.session = Session()
        self.session.headers.update({
            # Always send and receive JSON
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def request(self, method, endpoint, **kwargs):
        """Sends a request to another Biglearn server"""
        url = '/'.join([self._base_url, str(endpoint)])

        LOGGER.debug('%s %s with %s', method, url, kwargs)
        request_method = getattr(self.session, method)
        response = request_method(url, **kwargs)

        raise_if_response_is_http_error(response)

        return response.json()

    def post(self, endpoint, **kwargs):
        """Sends a post request to another Biglearn server"""
        return self.request('post', endpoint, **kwargs)


class BiglearnApi(BiglearnClient):
    """Communicates with the biglearn-api server."""

    def __init__(self, token=BIGLEARN_API_TOKEN):
        super().__init__(base_url=BIGLEARN_API_URL)

        self.session.headers.update({
            'Biglearn-Api-Token': token,
            'User-Agent': 'Biglearn-API Python API client {}'.format(__version__),
        })

    def fetch_ecosystem_metadatas(self, metadata_sequence_number_offset, max_num_metadatas=1000):
        return self.post('fetch_ecosystem_metadatas', json={
            'metadata_sequence_number_offset': metadata_sequence_number_offset,
            'max_num_metadatas': max_num_metadatas
        })['ecosystem_responses']

    def fetch_ecosystem_events(self, ecosystem_event_requests, max_num_events=1000):
        return self.post('fetch_ecosystem_events', json={
            'ecosystem_event_requests': ecosystem_event_requests,
            'max_num_events': max_num_events
        })['ecosystem_event_responses']

    def fetch_course_metadatas(self, metadata_sequence_number_offset, max_num_metadatas=1000):
        return self.post('fetch_course_metadatas', json={
            'metadata_sequence_number_offset': metadata_sequence_number_offset,
            'max_num_metadatas': max_num_metadatas
        })['course_responses']

    def fetch_course_events(self, course_event_requests, max_num_events=1000):
        return self.post('fetch_course_events', json={
            'course_event_requests': course_event_requests,
            'max_num_events': max_num_events
        })['course_event_responses']


class BiglearnScheduler(BiglearnClient):
    """Communicates with the biglearn-scheduler server."""

    def __init__(self, token=BIGLEARN_SCHED_TOKEN, algorithm_name=BIGLEARN_SCHED_ALGORITHM_NAME):
        super().__init__(base_url=BIGLEARN_SCHED_URL)

        self.session.headers.update({
            'Biglearn-Scheduler-Token': token,
            'User-Agent': 'Biglearn-Scheduler Python API client {}'.format(__version__),
        })
        self._algorithm_name_dict = {'algorithm_name': algorithm_name}

    def _update_with_algorithm_name(self, requests):
        for request in requests:
            request.update(self._algorithm_name_dict)

    def fetch_ecosystem_matrix_updates(self):
        return self.post(
            'fetch_ecosystem_matrix_updates', json=self._algorithm_name_dict
        )['ecosystem_matrix_updates']

    def ecosystem_matrices_updated(self, ecosystem_matrix_requests):
        self._update_with_algorithm_name(ecosystem_matrix_requests)

        return self.post(
            'ecosystem_matrices_updated',
            json={'ecosystem_matrices_updated': ecosystem_matrix_requests}
        )['ecosystem_matrix_updated_responses']

    def fetch_exercise_calculations(self):
        return self.post(
            'fetch_exercise_calculations', json=self._algorithm_name_dict
        )['exercise_calculations']

    def update_exercise_calculations(self, exercise_calculation_requests):
        self._update_with_algorithm_name(exercise_calculation_requests)

        return self.post(
            'update_exercise_calculations',
            json={'exercise_calculation_updates': exercise_calculation_requests}
        )['exercise_calculation_update_responses']

    def fetch_clue_calculations(self):
        return self.post(
            'fetch_clue_calculations', json=self._algorithm_name_dict
        )['clue_calculations']

    def update_clue_calculations(self, clue_calculation_requests):
        self._update_with_algorithm_name(clue_calculation_requests)

        return self.post(
            'update_clue_calculations', json={'clue_calculation_updates': clue_calculation_requests}
        )['clue_calculation_update_responses']


BLAPI = BiglearnApi()
BLSCHED = BiglearnScheduler()
