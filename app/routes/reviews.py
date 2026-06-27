from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')


@reviews_bp.route('', methods=['GET'])
def get_reviews():
    from app.models.review import Review
    listing_id = request.args.get('listingId')
    listing_type = request.args.get('listingType', 'listing')
    if not listing_id:
        return jsonify({'error': 'listingId is required'}), 400
    reviews = Review.get_for_listing(listing_id, listing_type)
    return jsonify({'reviews': reviews}), 200


@reviews_bp.route('', methods=['POST'])
@login_required
def create_review():
    from app.models.review import Review
    from app.models.booking import Booking
    data = request.get_json() or {}
    listing_id = data.get('listingId')
    listing_type = data.get('listingType', 'listing')
    rating = data.get('rating')
    comment = data.get('comment', '')

    if not listing_id or rating is None:
        return jsonify({'error': 'listingId and rating are required'}), 400
    try:
        rating = float(rating)
        if not (1 <= rating <= 5):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'rating must be a number between 1 and 5'}), 400

    user_id = session['user_id']
    bookings = Booking.get_by_guest(user_id)
    has_booking = any(
        b.get('listingId') == listing_id and b.get('status') in ('confirmed', 'completed')
        for b in bookings
    )
    if not has_booking:
        return jsonify({'error': 'You must have a confirmed booking to leave a review'}), 403

    review = Review.create(user_id, listing_id, listing_type, rating, comment)
    return jsonify(review), 201


@reviews_bp.route('/<review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    from app.models.review import Review
    review = Review.get_by_id(review_id)
    if not review:
        return jsonify({'error': 'Not found'}), 404
    if review.get('guestId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    data = request.get_json() or {}
    rating = data.get('rating', review['rating'])
    comment = data.get('comment', review.get('comment', ''))
    updated = Review.update(review_id, rating, comment)
    return jsonify(updated), 200


@reviews_bp.route('/<review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    from app.models.review import Review
    review = Review.get_by_id(review_id)
    if not review:
        return jsonify({'error': 'Not found'}), 404
    if review.get('guestId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Review.delete(review_id)
    return jsonify({'ok': True}), 200
