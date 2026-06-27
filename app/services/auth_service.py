import os
import requests as http_requests
from firebase_admin import auth as firebase_auth
from firebase_admin import firestore as fs
from flask import session
from functools import wraps
from flask import jsonify


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


class AuthService:

    @staticmethod
    def register(email, password, user_data):
        try:
            user = firebase_auth.create_user(email=email, password=password)
            from app.firebase_config import db
            if db:
                db.collection('users').document(user.uid).set({
                    'uid': user.uid,
                    'email': email,
                    'role': user_data.get('role', 'guest'),
                    'name': user_data.get('name', ''),
                    'phone': '',
                    'bio': '',
                    'profile_image': '',
                    'created_at': fs.SERVER_TIMESTAMP,
                    'updated_at': fs.SERVER_TIMESTAMP,
                })
            return user
        except firebase_auth.EmailAlreadyExistsError:
            return {'error': 'An account with this email already exists.'}
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def verify_password(email, password):
        api_key = os.getenv('FIREBASE_WEB_API_KEY', '')
        if not api_key:
            from app.models.user import User
            user = User.get_by_email(email)
            if user:
                return user
            raise ValueError('Invalid credentials. Make sure FIREBASE_WEB_API_KEY is set.')

        url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}'
        try:
            resp = http_requests.post(
                url,
                json={'email': email, 'password': password, 'returnSecureToken': True},
                timeout=10,
            )
            data = resp.json()
        except Exception:
            raise ValueError('Could not reach authentication server. Please try again.')

        if 'error' in data:
            msg = data['error'].get('message', '')
            if 'INVALID_PASSWORD' in msg or 'EMAIL_NOT_FOUND' in msg or 'INVALID_LOGIN_CREDENTIALS' in msg:
                raise ValueError('Invalid email or password.')
            if 'TOO_MANY_ATTEMPTS' in msg:
                raise ValueError('Too many failed attempts. Please try again later.')
            raise ValueError('Sign in failed. Please try again.')

        uid = data['localId']
        from app.firebase_config import db
        if db:
            doc = db.collection('users').document(uid).get()
            if doc.exists:
                return doc.to_dict()
        return {'uid': uid, 'email': email, 'role': 'guest', 'name': ''}

    @staticmethod
    def verify_token(token):
        try:
            return firebase_auth.verify_id_token(token)
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def logout():
        session.clear()
