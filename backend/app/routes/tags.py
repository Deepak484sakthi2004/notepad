from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.tag import Tag
from app.models.page import Page
from app.models.workspace import Workspace
from app.models.user import User
from app.utils.validators import validate_hex_color

tags_bp = Blueprint("tags", __name__)


def _current_user():
    return User.query.get(get_jwt_identity())


def _assert_workspace(wid, user_id):
    return Workspace.query.filter_by(id=wid, owner_id=user_id).first()


@tags_bp.route("/api/workspaces/<string:wid>/tags", methods=["GET"])
@jwt_required()
def list_tags(wid):
    user = _current_user()
    if not _assert_workspace(wid, user.id):
        return jsonify({"error": "Workspace not found"}), 404
    tags = Tag.query.filter_by(workspace_id=wid).all()
    return jsonify({"tags": [t.to_dict() for t in tags]}), 200


@tags_bp.route("/api/workspaces/<string:wid>/tags", methods=["POST"])
@jwt_required()
def create_tag(wid):
    user = _current_user()
    if not _assert_workspace(wid, user.id):
        return jsonify({"error": "Workspace not found"}), 404

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 422

    colour = data.get("colour", "#6366f1")
    if not validate_hex_color(colour):
        colour = "#6366f1"

    tag = Tag(workspace_id=wid, name=name[:50], colour=colour, created_by=user.id)
    db.session.add(tag)
    db.session.commit()
    return jsonify({"tag": tag.to_dict()}), 201


@tags_bp.route("/api/tags/<string:tag_id>", methods=["PUT"])
@jwt_required()
def update_tag(tag_id):
    user = _current_user()
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({"error": "Tag not found"}), 404
    if not _assert_workspace(tag.workspace_id, user.id):
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    if "name" in data and data["name"]:
        tag.name = data["name"][:50]
    if "colour" in data and validate_hex_color(data["colour"]):
        tag.colour = data["colour"]

    db.session.commit()
    return jsonify({"tag": tag.to_dict()}), 200


@tags_bp.route("/api/tags/<string:tag_id>", methods=["DELETE"])
@jwt_required()
def delete_tag(tag_id):
    user = _current_user()
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({"error": "Tag not found"}), 404
    if not _assert_workspace(tag.workspace_id, user.id):
        return jsonify({"error": "Access denied"}), 403

    db.session.delete(tag)
    db.session.commit()
    return jsonify({"message": "Tag deleted"}), 200


@tags_bp.route("/api/pages/<string:page_id>/tags", methods=["POST"])
@jwt_required()
def add_page_tag(page_id):
    user = _current_user()
    page = Page.query.get(page_id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    if not Workspace.query.filter_by(id=page.workspace_id, owner_id=user.id).first():
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    tag_id = data.get("tag_id")
    if not tag_id:
        return jsonify({"error": "tag_id is required"}), 422

    tag = Tag.query.filter_by(id=tag_id, workspace_id=page.workspace_id).first()
    if not tag:
        return jsonify({"error": "Tag not found in workspace"}), 404

    if tag not in page.tags:
        page.tags.append(tag)
        db.session.commit()

    return jsonify({"tags": [t.to_dict() for t in page.tags]}), 200


@tags_bp.route("/api/pages/<string:page_id>/tags/<string:tag_id>", methods=["DELETE"])
@jwt_required()
def remove_page_tag(page_id, tag_id):
    user = _current_user()
    page = Page.query.get(page_id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    if not Workspace.query.filter_by(id=page.workspace_id, owner_id=user.id).first():
        return jsonify({"error": "Access denied"}), 403

    tag = Tag.query.get(tag_id)
    if tag and tag in page.tags:
        page.tags.remove(tag)
        db.session.commit()

    return jsonify({"tags": [t.to_dict() for t in page.tags]}), 200
