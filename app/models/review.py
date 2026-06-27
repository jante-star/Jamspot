from datetime import datetime, timezone
from app.firebase_config import get_db


class Review:
    @staticmethod
    def get_for_listing(listing_id, listing_type='listing'):
        db = get_db()
        docs = (db.collection('reviews')
                .where('listingId', '==', listing_id)
                .where('listingType', '==', listing_type)
                .order_by('created_at', direction='DESCENDING')
                .stream())
        results = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            results.append(d)
        return results

    @staticmethod
    def create(guest_id, listing_id, listing_type, rating, comment):
        db = get_db()
        now = datetime.now(timezone.utc)
        ref = db.collection('reviews').document()
        ref.set({
            'guestId': guest_id,
            'listingId': listing_id,
            'listingType': listing_type,
            'rating': float(rating),
            'comment': comment,
            'created_at': now,
        })
        Review._update_listing_rating(db, listing_id, listing_type)
        d = ref.get().to_dict()
        d['id'] = ref.id
        return d

    @staticmethod
    def update(review_id, rating, comment):
        db = get_db()
        doc = db.collection('reviews').document(review_id).get()
        if not doc.exists:
            return None
        db.collection('reviews').document(review_id).update({'rating': float(rating), 'comment': comment})
        d = doc.to_dict()
        Review._update_listing_rating(db, d['listingId'], d['listingType'])
        updated = db.collection('reviews').document(review_id).get().to_dict()
        updated['id'] = review_id
        return updated

    @staticmethod
    def delete(review_id):
        db = get_db()
        doc = db.collection('reviews').document(review_id).get()
        if not doc.exists:
            return False
        d = doc.to_dict()
        db.collection('reviews').document(review_id).delete()
        Review._update_listing_rating(db, d['listingId'], d['listingType'])
        return True

    @staticmethod
    def get_by_id(review_id):
        db = get_db()
        doc = db.collection('reviews').document(review_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        d['id'] = doc.id
        return d

    @staticmethod
    def _update_listing_rating(db, listing_id, listing_type):
        collection = {'listing': 'listings', 'experience': 'experiences', 'service': 'services'}.get(listing_type, 'listings')
        reviews = db.collection('reviews').where('listingId', '==', listing_id).where('listingType', '==', listing_type).stream()
        ratings = [r.to_dict().get('rating', 0) for r in reviews]
        if ratings:
            avg = round(sum(ratings) / len(ratings), 2)
            count = len(ratings)
        else:
            avg = 0
            count = 0
        db.collection(collection).document(listing_id).update({'ratings': {'average': avg, 'count': count}})
