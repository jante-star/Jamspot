import os
from werkzeug.utils import secure_filename

ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


class StorageService:

    @staticmethod
    def upload(file_obj, folder='uploads'):
        from app.firebase_config import bucket
        if not bucket:
            return None
        if not file_obj or not file_obj.filename:
            return None
        ext = file_obj.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED:
            return None
        filename = secure_filename(file_obj.filename)
        blob_path = f'{folder}/{filename}'
        try:
            blob = bucket.blob(blob_path)
            blob.upload_from_file(file_obj, content_type=file_obj.content_type)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print(f'[StorageService] upload error: {e}')
            return None

    @staticmethod
    def upload_multiple(files, folder='uploads'):
        urls = []
        for f in files:
            url = StorageService.upload(f, folder)
            if url:
                urls.append(url)
        return urls
