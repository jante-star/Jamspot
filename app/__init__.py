import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS


def create_app(config=None):
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'project'),
        static_url_path='',
    )

    if config:
        app.config.from_object(config)

    CORS(app, resources={r'/api/*': {'origins': '*'}}, supports_credentials=True)

    from app.routes.auth import auth_bp
    from app.routes.listings import listings_bp
    from app.routes.experiences import experiences_bp
    from app.routes.services import services_bp
    from app.routes.bookings import bookings_bp
    from app.routes.search import search_bp
    from app.routes.profile import profile_bp
    from app.routes.retell_webhook import retell_bp
    from app.routes.messages import messages_bp
    from app.routes.wishlists import wishlists_bp
    from app.routes.reviews import reviews_bp
    from app.routes.host import host_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(experiences_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(retell_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(wishlists_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(host_bp)

    @app.route('/health')
    def health():
        return jsonify({'ok': True}), 200

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_files(path):
        try:
            return send_from_directory(app.static_folder, path)
        except Exception:
            return send_from_directory(app.static_folder, 'index.html')

    return app
