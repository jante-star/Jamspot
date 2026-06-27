import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import os
import json

db = None
auth_client = None
bucket = None

firebase_storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET', '')


def _init_firebase():
    global db, auth_client, bucket
    init_options = {}
    if firebase_storage_bucket:
        init_options['storageBucket'] = firebase_storage_bucket

    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '')
    if service_account_json:
        try:
            cred = credentials.Certificate(json.loads(service_account_json))
            firebase_admin.initialize_app(cred, init_options)
            db = firestore.client()
            auth_client = auth
            if firebase_storage_bucket:
                bucket = storage.bucket()
            print('✅ Firebase connected (env var credentials)')
            if not firebase_storage_bucket:
                print('⚠️  FIREBASE_STORAGE_BUCKET not set — image uploads disabled')
            return
        except Exception as e:
            print(f'⚠️  Firebase env var error: {e}')

    firebase_key_path = os.getenv('FIREBASE_KEY_PATH', './firebase-key.json')
    if os.path.exists(firebase_key_path):
        try:
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred, init_options)
            db = firestore.client()
            auth_client = auth
            if firebase_storage_bucket:
                bucket = storage.bucket()
            print('✅ Firebase connected (key file)')
            if not firebase_storage_bucket:
                print('⚠️  FIREBASE_STORAGE_BUCKET not set — image uploads disabled')
            return
        except Exception as e:
            print(f'⚠️  Firebase key file error: {e}')

    print('⚠️  Firebase not configured — set FIREBASE_SERVICE_ACCOUNT_JSON or firebase-key.json')


_init_firebase()


def get_db():
    return db
