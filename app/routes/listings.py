from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

listings_bp = Blueprint('listings', __name__, url_prefix='/api/listings')


@listings_bp.route('', methods=['GET'])
def get_listings():
    from app.models.listing import Listing
    filters = {
        'q': request.args.get('q', ''),
        'city': request.args.get('city', ''),
        'category': request.args.get('category', ''),
        'min_price': request.args.get('min_price'),
        'max_price': request.args.get('max_price'),
    }
    listings = Listing.search(filters)
    return jsonify({'listings': listings, 'total': len(listings)}), 200


@listings_bp.route('/<listing_id>', methods=['GET'])
def get_listing(listing_id):
    from app.models.listing import Listing
    listing = Listing.get_by_id(listing_id)
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    return jsonify(listing), 200


@listings_bp.route('', methods=['POST'])
@login_required
def create_listing():
    from app.models.listing import Listing
    data = request.get_json() or {}
    if not data.get('title') or not data.get('price'):
        return jsonify({'error': 'title and price are required'}), 400
    listing_id = Listing.create(session['user_id'], data)
    if not listing_id:
        return jsonify({'error': 'Failed to create listing'}), 500
    return jsonify({'id': listing_id, 'message': 'Listing created'}), 201


@listings_bp.route('/<listing_id>', methods=['PUT'])
@login_required
def update_listing(listing_id):
    from app.models.listing import Listing
    listing = Listing.get_by_id(listing_id)
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    if listing.get('hostId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    data = request.get_json() or {}
    Listing.update(listing_id, data)
    return jsonify({'ok': True}), 200


@listings_bp.route('/<listing_id>', methods=['DELETE'])
@login_required
def delete_listing(listing_id):
    from app.models.listing import Listing
    listing = Listing.get_by_id(listing_id)
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    if listing.get('hostId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Listing.delete(listing_id)
    return jsonify({'ok': True}), 200


@listings_bp.route('/host/mine', methods=['GET'])
@login_required
def my_listings():
    from app.models.listing import Listing
    listings = Listing.get_by_host(session['user_id'])
    return jsonify({'listings': listings}), 200


@listings_bp.route('/places/search', methods=['GET'])
def places_search():
    from app.services.places_service import PlacesService
    q = request.args.get('q', 'hotels')
    location = request.args.get('location', '')
    results = PlacesService.search_accommodations(q, location)
    return jsonify({'results': results}), 200


@listings_bp.route('/places/<place_id>', methods=['GET'])
def place_details(place_id):
    from app.services.places_service import PlacesService
    details = PlacesService.get_place_details(place_id)
    if not details:
        return jsonify({'error': 'Place not found'}), 404
    return jsonify(details), 200
