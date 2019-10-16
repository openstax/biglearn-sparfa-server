from werkzeug.exceptions import Unauthorized, BadRequest
from flask import Blueprint, request, jsonify

from .config import BIGLEARN_SPARFA_TOKEN
from .orm import transaction, EcosystemMatrix


blueprint = Blueprint('API', __name__)


@blueprint.route('/fetch_ecosystem_matrices', methods=['POST'])
def show():
    if 'Biglearn-Sparfa-Token' not in request.headers:
        raise Unauthorized('Request missing the Biglearn-Sparfa-Token header')

    if request.headers['Biglearn-Sparfa-Token'] != BIGLEARN_SPARFA_TOKEN:
        raise Unauthorized('Invalid Biglearn-Sparfa-Token header')

    request_data = request.get_json(force=True)
    if 'ecosystem_matrix_uuids' not in request_data:
        raise BadRequest('Request data missing the ecosystem_matrix_uuids key')

    ecosystem_matrix_uuids = request_data['ecosystem_matrix_uuids']
    if not ecosystem_matrix_uuids:
        return jsonify({'ecosystem_matrices': []})

    if len(ecosystem_matrix_uuids) > 10:
        raise BadRequest('The number of ecosystem_matrix_uuids is limited to 10 per request')

    with transaction() as session:
        ecosystem_matrix_dicts = [
            ecosystem_matrix.dict for ecosystem_matrix in session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(ecosystem_matrix_uuids)
            ).all()
        ]

    return jsonify({'ecosystem_matrices': [{
        key if key != 'uuid' else 'ecosystem_matrix_uuid':
            value if not hasattr(value, 'isoformat') else value.isoformat()
        for (key, value) in ecosystem_matrix_dict.items()
        if key != 'is_used_in_assignments'
    } for ecosystem_matrix_dict in ecosystem_matrix_dicts]})
