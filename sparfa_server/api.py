from flask import Blueprint, render_template

from .orm import transaction, EcosystemMatrix

blueprint = Blueprint('API', __name__, template_folder='templates')

@blueprint.route('/fetch_ecosystem_matrices', methods=['POST'])
def show():
    with transaction() as session:
        ecosystem_matrices = session.query(EcosystemMatrix).all()
        ecosystem_matrix_dicts = [{
            key: value
            for (key, value) in ecosystem_matrix.dict.items()
            if key != 'is_used_in_assignments'
        } for ecosystem_matrix in ecosystem_matrices]

    return render_template('fetch_ecosystem_matrices.json',
                           ecosystem_matrices=ecosystem_matrix_dicts)
