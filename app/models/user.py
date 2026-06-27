from firebase_admin import firestore as fs


class User:
    COLLECTION = 'users'

    @staticmethod
    def get_by_id(uid):
        from app.firebase_config import db
        if not db or not uid:
            return None
        doc = db.collection(User.COLLECTION).document(uid).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    @staticmethod
    def get_by_email(email):
        from app.firebase_config import db
        if not db or not email:
            return None
        docs = db.collection(User.COLLECTION).where('email', '==', email).limit(1).stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    @staticmethod
    def update(uid, data):
        from app.firebase_config import db
        if not db or not uid:
            return False
        data['updated_at'] = fs.SERVER_TIMESTAMP
        db.collection(User.COLLECTION).document(uid).update(data)
        return True
