from flask import Blueprint, request, render_template
from werkzeug.exceptions import BadRequest

from .config import BIGLEARN_SPARFA_TOKEN
from .orm import transaction, EcosystemMatrix


# https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/
class ApiException(Exception):
    status_code = 400
    payload = {}

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        if status_code is not None:
            self.status_code = status_code
        if payload is not None:
            self.payload = payload
        self.payload['errors'] = [message]


api_blueprint = Blueprint('API', __name__, template_folder='templates')


@api_blueprint.route('/fetch_ecosystem_matrices', methods=['POST'])
def show():
    if 'Biglearn-Sparfa-Token' not in request.headers:
        raise ApiException('Request missing the Biglearn-Sparfa-Token header')

    if request.headers['Biglearn-Sparfa-Token'] != BIGLEARN_SPARFA_TOKEN:
        raise ApiException('Invalid Biglearn-Sparfa-Token header')

    request_data = request.get_json(force=True)
    if 'ecosystem_matrix_uuids' not in request_data:
        raise ApiException('Request data missing the ecosystem_matrix_uuids key')

    ecosystem_matrix_uuids = request_data['ecosystem_matrix_uuids']
    if not ecosystem_matrix_uuids:
        return render_template(
                   'fetch_ecosystem_matrices.json', ecosystem_matrices=[]
               ), {'Content-Type': 'application/json'}

    if len(ecosystem_matrix_uuids) > 10:
        raise ApiException('The number of ecosystem_matrix_uuids is limited to 10 per request')

    with transaction() as session:
        ecosystem_matrices_attributes = [{
            key if key != 'uuid' else 'ecosystem_matrix_uuid':
                value if not hasattr(value, 'isoformat') else value.isoformat()
            for (key, value) in ecosystem_matrix.dict.items()
            if key != 'is_used_in_assignments'
        } for ecosystem_matrix in session.query(EcosystemMatrix).filter(
            EcosystemMatrix.uuid.in_(ecosystem_matrix_uuids)
        ).all()]

    return render_template(
               'fetch_ecosystem_matrices.json', ecosystem_matrices=ecosystem_matrices_attributes
           ), {'Content-Type': 'application/json'}
