from fastjsonschema import compile
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import Unauthorized
from scipy.sparse import coo_matrix

from .config import BIGLEARN_SPARFA_TOKEN
from .orm import transaction, EcosystemMatrix, Response

FETCH_ECOSYSTEM_MATRICES_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'properties': {
        'ecosystem_matrix_requests': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'request_uuid': {'$ref': '#/uuid'},
                    'ecosystem_matrix_uuid': {'$ref': '#/uuid'},
                    'student_uuids': {
                        'type': 'array',
                        'items': {'$ref': '#/uuid'},
                        'maxItems': 1000
                    },
                    'responded_before': {'$ref': '#/datetime'}
                },
                'required': ['request_uuid', 'ecosystem_matrix_uuid'],
                'additionalProperties': False
            },
            'maxItems': 10
        }
    },
    'required': ['ecosystem_matrix_requests'],
    'additionalProperties': False,
    'uuid': {
        'type': 'string',
        'pattern': '^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-' +
                   '[04][a-fA-F0-9]{3}-[a-fA-F0-9]{4}-' +
                   '[a-fA-F0-9]{12}$',
    },
    'datetime': {
        'type': 'string',
        'pattern': '^\\d{4}-' +                       # year
                   '(0[1-9]|1[0-2])-' +               # month
                   '(0[1-9]|1[0-9]|2[0-9]|3[0-1])' +  # day of month
                   '(T|t)' +                          # ISO8601 spacer
                   '(0[0-9]|1[0-9]|2[0-3]):' +        # hour
                   '([0-5][0-9]):' +                  # minute
                   '([0-5][0-9]|60)' +                # second
                   '(\\.\\d{1,6})?' +                 # fraction of second
                   '(Z|z)$'                           # Zulu timezone
    }
}

FETCH_ECOSYSTEM_MATRICES_VALIDATOR = compile(FETCH_ECOSYSTEM_MATRICES_SCHEMA)

blueprint = Blueprint('API', __name__)


@blueprint.route('/fetch_ecosystem_matrices', methods=['POST'])
def show():
    if 'Biglearn-Sparfa-Token' not in request.headers:
        raise Unauthorized('Request missing the Biglearn-Sparfa-Token header')

    if request.headers['Biglearn-Sparfa-Token'] != BIGLEARN_SPARFA_TOKEN:
        raise Unauthorized('Invalid Biglearn-Sparfa-Token header')

    request_data = request.get_json(force=True)

    FETCH_ECOSYSTEM_MATRICES_VALIDATOR(request_data)

    ecosystem_matrix_requests = request_data['ecosystem_matrix_requests']

    ecosystem_matrix_uuids = []
    student_uuids_by_request_uuid = {}
    responded_before_by_request_uuid = {}
    for em_request in ecosystem_matrix_requests:
        ecosystem_matrix_uuids.append(em_request['ecosystem_matrix_uuid'])
        request_uuid = em_request['request_uuid']
        student_uuids_by_request_uuid[request_uuid] = em_request.get('student_uuids')
        responded_before_by_request_uuid[request_uuid] = em_request.get('responded_before')

    with transaction() as session:
        ecosystem_matrices_by_uuid = {
            ecosystem_matrix.uuid: ecosystem_matrix
            for ecosystem_matrix in session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(ecosystem_matrix_uuids)
            ).all()
        }

        ecosystem_matrix_responses = []
        for ecosystem_matrix_request in ecosystem_matrix_requests:
            request_uuid = ecosystem_matrix_request['request_uuid']
            ecosystem_matrix_uuid = ecosystem_matrix_request['ecosystem_matrix_uuid']
            student_uuids = student_uuids_by_request_uuid[request_uuid]
            ecosystem_matrix_response = {
                'request_uuid': request_uuid,
                'ecosystem_matrix_uuid': ecosystem_matrix_uuid,
                'responded_before': ecosystem_matrix_request.get('responded_before'),
                'ecosystem_uuid': None,
                'L_ids': [] if student_uuids is None else student_uuids,
                'Q_ids': [],
                'C_ids': [],
                'd_data': [],
                'W_data': [],
                'W_row': [],
                'W_col': [],
                'H_mask_data': [],
                'H_mask_row': [],
                'H_mask_col': [],
                'G_data': [],
                'G_row': [],
                'G_col': [],
                'G_mask_data': [],
                'G_mask_row': [],
                'G_mask_col': [],
                'U_data': [],
                'U_row': [],
                'U_col': [],
                'superseded_at': None
            }

            ecosystem_matrix = ecosystem_matrices_by_uuid.get(ecosystem_matrix_uuid)
            if ecosystem_matrix:
                ecosystem_matrix_response.update({
                    key: value.isoformat() + 'Z' if hasattr(value, 'isoformat') else value
                    for (key, value) in ecosystem_matrix.dict.items()
                    if key != 'uuid' and key != 'is_used_in_assignments'
                })

                if student_uuids != [] and ecosystem_matrix.Q_ids and ecosystem_matrix.C_ids:
                    responded_before = responded_before_by_request_uuid[request_uuid]
                    query = session.query(Response).filter(
                        Response.ecosystem_uuid == ecosystem_matrix.ecosystem_uuid
                    )
                    if student_uuids is not None:
                        query = query.filter(Response.student_uuid.in_(student_uuids))
                    if responded_before is not None:
                        query = query.filter(Response.responded_at < responded_before)
                    responses = query.all()

                    if responses:
                        if student_uuids is None:
                            student_uuids = [response.student_uuid for response in responses]
                            ecosystem_matrix_response['L_ids'] = student_uuids

                        algs = ecosystem_matrix.to_sparfa_algs_with_student_uuids_responses(
                            student_uuids=student_uuids, responses=responses
                        )

                        G = coo_matrix(algs.G_NQxNL)
                        ecosystem_matrix_response['G_data'] = G.data.tolist()
                        ecosystem_matrix_response['G_row'] = G.row.tolist()
                        ecosystem_matrix_response['G_col'] = G.col.tolist()

                        G_mask = coo_matrix(algs.G_mask_NQxNL)
                        ecosystem_matrix_response['G_mask_data'] = G_mask.data.tolist()
                        ecosystem_matrix_response['G_mask_row'] = G_mask.row.tolist()
                        ecosystem_matrix_response['G_mask_col'] = G_mask.col.tolist()

                        U = coo_matrix(algs.U_NCxNL)
                        ecosystem_matrix_response['U_data'] = U.data.tolist()
                        ecosystem_matrix_response['U_row'] = U.row.tolist()
                        ecosystem_matrix_response['U_col'] = U.col.tolist()

            ecosystem_matrix_responses.append(ecosystem_matrix_response)

    return jsonify({'ecosystem_matrices': [{
        key if key != 'uuid' else 'ecosystem_matrix_uuid':
            value.isoformat() + 'Z' if hasattr(value, 'isoformat') else value
        for (key, value) in ecosystem_matrix_response.items()
        if key != 'is_used_in_assignments'
    } for ecosystem_matrix_response in ecosystem_matrix_responses]})
