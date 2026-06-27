from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

experiences_bp = Blueprint('experiences', __name__, url_prefix='/api/experiences')


@experiences_bp.route('', methods=['GET'])
def get_experiences():
    from app.models.experience import Experience
    filters = {'q': request.args.get('q', '')}
    experiences = Experience.search(filters)
    return jsonify({'experiences': experiences, 'total': len(experiences)}), 200


@experiences_bp.route('/<exp_id>', methods=['GET'])
def get_experience(exp_id):
    from app.models.experience import Experience
    exp = Experience.get_by_id(exp_id)
    if not exp:
        return jsonify({'error': 'Experience not found'}), 404
    return jsonify(exp), 200


@experiences_bp.route('', methods=['POST'])
@login_required
def create_experience():
    from app.models.experience import Experience
    data = request.get_json() or {}
    if not data.get('title') or not data.get('price'):
        return jsonify({'error': 'title and price are required'}), 400
    exp_id = Experience.create(session['user_id'], data)
    if not exp_id:
        return jsonify({'error': 'Failed to create experience'}), 500
    return jsonify({'id': exp_id, 'message': 'Experience created'}), 201


@experiences_bp.route('/<exp_id>', methods=['PUT'])
@login_required
def update_experience(exp_id):
    from app.models.experience import Experience
    exp = Experience.get_by_id(exp_id)
    if not exp:
        return jsonify({'error': 'Experience not found'}), 404
    if exp.get('hostId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    data = request.get_json() or {}
    Experience.update(exp_id, data)
    return jsonify({'ok': True}), 200


@experiences_bp.route('/<exp_id>', methods=['DELETE'])
@login_required
def delete_experience(exp_id):
    from app.models.experience import Experience
    exp = Experience.get_by_id(exp_id)
    if not exp:
        return jsonify({'error': 'Experience not found'}), 404
    if exp.get('hostId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Experience.delete(exp_id)
    return jsonify({'ok': True}), 200


@experiences_bp.route('/host/mine', methods=['GET'])
@login_required
def my_experiences():
    from app.models.experience import Experience
    experiences = Experience.get_by_host(session['user_id'])
    return jsonify({'experiences': experiences}), 200
