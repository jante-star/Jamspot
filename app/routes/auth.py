from flask import Blueprint, request, jsonify, session

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _get_body():
    if request.is_json:
        return request.get_json() or {}
    return request.form.to_dict()


@auth_bp.route('/register', methods=['POST'])
def register():
    data = _get_body()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    role = data.get('role', 'guest')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    from app.services.auth_service import AuthService
    result = AuthService.register(email, password, {'name': name, 'role': role})

    if isinstance(result, dict) and 'error' in result:
        return jsonify(result), 400

    session['user_id'] = result.uid
    session['email'] = result.email
    session['role'] = role
    session['name'] = name
    session.permanent = True

    return jsonify({
        'uid': result.uid,
        'email': result.email,
        'name': name,
        'role': role,
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = _get_body()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    from app.services.auth_service import AuthService
    try:
        user = AuthService.verify_password(email, password)
    except ValueError as e:
        return jsonify({'error': str(e)}), 401

    session['user_id'] = user.get('uid') or user.get('id', '')
    session['email'] = user.get('email', email)
    session['role'] = user.get('role', 'guest')
    session['name'] = user.get('name', '')
    session.permanent = True

    return jsonify({
        'uid': session['user_id'],
        'email': session['email'],
        'name': session['name'],
        'role': session['role'],
    }), 200


@auth_bp.route('/google', methods=['POST'])
def google_signin():
    data = _get_body()
    id_token = data.get('idToken', '')
    if not id_token:
        return jsonify({'error': 'idToken is required.'}), 400

    from app.services.auth_service import AuthService
    decoded = AuthService.verify_token(id_token)
    if isinstance(decoded, dict) and 'error' in decoded:
        return jsonify({'error': 'Invalid Google sign-in token.'}), 401

    uid = decoded.get('uid')
    email = decoded.get('email', '')
    name = decoded.get('name', '')

    from app.firebase_config import db
    from firebase_admin import firestore as fs
    role = 'guest'
    if db:
        doc_ref = db.collection('users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            existing = doc.to_dict()
            role = existing.get('role', 'guest')
            name = existing.get('name') or name
        else:
            doc_ref.set({
                'uid': uid,
                'email': email,
                'role': role,
                'name': name,
                'phone': '',
                'bio': '',
                'profile_image': '',
                'created_at': fs.SERVER_TIMESTAMP,
                'updated_at': fs.SERVER_TIMESTAMP,
            })

    session['user_id'] = uid
    session['email'] = email
    session['role'] = role
    session['name'] = name
    session.permanent = True

    return jsonify({'uid': uid, 'email': email, 'name': name, 'role': role}), 200


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    from app.services.auth_service import AuthService
    AuthService.logout()
    return jsonify({'ok': True}), 200


@auth_bp.route('/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 200
    return jsonify({
        'authenticated': True,
        'uid': session['user_id'],
        'email': session.get('email', ''),
        'name': session.get('name', ''),
        'role': session.get('role', 'guest'),
    }), 200
