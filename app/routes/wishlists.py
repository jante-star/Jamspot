from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

wishlists_bp = Blueprint('wishlists', __name__, url_prefix='/api/wishlists')


@wishlists_bp.route('', methods=['GET'])
@login_required
def get_wishlists():
    from app.models.wishlist import Wishlist
    lists = Wishlist.get_for_user(session['user_id'])
    return jsonify({'wishlists': lists}), 200


@wishlists_bp.route('', methods=['POST'])
@login_required
def create_wishlist():
    from app.models.wishlist import Wishlist
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400
    wishlist = Wishlist.create(session['user_id'], name)
    return jsonify(wishlist), 201


@wishlists_bp.route('/<wishlist_id>/add', methods=['POST'])
@login_required
def add_to_wishlist(wishlist_id):
    from app.models.wishlist import Wishlist
    wishlist = Wishlist.get_by_id(wishlist_id)
    if not wishlist:
        return jsonify({'error': 'Not found'}), 404
    if wishlist.get('userId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    data = request.get_json() or {}
    listing_id = data.get('listingId')
    if not listing_id:
        return jsonify({'error': 'listingId is required'}), 400
    Wishlist.add_listing(wishlist_id, listing_id)
    return jsonify({'ok': True}), 200


@wishlists_bp.route('/<wishlist_id>/remove/<listing_id>', methods=['DELETE'])
@login_required
def remove_from_wishlist(wishlist_id, listing_id):
    from app.models.wishlist import Wishlist
    wishlist = Wishlist.get_by_id(wishlist_id)
    if not wishlist:
        return jsonify({'error': 'Not found'}), 404
    if wishlist.get('userId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Wishlist.remove_listing(wishlist_id, listing_id)
    return jsonify({'ok': True}), 200


@wishlists_bp.route('/<wishlist_id>', methods=['DELETE'])
@login_required
def delete_wishlist(wishlist_id):
    from app.models.wishlist import Wishlist
    wishlist = Wishlist.get_by_id(wishlist_id)
    if not wishlist:
        return jsonify({'error': 'Not found'}), 404
    if wishlist.get('userId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Wishlist.delete(wishlist_id)
    return jsonify({'ok': True}), 200
