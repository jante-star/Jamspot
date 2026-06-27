import os
from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required

bookings_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')


def _resolve_listing(listing_id):
    from app.models.listing import Listing
    from app.models.experience import Experience
    from app.models.service import Service
    for lt, getter in [('listing', Listing.get_by_id),
                       ('experience', Experience.get_by_id),
                       ('service', Service.get_by_id)]:
        result = getter(listing_id)
        if result:
            return result, lt
    return None, None


@bookings_bp.route('', methods=['POST'])
@login_required
def create_booking():
    from app.models.booking import Booking
    data = request.get_json() or {}

    listing_id = data.get('listing_id', '').strip()
    check_in = data.get('check_in', '')
    check_out = data.get('check_out', '')
    guests = int(data.get('guests', 1))

    if not listing_id or not check_in or not check_out:
        return jsonify({'error': 'listing_id, check_in, and check_out are required'}), 400

    listing, listing_type = _resolve_listing(listing_id)
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404

    price = listing.get('price', 0)
    try:
        from datetime import date
        d1 = date.fromisoformat(check_in)
        d2 = date.fromisoformat(check_out)
        nights = max((d2 - d1).days, 1)
    except ValueError:
        nights = 1

    total = price * (nights if listing_type in ('listing', 'experience') else guests)

    payment_intent_id = ''
    stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
    if stripe_key:
        try:
            import stripe
            stripe.api_key = stripe_key
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),
                currency='usd',
                metadata={
                    'listing_id': listing_id,
                    'listing_type': listing_type,
                    'guest_id': session['user_id'],
                },
            )
            payment_intent_id = intent['id']
        except Exception as e:
            print(f'[Bookings] Stripe error: {e}')

    booking_id = Booking.create(
        guest_id=session['user_id'],
        listing_id=listing_id,
        listing_type=listing_type,
        data={
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests,
            'total_price': total,
            'payment_intent_id': payment_intent_id,
            'notes': data.get('notes', ''),
        },
    )

    if not booking_id:
        return jsonify({'error': 'Failed to create booking'}), 500

    return jsonify({
        'booking_id': booking_id,
        'confirmation_code': booking_id[-6:].upper(),
        'total_price': total,
        'payment_intent_id': payment_intent_id,
        'stripe_publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY', ''),
    }), 201


@bookings_bp.route('/my', methods=['GET'])
@login_required
def my_bookings():
    from app.models.booking import Booking
    bookings = Booking.get_by_guest(session['user_id'])
    return jsonify({'bookings': bookings}), 200


@bookings_bp.route('/<booking_id>', methods=['GET'])
@login_required
def get_booking(booking_id):
    from app.models.booking import Booking
    booking = Booking.get_by_id(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    if booking.get('guestId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify(booking), 200


@bookings_bp.route('/<booking_id>/confirm', methods=['POST'])
@login_required
def confirm_booking(booking_id):
    from app.models.booking import Booking
    booking = Booking.get_by_id(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    if booking.get('guestId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Booking.update_status(booking_id, 'confirmed')
    return jsonify({'ok': True, 'confirmation_code': booking_id[-6:].upper()}), 200


@bookings_bp.route('/<booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    from app.models.booking import Booking
    booking = Booking.get_by_id(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    if booking.get('guestId') != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    Booking.update_status(booking_id, 'cancelled')
    return jsonify({'ok': True}), 200


@bookings_bp.route('/ai/start-call', methods=['POST'])
@login_required
def start_ai_call():
    from app.services.ai_service import RetellAIService
    data = request.get_json() or {}
    listing_id = data.get('listing_id', '')
    listing_type = data.get('listing_type', '')
    token = RetellAIService.create_call_token(
        session['user_id'],
        listing_id=listing_id,
        listing_type=listing_type,
    )
    if not token:
        return jsonify({'error': 'Could not start call — Retell AI not configured'}), 503
    return jsonify({'access_token': token}), 200
