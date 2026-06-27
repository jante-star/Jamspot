from flask import Blueprint, jsonify, session
from app.services.auth_service import login_required
from collections import defaultdict

host_bp = Blueprint('host', __name__, url_prefix='/api/host')


def _get_host_listings(user_id):
    from app.models.listing import Listing
    from app.models.experience import Experience
    from app.models.service import Service
    listings = Listing.get_by_host(user_id)
    experiences = Experience.get_by_host(user_id) if hasattr(Experience, 'get_by_host') else []
    services = Service.get_by_host(user_id) if hasattr(Service, 'get_by_host') else []
    return listings, experiences, services


def _get_all_host_bookings(listing_ids):
    from app.models.booking import Booking
    from app.firebase_config import get_db
    db = get_db()
    all_bookings = []
    for lid in listing_ids:
        all_bookings.extend(Booking.get_by_listing(lid))
    return all_bookings


@host_bp.route('/bookings', methods=['GET'])
@login_required
def host_bookings():
    listings, experiences, services = _get_host_listings(session['user_id'])
    listing_ids = [l['id'] for l in listings + experiences + services if l.get('id')]
    bookings = _get_all_host_bookings(listing_ids)
    bookings.sort(key=lambda b: b.get('created_at') or '', reverse=True)
    return jsonify({'bookings': bookings}), 200


@host_bp.route('/earnings', methods=['GET'])
@login_required
def host_earnings():
    listings, experiences, services = _get_host_listings(session['user_id'])
    listing_ids = [l['id'] for l in listings + experiences + services if l.get('id')]
    bookings = _get_all_host_bookings(listing_ids)

    total_revenue = 0.0
    pending_payout = 0.0
    monthly = defaultdict(float)

    for b in bookings:
        if b.get('status') in ('confirmed', 'completed'):
            price = float(b.get('totalPrice') or 0)
            total_revenue += price
            pending_payout += price
            created = b.get('created_at')
            if created:
                try:
                    month_key = created.strftime('%Y-%m') if hasattr(created, 'strftime') else str(created)[:7]
                    monthly[month_key] += price
                except Exception:
                    pass

    monthly_breakdown = [{'month': k, 'revenue': round(v, 2)} for k, v in sorted(monthly.items())]
    return jsonify({
        'totalRevenue': round(total_revenue, 2),
        'pendingPayout': round(pending_payout, 2),
        'currency': 'USD',
        'monthlyBreakdown': monthly_breakdown,
    }), 200


@host_bp.route('/analytics', methods=['GET'])
@login_required
def host_analytics():
    listings, experiences, services = _get_host_listings(session['user_id'])
    all_items = listings + experiences + services
    listing_ids = [l['id'] for l in all_items if l.get('id')]
    bookings = _get_all_host_bookings(listing_ids)

    confirmed = [b for b in bookings if b.get('status') in ('confirmed', 'completed')]
    booking_rate = round(len(confirmed) / len(bookings) * 100, 1) if bookings else 0

    bookings_by_listing = defaultdict(int)
    revenue_by_listing = defaultdict(float)
    for b in confirmed:
        lid = b.get('listingId', '')
        bookings_by_listing[lid] += 1
        revenue_by_listing[lid] += float(b.get('totalPrice') or 0)

    listing_map = {l['id']: l for l in all_items if l.get('id')}
    top_listings = sorted(
        [{'id': lid, 'title': listing_map.get(lid, {}).get('title', lid),
          'bookings': bookings_by_listing[lid], 'revenue': round(revenue_by_listing[lid], 2)}
         for lid in listing_ids],
        key=lambda x: x['revenue'], reverse=True
    )[:5]

    return jsonify({
        'totalListings': len(all_items),
        'totalBookings': len(bookings),
        'confirmedBookings': len(confirmed),
        'bookingRate': booking_rate,
        'topListings': top_listings,
    }), 200
