from datetime import datetime, timezone
from app.firebase_config import get_db


class Wishlist:
    @staticmethod
    def get_for_user(user_id):
        db = get_db()
        docs = db.collection('wishlists').where('userId', '==', user_id).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            results.append(d)
        return results

    @staticmethod
    def create(user_id, name):
        db = get_db()
        now = datetime.now(timezone.utc)
        ref = db.collection('wishlists').document()
        ref.set({'userId': user_id, 'name': name, 'listingIds': [], 'created_at': now})
        d = ref.get().to_dict()
        d['id'] = ref.id
        return d

    @staticmethod
    def get_by_id(wishlist_id):
        db = get_db()
        doc = db.collection('wishlists').document(wishlist_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        d['id'] = doc.id
        return d

    @staticmethod
    def add_listing(wishlist_id, listing_id):
        db = get_db()
        from google.cloud.firestore import ArrayUnion
        db.collection('wishlists').document(wishlist_id).update({'listingIds': ArrayUnion([listing_id])})

    @staticmethod
    def remove_listing(wishlist_id, listing_id):
        db = get_db()
        from google.cloud.firestore import ArrayRemove
        db.collection('wishlists').document(wishlist_id).update({'listingIds': ArrayRemove([listing_id])})

    @staticmethod
    def delete(wishlist_id):
        db = get_db()
        db.collection('wishlists').document(wishlist_id).delete()
