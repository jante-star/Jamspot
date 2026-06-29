from flask import Blueprint, request, jsonify

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


@search_bp.route('', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    content_type = request.args.get('type', 'all').lower()
    filters = {'q': q}

    results = {}

    if content_type in ('all', 'stays', 'listings'):
        from app.models.listing import Listing
        results['listings'] = Listing.search(filters)

    if content_type in ('all', 'experiences'):
        from app.models.experience import Experience
        results['experiences'] = Experience.search(filters)

    if content_type in ('all', 'services'):
        from app.models.service import Service
        results['services'] = Service.search(filters)

    total = len(results.get('listings', [])) + len(results.get('experiences', [])) + len(results.get('services', []))

    return jsonify({
        'listings': results.get('listings', []),
        'experiences': results.get('experiences', []),
        'services': results.get('services', []),
        'query': q, 'type': content_type, 'total': total
    }), 200
