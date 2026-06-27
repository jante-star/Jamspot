from firebase_admin import firestore as fs
import uuid


class Booking:
    COLLECTION = 'bookings'

    @staticmethod
    def get_by_id(booking_id):
        from app.firebase_config import db
        if not db or not booking_id:
            return None
        doc = db.collection(Booking.COLLECTION).document(booking_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    @staticmethod
    def create(guest_id, listing_id, listing_type, data):
        from app.firebase_config import db
        if not db:
            return None
        doc_ref = db.collection(Booking.COLLECTION).document()
        doc_ref.set({
            'guestId': guest_id,
            'listingId': listing_id,
            'listingType': listing_type,
            'checkIn': data.get('check_in', ''),
            'checkOut': data.get('check_out', ''),
            'guests': int(data.get('guests', 1)),
            'totalPrice': float(data.get('total_price', 0)),
            'currency': data.get('currency', 'USD'),
            'status': 'pending',
            'paymentIntentId': data.get('payment_intent_id', ''),
            'notes': data.get('notes', ''),
            'created_at': fs.SERVER_TIMESTAMP,
            'updated_at': fs.SERVER_TIMESTAMP,
        })
        return doc_ref.id

    @staticmethod
    def get_by_guest(guest_id):
        from app.firebase_config import db
        if not db:
            return []
        results = []
        for doc in db.collection(Booking.COLLECTION).where('guestId', '==', guest_id).stream():
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        return results

    @staticmethod
    def get_by_listing(listing_id):
        from app.firebase_config import db
        if not db:
            return []
        results = []
        for doc in db.collection(Booking.COLLECTION).where('listingId', '==', listing_id).stream():
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        return results

    @staticmethod
    def update_status(booking_id, status):
        from app.firebase_config import db
        if not db:
            return False
        db.collection(Booking.COLLECTION).document(booking_id).update({
            'status': status,
            'updated_at': fs.SERVER_TIMESTAMP,
        })
        return True

    @staticmethod
    def update(booking_id, data):
        from app.firebase_config import db
        if not db:
            return False
        data['updated_at'] = fs.SERVER_TIMESTAMP
        db.collection(Booking.COLLECTION).document(booking_id).update(data)
        return True
