import hashlib
import hmac
import os

from flask import Blueprint, request, jsonify
from firebase_admin import firestore as fs

from app.models.listing import Listing
from app.models.experience import Experience
from app.models.service import Service
from app.models.booking import Booking
from app.models.user import User

retell_bp = Blueprint('retell', __name__, url_prefix='/api/retell')

WEBHOOK_SECRET = os.getenv('RETELL_WEBHOOK_SECRET', '')


def _verify_signature(payload_bytes, sig_header):
    if not WEBHOOK_SECRET:
        return True
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header or '')


@retell_bp.route('/events', methods=['POST'])
def call_events():
    raw = request.get_data()
    sig = request.headers.get('x-retell-signature', '')
    if not _verify_signature(raw, sig):
        return jsonify({'error': 'Invalid signature'}), 401

    data = request.get_json(force=True) or {}
    event = data.get('event')
    call = data.get('call', {})

    if event == 'call_analyzed':
        _save_call_log(call)

    return jsonify({'received': True}), 200


def _save_call_log(call):
    try:
        from app.firebase_config import db
        if not db:
            return
        db.collection('call_logs').add({
            'callId': call.get('call_id'),
            'agentId': call.get('agent_id'),
            'listingId': (call.get('metadata') or {}).get('listing_id', ''),
            'listingType': (call.get('metadata') or {}).get('listing_type', ''),
            'startTimestamp': call.get('start_timestamp'),
            'endTimestamp': call.get('end_timestamp'),
            'durationMs': call.get('duration_ms'),
            'transcript': call.get('transcript', ''),
            'callAnalysis': call.get('call_analysis', {}),
            'created_at': fs.SERVER_TIMESTAMP,
        })
    except Exception as e:
        print(f'[RetellWebhook] save_call_log error: {e}')


def _parse_tool_request():
    body = request.get_json(force=True) or {}
    return body.get('args', {}), body.get('call', {})


@retell_bp.route('/tools/get_listing', methods=['POST'])
def tool_get_listing():
    args, _ = _parse_tool_request()
    listing_id = args.get('listing_id', '').strip()
    name = args.get('name', '').lower()
    city = args.get('city', '').lower()

    listing = None
    listing_type = None

    if listing_id:
        for lt, getter in [('listing', Listing.get_by_id),
                           ('experience', Experience.get_by_id),
                           ('service', Service.get_by_id)]:
            result = getter(listing_id)
            if result:
                listing, listing_type = result, lt
                break

    if not listing and (name or city):
        listing, listing_type = _fuzzy_find(name, city)

    if not listing:
        return jsonify({'found': False, 'message': 'Listing not found.'}), 200

    return jsonify(_listing_payload(listing_type, listing)), 200


@retell_bp.route('/tools/check_availability', methods=['POST'])
def tool_check_availability():
    args, _ = _parse_tool_request()
    listing_id = args.get('listing_id', '').strip()
    check_in = args.get('check_in', '')
    check_out = args.get('check_out', '')

    if not listing_id or not check_in or not check_out:
        return jsonify({'error': 'listing_id, check_in, and check_out are required'}), 200

    try:
        from app.firebase_config import db
        if not db:
            return jsonify({'available': True, 'note': 'Firebase not connected'}), 200

        conflicts = []
        bookings = (
            db.collection('bookings')
            .where('listingId', '==', listing_id)
            .where('status', 'in', ['pending', 'confirmed'])
            .stream()
        )
        for doc in bookings:
            b = doc.to_dict()
            b_in = b.get('checkIn', '')
            b_out = b.get('checkOut', '')
            if b_in and b_out and check_in < b_out and check_out > b_in:
                conflicts.append({'check_in': b_in, 'check_out': b_out})

        return jsonify({
            'listing_id': listing_id,
            'check_in': check_in,
            'check_out': check_out,
            'available': len(conflicts) == 0,
            'conflicts': conflicts,
        }), 200

    except Exception as e:
        print(f'[RetellWebhook] check_availability error: {e}')
        return jsonify({'available': True, 'note': 'Could not verify — please confirm with host'}), 200


@retell_bp.route('/tools/create_booking', methods=['POST'])
def tool_create_booking():
    args, call = _parse_tool_request()

    listing_id = args.get('listing_id', '').strip()
    check_in = args.get('check_in', '')
    check_out = args.get('check_out', '')
    guests = int(args.get('guests', 1))
    contact_name = args.get('contact_name', '')
    contact_phone = args.get('contact_phone', '')

    if not listing_id or not check_in or not check_out or not contact_name:
        return jsonify({'error': 'listing_id, check_in, check_out, and contact_name are required'}), 200

    listing = None
    listing_type = 'listing'
    for lt, getter in [('listing', Listing.get_by_id),
                       ('experience', Experience.get_by_id),
                       ('service', Service.get_by_id)]:
        result = getter(listing_id)
        if result:
            listing, listing_type = result, lt
            break

    if not listing:
        return jsonify({'error': 'Listing not found — cannot create booking'}), 200

    price = listing.get('price', 0)
    try:
        from datetime import date
        d1 = date.fromisoformat(check_in)
        d2 = date.fromisoformat(check_out)
        nights = max((d2 - d1).days, 1)
    except ValueError:
        nights = 1

    total = price * (nights if listing_type in ('listing', 'experience') else guests)

    booking_id = Booking.create(
        guest_id=f'call_{call.get("call_id", "unknown")}',
        listing_id=listing_id,
        listing_type=listing_type,
        data={
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests,
            'total_price': total,
            'notes': f'Booked via AI call. Caller: {contact_name} {contact_phone}'.strip(),
        },
    )

    if not booking_id:
        return jsonify({'error': 'Could not create booking — please try again'}), 200

    confirmation_code = booking_id[-6:].upper()
    return jsonify({
        'booking_id': booking_id,
        'confirmation_code': confirmation_code,
        'listing_title': listing.get('title', ''),
        'check_in': check_in,
        'check_out': check_out,
        'guests': guests,
        'total_price': total,
        'currency': 'USD',
        'status': 'pending',
        'message': (
            f"Booking confirmed! Your confirmation code is {confirmation_code}. "
            f"Total: ${total:.0f}. You'll receive details at the contact number provided."
        ),
    }), 200


@retell_bp.route('/tools/transfer_to_host', methods=['POST'])
def tool_transfer_to_host():
    args, _ = _parse_tool_request()
    listing_id = args.get('listing_id', '').strip()

    host_phone = None
    for getter in [Listing.get_by_id, Experience.get_by_id, Service.get_by_id]:
        result = getter(listing_id)
        if result:
            host_id = result.get('hostId', '')
            if host_id:
                host = User.get_by_id(host_id)
                if host:
                    host_phone = host.get('phone', '')
            break

    if host_phone:
        return jsonify({'phone': host_phone}), 200

    return jsonify({'phone': None, 'message': 'Host phone not available — transferring to support.'}), 200


def _fuzzy_find(name, city):
    for lt, get_all in [('listing', Listing.search),
                        ('experience', Experience.get_all_published),
                        ('service', Service.get_all_published)]:
        items = get_all({}) if lt == 'listing' else get_all()
        for item in items:
            t = (item.get('title') or '').lower()
            c = (item.get('location') or {}).get('city', '').lower()
            if (not name or name in t) and (not city or city in c):
                return item, lt
    return None, None


def _listing_payload(listing_type, listing):
    loc = listing.get('location') or {}
    price_unit = {'listing': 'night', 'experience': 'person', 'service': 'session'}.get(listing_type, 'item')
    return {
        'found': True,
        'listing_id': listing.get('id'),
        'type': listing_type,
        'title': listing.get('title'),
        'city': loc.get('city'),
        'country': loc.get('country'),
        'address': loc.get('address'),
        'price': listing.get('price'),
        'price_unit': price_unit,
        'description': listing.get('description'),
        'bedrooms': listing.get('bedrooms'),
        'bathrooms': listing.get('bathrooms'),
        'amenities': listing.get('amenities', []),
        'capacity': listing.get('maxGuests') or listing.get('maxGroupSize'),
        'rating': (listing.get('ratings') or {}).get('average'),
        'host_id': listing.get('hostId'),
    }
