from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

services_bp = Blueprint('services', __name__, url_prefix='/api/services')


@services_bp.route('', methods=['GET'])
def get_services():
    from app.models.service import Service
    filters = {'q': request.args.get('q', '')}
    svcs = Service.search(filters)
    return jsonify({'services': svcs, 'total': len(svcs)}), 200


@services_bp.route('/<service_id>', methods=['GET'])
def get_service(service_id):
    from app.models.service import Service
    svc = Service.get_by_id(service_id)
    if not svc:
        return jsonify({'error': 'Service not found'}), 404
    return jsonify(svc), 200


@services_bp.route('', methods=['POST'])
@login_required
def create_service():
    from app.models.service import Service
    data = request.get_json() or {}
    if not data.get('title') or not data.get('price'):
        return jsonify({'error': 'title and price are required'}), 400
    svc_id = Service.create(session['user_id'], data)
    if not svc_id:
        return jsonify({'error': 'Failed to create service'}), 500
    return jsonify({'id': svc_id, 'message': 'Service created'}), 201


@services_bp.route('/<service_id>', methods=['PUT'])
@login_required
def update_service(service_id):
    from app.models.service import Service
    svc = Service.get_by_id(service_id)
    if not svc:
        return jsonify({'error': 'Service not found'}), 404
    if svc.get('hostId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    data = request.get_json() or {}
    Service.update(service_id, data)
    return jsonify({'ok': True}), 200


@services_bp.route('/<service_id>', methods=['DELETE'])
@login_required
def delete_service(service_id):
    from app.models.service import Service
    svc = Service.get_by_id(service_id)
    if not svc:
        return jsonify({'error': 'Service not found'}), 404
    if svc.get('hostId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Service.delete(service_id)
    return jsonify({'ok': True}), 200


@services_bp.route('/host/mine', methods=['GET'])
@login_required
def my_services():
    from app.models.service import Service
    svcs = Service.get_by_host(session['user_id'])
    return jsonify({'services': svcs}), 200
