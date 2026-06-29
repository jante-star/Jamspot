from firebase_admin import firestore as fs


class Listing:
    COLLECTION = 'listings'

    @staticmethod
    def get_by_id(listing_id):
        from app.firebase_config import db
        if not db or not listing_id:
            return None
        doc = db.collection(Listing.COLLECTION).document(listing_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    @staticmethod
    def create(host_id, data):
        from app.firebase_config import db
        if not db:
            return None
        doc_ref = db.collection(Listing.COLLECTION).document()
        doc_ref.set({
            'hostId': host_id,
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'price': float(data.get('price', 0)),
            'location': data.get('location', {}),
            'photos': data.get('photos', []),
            'amenities': data.get('amenities', []),
            'bedrooms': int(data.get('bedrooms', 1)),
            'bathrooms': float(data.get('bathrooms', 1)),
            'maxGuests': int(data.get('maxGuests', 2)),
            'category': data.get('category', 'home'),
            'status': 'active',
            'ratings': {'average': 0, 'count': 0},
            'created_at': fs.SERVER_TIMESTAMP,
            'updated_at': fs.SERVER_TIMESTAMP,
        })
        return doc_ref.id

    @staticmethod
    def search(filters=None):
        from app.firebase_config import db
        if not db:
            return []
        filters = filters or {}
        query = db.collection(Listing.COLLECTION).where('status', '==', 'active')
        q = (filters.get('q') or '').lower()
        category = (filters.get('category') or '').lower()
        city_f = (filters.get('city') or '').lower()
        try:
            min_price = float(filters.get('min_price') or 0)
            max_price = float(filters.get('max_price') or 0)
        except (TypeError, ValueError):
            min_price = max_price = 0
        results = []
        for doc in query.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            loc = data.get('location', {})
            city = loc.get('city', '').lower()
            if q and q not in data.get('title', '').lower() and q not in city:
                continue
            if category and data.get('category', '').lower() != category:
                continue
            if city_f and city_f not in city:
                continue
            price = float(data.get('price', 0))
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue
            results.append(data)
        return results

    @staticmethod
    def get_by_host(host_id):
        from app.firebase_config import db
        if not db:
            return []
        results = []
        for doc in db.collection(Listing.COLLECTION).where('hostId', '==', host_id).stream():
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        return results

    @staticmethod
    def update(listing_id, data):
        from app.firebase_config import db
        if not db:
            return False
        data['updated_at'] = fs.SERVER_TIMESTAMP
        db.collection(Listing.COLLECTION).document(listing_id).update(data)
        return True

    @staticmethod
    def delete(listing_id):
        from app.firebase_config import db
        if not db:
            return False
        db.collection(Listing.COLLECTION).document(listing_id).delete()
        return True
