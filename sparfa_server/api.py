from fastjsonschema import compile
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import Unauthorized, BadRequest

from .config import BIGLEARN_SPARFA_TOKEN
from .orm import transaction, EcosystemMatrix

FETCH_ECOSYSTEM_MATRICES_SCHEMA = {
  '$schema': 'http://json-schema.org/draft-04/schema#',
  'type': 'object',
  'properties': {
      'ecosystem_matrix_requests': {
          'type': 'array',
          'items': {
              'type': 'object',
              'properties': {
                  'ecosystem_matrix_uuid': {'$ref': '#/uuid'},
                  'student_uuids': {
                      'type': 'array',
                      'items': {'$ref': '#/uuid'},
                      'maxItems': 1000
                  }
              },
              'required': ['ecosystem_matrix_uuid', 'student_uuids'],
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

    student_uuids_by_ecosystem_matrix_uuid = {req['ecosystem_matrix_uuid']: req['student_uuids']
                                              for req in request_data['ecosystem_matrix_requests']}

    with transaction() as session:
        ecosystem_matrix_dicts = [
            ecosystem_matrix.dict for ecosystem_matrix in session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(student_uuids_by_ecosystem_matrix_uuid.keys())
            ).all()
        ]

    return jsonify({'ecosystem_matrices': [{
        key if key != 'uuid' else 'ecosystem_matrix_uuid':
            value if not hasattr(value, 'isoformat') else value.isoformat()
        for (key, value) in ecosystem_matrix_dict.items()
        if key != 'is_used_in_assignments'
    } for ecosystem_matrix_dict in ecosystem_matrix_dicts]})
