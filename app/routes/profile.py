from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')


@profile_bp.route('', methods=['GET'])
@login_required
def get_profile():
    from app.models.user import User
    user = User.get_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.pop('password', None)
    return jsonify(user), 200


@profile_bp.route('', methods=['PUT'])
@login_required
def update_profile():
    from app.models.user import User
    data = request.get_json() or {}
    allowed = {'name', 'phone', 'bio', 'profile_image', 'role'}
    update_data = {k: v for k, v in data.items() if k in allowed}
    if not update_data:
        return jsonify({'error': 'No valid fields to update'}), 400
    User.update(session['user_id'], update_data)
    if 'name' in update_data:
        session['name'] = update_data['name']
    if 'role' in update_data:
        session['role'] = update_data['role']
    return jsonify({'ok': True}), 200


@profile_bp.route('/photo', methods=['POST'])
@login_required
def upload_photo():
    from app.services.storage_service import StorageService
    from app.models.user import User
    file = request.files.get('photo')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    url = StorageService.upload(file, folder=f'profiles/{session["user_id"]}')
    if not url:
        return jsonify({'error': 'Upload failed — check storage configuration'}), 500
    User.update(session['user_id'], {'profile_image': url})
    return jsonify({'url': url}), 200
