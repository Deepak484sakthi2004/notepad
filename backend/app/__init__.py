import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from app.config import get_config
from app.extensions import db, jwt, mail, migrate, limiter, init_redis
from app.routes import auth_bp, workspaces_bp, pages_bp, tags_bp, search_bp, flashcards_bp, ai_bp


def create_app(config_class=None):
    app = Flask(__name__, static_folder=None)

    cfg = config_class or get_config()
    app.config.from_object(cfg)

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Redis
    try:
        init_redis(app)
    except Exception as exc:
        app.logger.warning("Redis init failed (non-fatal): %s", exc)

    # CORS
    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS", ["http://localhost:5173"]),
        supports_credentials=True,
    )

    # JWT token blacklist callback
    from app.services.auth_service import is_token_blacklisted

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return is_token_blacklisted(jwt_payload.get("jti", ""))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({"error": "Token has expired", "code": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from flask import jsonify
        return jsonify({"error": "Invalid token", "code": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        from flask import jsonify
        return jsonify({"error": "Authorization required", "code": "authorization_required"}), 401

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(workspaces_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(ai_bp)

    # User profile routes (registered on flashcards_bp but under /api/user)
    @app.route("/api/user/profile", methods=["GET"])
    def user_profile_get_alias():
        from flask_jwt_extended import jwt_required, get_jwt_identity
        from app.models.user import User
        from flask import jsonify
        # delegate
        return app.view_functions["flashcards.user_profile_get"]()

    # Serve uploads
    upload_folder = app.config.get("UPLOAD_FOLDER", "./uploads")
    os.makedirs(upload_folder, exist_ok=True)

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(os.path.abspath(upload_folder), filename)

    @app.route("/api/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "ok"}), 200

    # Create tables in development
    with app.app_context():
        db.create_all()

    return app
