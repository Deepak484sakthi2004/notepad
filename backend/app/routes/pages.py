from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import io
from app.extensions import db
from app.models.page import Page, page_favourites
from app.models.workspace import Workspace
from app.models.user import User
from app.services.page_service import (
    create_page,
    duplicate_page,
    export_page_markdown,
    export_page_pdf,
    export_page_txt,
    get_pages_tree,
    handle_image_upload,
    move_page,
    update_page_content,
)
from app.utils.text_extractor import extract_text_from_blocks

pages_bp = Blueprint("pages", __name__)


def _current_user():
    return User.query.get(get_jwt_identity())


def _assert_workspace_access(workspace_id: str, user_id: str):
    ws = Workspace.query.filter_by(id=workspace_id, owner_id=user_id).first()
    if not ws:
        return None
    return ws


def _assert_page_access(page_id: str, user_id: str):
    page = Page.query.get(page_id)
    if not page:
        return None, None
    ws = _assert_workspace_access(page.workspace_id, user_id)
    if not ws:
        return None, None
    return page, ws


# ── Workspace-scoped page list ────────────────────────────────────────────────

@pages_bp.route("/api/workspaces/<string:wid>/pages", methods=["GET"])
@jwt_required()
def list_pages(wid):
    user = _current_user()
    if not _assert_workspace_access(wid, user.id):
        return jsonify({"error": "Workspace not found"}), 404
    tree = get_pages_tree(wid, user.id)
    return jsonify({"pages": tree}), 200


@pages_bp.route("/api/workspaces/<string:wid>/pages", methods=["POST"])
@jwt_required()
def create_page_route(wid):
    user = _current_user()
    if not _assert_workspace_access(wid, user.id):
        return jsonify({"error": "Workspace not found"}), 404

    data = request.get_json(silent=True) or {}
    page = create_page(
        workspace_id=wid,
        user_id=user.id,
        title=data.get("title", "Untitled"),
        parent_page_id=data.get("parent_page_id"),
        icon=data.get("icon", "📄"),
    )
    return jsonify({"page": page.to_dict(include_blocks=True)}), 201


# ── Single page operations ─────────────────────────────────────────────────────

@pages_bp.route("/api/pages/<string:page_id>", methods=["GET"])
@jwt_required()
def get_page(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    return jsonify({"page": page.to_dict(include_blocks=True)}), 200


@pages_bp.route("/api/pages/<string:page_id>", methods=["PUT"])
@jwt_required()
def update_page(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404

    data = request.get_json(silent=True) or {}
    if "title" in data:
        page.title = (data["title"] or "Untitled")[:300]
    if "icon" in data:
        page.icon = (data["icon"] or "📄")[:10]
    if "cover_image" in data:
        page.cover_image = data["cover_image"]
    db.session.commit()
    return jsonify({"page": page.to_dict(include_blocks=True)}), 200


@pages_bp.route("/api/pages/<string:page_id>/content", methods=["PUT"])
@jwt_required()
def update_page_content_route(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404

    data = request.get_json(silent=True) or {}
    blocks = data.get("blocks", {})
    plain_text = data.get("plain_text") or extract_text_from_blocks(blocks)
    update_page_content(page, blocks, plain_text)
    return jsonify({"page": page.to_dict(include_blocks=True)}), 200


@pages_bp.route("/api/pages/<string:page_id>", methods=["DELETE"])
@jwt_required()
def soft_delete_page(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    page.soft_delete()
    db.session.commit()
    return jsonify({"message": "Page moved to trash"}), 200


@pages_bp.route("/api/pages/<string:page_id>/restore", methods=["POST"])
@jwt_required()
def restore_page(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    page.restore()
    db.session.commit()
    return jsonify({"page": page.to_dict()}), 200


@pages_bp.route("/api/pages/<string:page_id>/permanent", methods=["DELETE"])
@jwt_required()
def permanent_delete_page(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    db.session.delete(page)
    db.session.commit()
    return jsonify({"message": "Page permanently deleted"}), 200


@pages_bp.route("/api/pages/<string:page_id>/duplicate", methods=["POST"])
@jwt_required()
def duplicate_page_route(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    new_page = duplicate_page(page, user.id)
    return jsonify({"page": new_page.to_dict(include_blocks=True)}), 201


@pages_bp.route("/api/pages/<string:page_id>/move", methods=["POST"])
@jwt_required()
def move_page_route(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404

    data = request.get_json(silent=True) or {}
    try:
        updated = move_page(
            page,
            new_parent_id=data.get("parent_page_id"),
            new_workspace_id=data.get("workspace_id"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    return jsonify({"page": updated.to_dict()}), 200


@pages_bp.route("/api/pages/<string:page_id>/upload-image", methods=["POST"])
@jwt_required()
def upload_image(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    try:
        url = handle_image_upload(page, file)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    return jsonify({"url": url}), 200


@pages_bp.route("/api/pages/<string:page_id>/export", methods=["GET"])
@jwt_required()
def export_page(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404

    fmt = request.args.get("format", "md").lower()
    if fmt == "md":
        content = export_page_markdown(page)
        return send_file(
            io.BytesIO(content.encode()),
            mimetype="text/markdown",
            as_attachment=True,
            download_name=f"{page.title}.md",
        )
    elif fmt == "txt":
        content = export_page_txt(page)
        return send_file(
            io.BytesIO(content.encode()),
            mimetype="text/plain",
            as_attachment=True,
            download_name=f"{page.title}.txt",
        )
    elif fmt == "pdf":
        content = export_page_pdf(page)
        return send_file(
            io.BytesIO(content),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{page.title}.pdf",
        )
    else:
        return jsonify({"error": "Unsupported format. Use md, txt, or pdf"}), 422


@pages_bp.route("/api/pages/<string:page_id>/favourite", methods=["PUT"])
@jwt_required()
def add_favourite(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    if user not in page.favourited_by:
        page.favourited_by.append(user)
        db.session.commit()
    return jsonify({"message": "Added to favourites"}), 200


@pages_bp.route("/api/pages/<string:page_id>/favourite", methods=["DELETE"])
@jwt_required()
def remove_favourite(page_id):
    user = _current_user()
    page, _ = _assert_page_access(page_id, user.id)
    if not page:
        return jsonify({"error": "Page not found"}), 404
    if user in page.favourited_by:
        page.favourited_by.remove(user)
        db.session.commit()
    return jsonify({"message": "Removed from favourites"}), 200


# ── Trash ─────────────────────────────────────────────────────────────────────

@pages_bp.route("/api/trash", methods=["GET"])
@jwt_required()
def list_trash():
    user = _current_user()
    workspace_id = request.args.get("workspace_id")

    query = (
        Page.query.join(Workspace, Page.workspace_id == Workspace.id)
        .filter(Workspace.owner_id == user.id, Page.is_deleted == True)
    )
    if workspace_id:
        query = query.filter(Page.workspace_id == workspace_id)

    pages = query.order_by(Page.deleted_at.desc()).all()
    return jsonify({"pages": [p.to_dict() for p in pages]}), 200


# ── Favourites ─────────────────────────────────────────────────────────────────

@pages_bp.route("/api/favourites", methods=["GET"])
@jwt_required()
def list_favourites():
    user = _current_user()
    workspace_id = request.args.get("workspace_id")

    favs = user.favourite_pages
    if workspace_id:
        favs = [p for p in favs if p.workspace_id == workspace_id and not p.is_deleted]
    else:
        favs = [p for p in favs if not p.is_deleted]

    return jsonify({"pages": [p.to_dict() for p in favs]}), 200
