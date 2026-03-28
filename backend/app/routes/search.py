from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.services.search_service import search_pages

search_bp = Blueprint("search", __name__, url_prefix="/api/search")


@search_bp.route("", methods=["GET"])
@jwt_required()
def search():
    user_id = get_jwt_identity()
    q = request.args.get("q", "").strip()
    workspace_id = request.args.get("workspace_id")

    if not q:
        return jsonify({"results": []}), 200

    results = search_pages(q, user_id, workspace_id)
    return jsonify({"results": results, "query": q}), 200
