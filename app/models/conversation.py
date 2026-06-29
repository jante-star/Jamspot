from datetime import datetime, timezone
from app.firebase_config import get_db


class Conversation:
    @staticmethod
    def create(participant_ids, listing_id, first_message, sender_id):
        db = get_db()
        now = datetime.now(timezone.utc)
        data = {
            'participants': participant_ids,
            'listingId': listing_id,
            'lastMessage': first_message,
            'lastMessageAt': now,
            'unreadCount': {uid: (0 if uid == sender_id else 1) for uid in participant_ids},
            'created_at': now,
        }
        ref = db.collection('conversations').document()
        ref.set(data)
        doc = ref.get()
        result = doc.to_dict()
        result['id'] = doc.id

        # create the first message
        msg_ref = ref.collection('messages').document()
        msg_ref.set({
            'senderId': sender_id,
            'body': first_message,
            'createdAt': now,
            'read': False,
        })
        return result

    @staticmethod
    def get_for_user(user_id):
        db = get_db()
        docs = db.collection('conversations').where('participants', 'array_contains', user_id).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            results.append(d)
        results.sort(key=lambda x: x.get('lastMessageAt') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return results

    @staticmethod
    def get_by_id(conv_id):
        db = get_db()
        doc = db.collection('conversations').document(conv_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        d['id'] = doc.id
        return d

    @staticmethod
    def get_messages(conv_id):
        db = get_db()
        docs = db.collection('conversations').document(conv_id).collection('messages').order_by('createdAt').stream()
        msgs = []
        for doc in docs:
            m = doc.to_dict()
            m['id'] = doc.id
            msgs.append(m)
        return msgs

    @staticmethod
    def send_message(conv_id, sender_id, body, other_participants):
        db = get_db()
        now = datetime.now(timezone.utc)
        conv_ref = db.collection('conversations').document(conv_id)
        msg_ref = conv_ref.collection('messages').document()
        msg_ref.set({'senderId': sender_id, 'body': body, 'createdAt': now, 'read': False})

        update = {'lastMessage': body, 'lastMessageAt': now}
        for uid in other_participants:
            update[f'unreadCount.{uid}'] = 1
        conv_ref.update(update)

        m = msg_ref.get().to_dict()
        m['id'] = msg_ref.id
        return m

    @staticmethod
    def mark_read(conv_id, user_id):
        db = get_db()
        db.collection('conversations').document(conv_id).update({f'unreadCount.{user_id}': 0})
