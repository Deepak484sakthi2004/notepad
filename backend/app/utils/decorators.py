from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app.models.workspace import Workspace
from app.models.page import Page


def jwt_required_with_user(fn):
    """Verify JWT and inject current_user into kwargs."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 401
        kwargs["current_user"] = user
        return fn(*args, **kwargs)

    return wrapper


def workspace_member_required(fn):
    """Verify the user owns the workspace identified by wid in URL."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": "Unauthorized"}), 401

        wid = kwargs.get("wid") or kwargs.get("workspace_id")
        if not wid:
            return jsonify({"error": "Workspace ID required"}), 400

        workspace = Workspace.query.filter_by(id=wid, owner_id=user_id).first()
        if not workspace:
            return jsonify({"error": "Workspace not found"}), 404

        kwargs["current_user"] = user
        kwargs["workspace"] = workspace
        return fn(*args, **kwargs)

    return wrapper


def page_access_required(fn):
    """Verify the user has access to the page identified by page_id in URL."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": "Unauthorized"}), 401

        page_id = kwargs.get("page_id")
        if not page_id:
            return jsonify({"error": "Page ID required"}), 400

        page = Page.query.get(page_id)
        if not page:
            return jsonify({"error": "Page not found"}), 404

        workspace = Workspace.query.filter_by(
            id=page.workspace_id, owner_id=user_id
        ).first()
        if not workspace:
            return jsonify({"error": "Access denied"}), 403

        kwargs["current_user"] = user
        kwargs["page"] = page
        kwargs["workspace"] = workspace
        return fn(*args, **kwargs)

    return wrapper
