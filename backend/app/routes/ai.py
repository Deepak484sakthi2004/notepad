from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.page import Page
from app.models.workspace import Workspace
from app.services.ai_service import ask_ai_about_card

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.route("/ask", methods=["POST"])
@jwt_required()
def ask():
    uid = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    context = (data.get("context") or "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 422

    try:
        from openai import OpenAI
        from flask import current_app

        client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
        model = current_app.config.get("OPENAI_MODEL", "gpt-4o")

        system = (
            "You are a knowledgeable study assistant helping a student understand their notes. "
            "Answer questions clearly and concisely, relating to the note context when provided."
        )
        user_msg = f"Context from my notes:\n{context}\n\nQuestion: {question}" if context else question

        response = client.chat.completions.create(
            model=model,
            max_tokens=600,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
        )
        answer = response.choices[0].message.content.strip()
        return jsonify({"answer": answer}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
