from logging import getLogger
from uuid import uuid4
from json import dumps
from requests import Session

from . import __version__
from exceptions import check_status_code

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

        self._base_url = '/'.join([str(base_url), 'api'])
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

    def __init__(self, token, session=None):
        super().__init__(base_url=BIGLEARN_API_URL, session=session)

        self.session.headers.update({
            'Biglearn-Api-Token': token,
            'User-Agent': 'Biglearn-API Python API client {0}'.format(__version__),
        })

    def fetch_ecosystem_metadatas(self):
        return self.post('fetch_ecosystem_metadatas')

    def fetch_ecosystem_events(self, ecosystem_event_requests, max_num_events=1000):
        return self.post('fetch_ecosystem_events', {
            'ecosystem_event_requests': ecosystem_event_requests,
            'max_num_events': max_num_events
        })

    def fetch_course_metadatas(self):
        return self.post('fetch_course_metadatas')

    def fetch_course_events(self, course_event_requests, max_num_events=1000):
        return self.post('fetch_course_events', {
            'course_event_requests': course_event_requests,
            'max_num_events': max_num_events
        })


class BiglearnScheduler(BiglearnClient):
    """Communicates with the biglearn-scheduler server."""

    def __init__(self, token, session=None):
        super().__init__(base_url=BIGLEARN_SCHED_URL, session=session)

        self.session.headers.update({
            'Biglearn-Scheduler-Token': token,
            'User-Agent': 'Biglearn-Scheduler Python API client {0}'.format(__version__),
        })

    def fetch_ecosystem_matrix_updates(self, request):
        url = self._build_url('scheduler', 'fetch_ecosystem_matrix_updates')
        json = self._json(self.fetch(url, data=request), 200)
        return self.post('fetch_ecosystem_matrix_updates')

    def update_matrix_calcs(self, request):
        url = self._build_url('scheduler', 'ecosystem_matrices_updated')
        json = self._json(self.fetch(url, data=request), 200)
        return json

    def fetch_exercise_calcs(self, request):
        url = self._build_url('scheduler', 'fetch_exercise_calculations')
        json = self._json(self.fetch(url, data=request), 200)
        return json

    def update_exercise_calcs(self, request):
        url = self._build_url('scheduler', 'update_exercise_calculations')
        json = self._json(self.fetch(url, data=request), 200)
        return json

    def fetch_clue_calcs(self, request):
        url = self._build_url('scheduler', 'fetch_clue_calculations')
        json = self._json(self.fetch(url, data=request), 200)
        return json

    def update_clue_calcs(self, request):
        url = self._build_url('scheduler', 'update_clue_calculations')
        json = self._json(self.fetch(url, data=request), 200)
        return json

blapi = BiglearnApi(BIGLEARN_API_TOKEN)
blsched = BiglearnScheduler(BIGLEARN_SCHED_TOKEN)


def fetch_course_uuids(course_uuids=None):
    __logs__.info('Polling courses endpoint for new courses')
    course_metadatas = blapi.fetch_course_metadatas()
    if course_uuids:
        return [uuid['uuid'] for uuid in course_metadatas['course_responses'] if
                uuid in course_uuids]

    return [uuid['uuid'] for uuid in course_metadatas['course_responses']]


def fetch_pending_courses_metadata(force=False):
    __logs__.info('Polling courses endpoint for new courses')
    course_metadatas = blapi.fetch_course_metadatas()

    db_course_uuids = session.query(Course.uuid).all()

    import_course_metadatas = list(
        filter(lambda x: x['uuid'] not in db_course_uuids,
               course_metadatas['course_responses']))

    if force:
        import_course_metadatas = course_metadatas

    return import_course_metadatas


def fetch_course_event_requests(course_uuid, offset=0, max_events=1000):
    payload = create_course_event_request(course_uuid, offset, max_events)

    course_event_reqs = blapi.fetch_course_event_requests(payload)

    course_event_resps = course_event_reqs['course_event_responses'][0]
    return course_event_resps


def fetch_pending_course_events_requests(current_course_events_data, max_events=1000):
    payload = create_course_event_requests(current_course_events_data, max_events)

    course_event_reqs = blapi.fetch_course_event_requests(payload)

    course_event_resps = course_event_reqs['course_event_responses']
    return course_event_resps


def fetch_ecosystem_uuids(ecosystem_uuids=None):
    ecosystem_metadatas = blapi.fetch_ecosystem_metadatas()
    if ecosystem_uuids:
        return [uuid['uuid'] for uuid in
                ecosystem_metadatas['ecosystem_responses'] if
                uuid in ecosystem_uuids]
    else:
        return [uuid['uuid'] for uuid in
                ecosystem_metadatas['ecosystem_responses']]


def fetch_ecosystem_event_requests(ecosystem_uuid, offset=0, max_events=1000):
    payload = create_ecosystem_event_request(ecosystem_uuid, offset, max_events)

    eco_event_reqs = blapi.fetch_ecosystem_event_requests(payload)

    eco_event_resps = eco_event_reqs['ecosystem_event_responses'][0]
    eco_data = eco_event_resps['events'][0]['event_data']

    contents_data = eco_data['book']['contents']
    exercises_data = eco_data['exercises']

    return contents_data, exercises_data


def fetch_matrix_calculations(algorithm_name):
    payload = dict(algorithm_name=algorithm_name)

    matrix_calcs_response = blapi.fetch_matrix_calcs(payload)
    matrix_calcs = matrix_calcs_response['ecosystem_matrix_updates']

    return matrix_calcs


def update_matrix_calculations(algorithm_name, calc_uuid):
    # TODO: add log message that update_matrix_calc is happening
    payload = {
        'ecosystem_matrices_updated': [
            {
                'calculation_uuid': calc_uuid,
                'algorithm_name': algorithm_name,
            },
        ],
    }

    response = blapi.update_matrix_calcs(payload)
    return response


def fetch_pending_ecosystems(force=False):
    __logs__.info('Polling ecosystem endpoint for new ecosystems')
    api_ecosystem_uuids = fetch_ecosystem_uuids()

    db_ecosystem_uuids = session.query(Ecosystem.uuid).all()

    import_ecosystem_uuids = list(
        filter(lambda x: x not in db_ecosystem_uuids,
               api_ecosystem_uuids))

    if force:
        import_ecosystem_uuids = api_ecosystem_uuids

    return import_ecosystem_uuids


def fetch_exercise_calcs(alg_name):
    # TODO: add log message that update_matrix_calc is happening
    payload = dict(
        algorithm_name=alg_name
    )

    response = blapi.fetch_exercise_calcs(payload)

    exercise_calcs = response['exercise_calculations']
    return exercise_calcs


def update_exercise_calcs(alg_name, calc_uuid, exercise_uuids):
    payload = {
        'exercise_calculation_updates': [
            {
                'calculation_uuid': calc_uuid,
                'algorithm_name': alg_name,
                'exercise_uuids': exercise_uuids
            }
        ]
    }
    response = blapi.update_exercise_calcs(payload)
    return response['exercise_calculation_update_responses'][0]


def fetch_clue_calcs(alg_name):
    payload = dict(
        algorithm_name=alg_name
    )

    response = blapi.fetch_clue_calcs(payload)

    clue_calcs = response['clue_calculations']
    return clue_calcs


def update_clue_calcs(alg_name, ecosystem_uuid, calc_uuid, clue_min,
                      clue_most_likely, clue_max, clue_is_real):
    payload = {
        'clue_calculation_updates': [
            {
                'calculation_uuid': calc_uuid,
                'algorithm_name': alg_name,
                'clue_data': {
                    'ecosystem_uuid': ecosystem_uuid,
                    'minimum': clue_min,
                    'most_likely': clue_most_likely,
                    'maximum': clue_max,
                    'is_real': clue_is_real
                }
            }
        ]
    }
    response = blapi.update_clue_calcs(payload)
    return response['clue_calculation_update_responses'][0]
