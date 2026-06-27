from firebase_admin import firestore as fs


class Experience:
    COLLECTION = 'experiences'

    @staticmethod
    def get_by_id(exp_id):
        from app.firebase_config import db
        if not db or not exp_id:
            return None
        doc = db.collection(Experience.COLLECTION).document(exp_id).get()
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
        doc_ref = db.collection(Experience.COLLECTION).document()
        doc_ref.set({
            'hostId': host_id,
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'price': float(data.get('price', 0)),
            'duration': data.get('duration', ''),
            'maxGroupSize': int(data.get('maxGroupSize', 10)),
            'location': data.get('location', {}),
            'photos': data.get('photos', []),
            'category': data.get('category', 'experience'),
            'languages': data.get('languages', ['English']),
            'included': data.get('included', []),
            'status': 'active',
            'ratings': {'average': 0, 'count': 0},
            'created_at': fs.SERVER_TIMESTAMP,
            'updated_at': fs.SERVER_TIMESTAMP,
        })
        return doc_ref.id

    @staticmethod
    def get_all_published():
        from app.firebase_config import db
        if not db:
            return []
        results = []
        for doc in db.collection(Experience.COLLECTION).where('status', '==', 'active').stream():
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        return results

    @staticmethod
    def search(filters=None):
        from app.firebase_config import db
        if not db:
            return []
        filters = filters or {}
        results = []
        for doc in db.collection(Experience.COLLECTION).where('status', '==', 'active').stream():
            data = doc.to_dict()
            data['id'] = doc.id
            q = (filters.get('q') or '').lower()
            if q and q not in data.get('title', '').lower():
                continue
            results.append(data)
        return results

    @staticmethod
    def get_by_host(host_id):
        from app.firebase_config import db
        if not db:
            return []
        results = []
        for doc in db.collection(Experience.COLLECTION).where('hostId', '==', host_id).stream():
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        return results

    @staticmethod
    def update(exp_id, data):
        from app.firebase_config import db
        if not db:
            return False
        data['updated_at'] = fs.SERVER_TIMESTAMP
        db.collection(Experience.COLLECTION).document(exp_id).update(data)
        return True

    @staticmethod
    def delete(exp_id):
        from app.firebase_config import db
        if not db:
            return False
        db.collection(Experience.COLLECTION).document(exp_id).delete()
        return True
