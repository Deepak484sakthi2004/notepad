from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.workspace import Workspace
from app.models.user import User

workspaces_bp = Blueprint("workspaces", __name__, url_prefix="/api/workspaces")


def _get_current_user():
    uid = get_jwt_identity()
    return User.query.get(uid)


@workspaces_bp.route("", methods=["GET"])
@jwt_required()
def list_workspaces():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    workspaces = Workspace.query.filter_by(owner_id=user.id).order_by(Workspace.created_at).all()
    return jsonify({"workspaces": [w.to_dict() for w in workspaces]}), 200


@workspaces_bp.route("", methods=["POST"])
@jwt_required()
def create_workspace():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 422

    workspace = Workspace(
        name=name[:200],
        icon=data.get("icon", "📓"),
        owner_id=user.id,
    )
    db.session.add(workspace)
    db.session.commit()
    return jsonify({"workspace": workspace.to_dict()}), 201


@workspaces_bp.route("/<string:wid>", methods=["GET"])
@jwt_required()
def get_workspace(wid):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    workspace = Workspace.query.filter_by(id=wid, owner_id=user.id).first()
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    return jsonify({"workspace": workspace.to_dict()}), 200


@workspaces_bp.route("/<string:wid>", methods=["PUT"])
@jwt_required()
def update_workspace(wid):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    workspace = Workspace.query.filter_by(id=wid, owner_id=user.id).first()
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data and data["name"]:
        workspace.name = data["name"][:200]
    if "icon" in data:
        workspace.icon = data["icon"][:10] if data["icon"] else "📓"

    db.session.commit()
    return jsonify({"workspace": workspace.to_dict()}), 200


@workspaces_bp.route("/<string:wid>", methods=["DELETE"])
@jwt_required()
def delete_workspace(wid):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    workspace = Workspace.query.filter_by(id=wid, owner_id=user.id).first()
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    db.session.delete(workspace)
    db.session.commit()
    return jsonify({"message": "Workspace deleted"}), 200
