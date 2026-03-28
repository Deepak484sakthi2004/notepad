from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from app.extensions import db
from app.models.user import User
from app.services.auth_service import (
    authenticate_user,
    blacklist_token,
    register_user,
    send_otp_email,
    verify_otp_and_reset,
)
from app.utils.validators import validate_email, validate_password_strength

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 422
    if not validate_email(email):
        return jsonify({"error": "Invalid email address"}), 422
    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"error": msg}), 422

    try:
        user_dict = register_user(name, email, password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    user = User.query.filter_by(email=email.lower()).first()
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    resp = jsonify({"user": user_dict, "access_token": access_token})
    set_refresh_cookies(resp, refresh_token)
    return resp, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 422

    try:
        user = authenticate_user(email, password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    resp = jsonify({"user": user.to_dict(), "access_token": access_token})
    set_refresh_cookies(resp, refresh_token)
    return resp, 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    jti = get_jwt()["jti"]
    blacklist_token(jti, timedelta(days=7))
    resp = jsonify({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp, 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    claims = get_jwt()
    jti = claims.get("jti")
    from app.services.auth_service import is_token_blacklisted
    if jti and is_token_blacklisted(jti):
        return jsonify({"error": "Token has been revoked"}), 401

    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 422

    user = User.query.filter_by(email=email).first()
    # Always return success to avoid user enumeration
    if user:
        send_otp_email(user)
    return jsonify({"message": "If the email exists, an OTP has been sent."}), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()
    new_password = data.get("new_password") or ""

    if not email or not otp or not new_password:
        return jsonify({"error": "email, otp, and new_password are required"}), 422

    ok, msg = validate_password_strength(new_password)
    if not ok:
        return jsonify({"error": msg}), 422

    success = verify_otp_and_reset(email, otp, new_password)
    if not success:
        return jsonify({"error": "Invalid or expired OTP"}), 400

    return jsonify({"message": "Password reset successfully"}), 200
