from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

messages_bp = Blueprint('messages', __name__, url_prefix='/api/conversations')


@messages_bp.route('', methods=['GET'])
@login_required
def list_conversations():
    from app.models.conversation import Conversation
    convs = Conversation.get_for_user(session['user_id'])
    return jsonify({'conversations': convs}), 200


@messages_bp.route('', methods=['POST'])
@login_required
def start_conversation():
    from app.models.conversation import Conversation
    from app.models.listing import Listing
    data = request.get_json() or {}
    listing_id = data.get('listingId')
    message = data.get('message', '').strip()
    if not listing_id or not message:
        return jsonify({'error': 'listingId and message are required'}), 400

    listing = Listing.get_by_id(listing_id)
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404

    host_id = listing.get('hostId')
    user_id = session['user_id']
    if user_id == host_id:
        return jsonify({'error': 'Cannot message your own listing'}), 400

    conv = Conversation.create([user_id, host_id], listing_id, message, user_id)
    return jsonify(conv), 201


@messages_bp.route('/<conv_id>', methods=['GET'])
@login_required
def get_conversation(conv_id):
    from app.models.conversation import Conversation
    conv = Conversation.get_by_id(conv_id)
    if not conv:
        return jsonify({'error': 'Not found'}), 404
    if session['user_id'] not in conv.get('participants', []):
        return jsonify({'error': 'Forbidden'}), 403
    messages = Conversation.get_messages(conv_id)
    return jsonify({'conversation': conv, 'messages': messages}), 200


@messages_bp.route('/<conv_id>/messages', methods=['POST'])
@login_required
def send_message(conv_id):
    from app.models.conversation import Conversation
    conv = Conversation.get_by_id(conv_id)
    if not conv:
        return jsonify({'error': 'Not found'}), 404
    user_id = session['user_id']
    participants = conv.get('participants', [])
    if user_id not in participants:
        return jsonify({'error': 'Forbidden'}), 403
    data = request.get_json() or {}
    body = data.get('body', '').strip()
    if not body:
        return jsonify({'error': 'body is required'}), 400
    others = [p for p in participants if p != user_id]
    msg = Conversation.send_message(conv_id, user_id, body, others)
    return jsonify(msg), 201


@messages_bp.route('/<conv_id>/read', methods=['PUT'])
@login_required
def mark_read(conv_id):
    from app.models.conversation import Conversation
    conv = Conversation.get_by_id(conv_id)
    if not conv:
        return jsonify({'error': 'Not found'}), 404
    if session['user_id'] not in conv.get('participants', []):
        return jsonify({'error': 'Forbidden'}), 403
    Conversation.mark_read(conv_id, session['user_id'])
    return jsonify({'ok': True}), 200
