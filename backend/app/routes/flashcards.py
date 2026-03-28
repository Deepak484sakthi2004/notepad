from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.flashcard import Flashcard, FlashcardDeck
from app.models.review import FlashcardReview, StudySession
from app.models.page import Page
from app.models.user import User
from app.models.workspace import Workspace
from app.services.generation_service import generate_deck_for_page, regenerate_deck
from app.services.spaced_repetition import compute_next_review

flashcards_bp = Blueprint("flashcards", __name__, url_prefix="/api/flashcards")


def _is_due(next_review_at, now):
    """Compare next_review_at to now, handling both naive and aware datetimes."""
    if next_review_at is None:
        return True
    if next_review_at.tzinfo is None:
        # SQLite returns naive datetimes; compare against naive now
        return next_review_at <= now.replace(tzinfo=None)
    return next_review_at <= now


def _uid():
    return get_jwt_identity()


def _user():
    return User.query.get(_uid())


def _assert_deck(deck_id, user_id):
    return FlashcardDeck.query.filter_by(id=deck_id, user_id=user_id).first()


# ── Decks ──────────────────────────────────────────────────────────────────────

@flashcards_bp.route("/decks", methods=["GET"])
@jwt_required()
def list_decks():
    decks = FlashcardDeck.query.filter_by(user_id=_uid()).order_by(FlashcardDeck.updated_at.desc()).all()
    return jsonify({"decks": [d.to_dict() for d in decks]}), 200


@flashcards_bp.route("/decks", methods=["POST"])
@jwt_required()
def create_deck():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 422

    deck = FlashcardDeck(
        user_id=_uid(),
        source_page_id=data.get("source_page_id"),
        name=name[:200],
        description=data.get("description", ""),
        auto_generated=False,
    )
    db.session.add(deck)
    db.session.commit()
    return jsonify({"deck": deck.to_dict()}), 201


@flashcards_bp.route("/decks/<string:deck_id>", methods=["GET"])
@jwt_required()
def get_deck(deck_id):
    deck = _assert_deck(deck_id, _uid())
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    return jsonify({"deck": deck.to_dict()}), 200


@flashcards_bp.route("/decks/<string:deck_id>", methods=["PUT"])
@jwt_required()
def update_deck(deck_id):
    deck = _assert_deck(deck_id, _uid())
    if not deck:
        return jsonify({"error": "Deck not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data and data["name"]:
        deck.name = data["name"][:200]
    if "description" in data:
        deck.description = data["description"]
    db.session.commit()
    return jsonify({"deck": deck.to_dict()}), 200


@flashcards_bp.route("/decks/<string:deck_id>", methods=["DELETE"])
@jwt_required()
def delete_deck(deck_id):
    deck = _assert_deck(deck_id, _uid())
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    db.session.delete(deck)
    db.session.commit()
    return jsonify({"message": "Deck deleted"}), 200


@flashcards_bp.route("/decks/<string:deck_id>/regenerate", methods=["POST"])
@jwt_required()
def regenerate_deck_route(deck_id):
    deck = _assert_deck(deck_id, _uid())
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    try:
        data = request.get_json(silent=True) or {}
        num = int(data.get("num_cards", 10))
        updated = regenerate_deck(deck, num_cards=num)
        return jsonify({"deck": updated.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:
        return jsonify({"error": f"Generation failed: {str(exc)}"}), 500


@flashcards_bp.route("/decks/<string:deck_id>/stats", methods=["GET"])
@jwt_required()
def deck_stats(deck_id):
    uid = _uid()
    deck = _assert_deck(deck_id, uid)
    if not deck:
        return jsonify({"error": "Deck not found"}), 404

    cards = deck.cards
    total = len(cards)
    now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)

    due_ids = {c.id for c in cards}
    # Cards with a future next_review_at are NOT due
    reviewed = (
        FlashcardReview.query.filter(
            FlashcardReview.user_id == uid,
            FlashcardReview.flashcard_id.in_([c.id for c in cards]),
            FlashcardReview.next_review_at > now_naive,
        )
        .with_entities(FlashcardReview.flashcard_id)
        .all()
    )
    not_due_ids = {r.flashcard_id for r in reviewed}
    due_count = len(due_ids - not_due_ids)

    return jsonify({
        "total": total,
        "due": due_count,
        "deck_id": deck_id,
    }), 200


# ── Cards ──────────────────────────────────────────────────────────────────────

@flashcards_bp.route("/decks/<string:deck_id>/cards", methods=["GET"])
@jwt_required()
def list_cards(deck_id):
    deck = _assert_deck(deck_id, _uid())
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    cards = Flashcard.query.filter_by(deck_id=deck_id).order_by(Flashcard.created_at).all()
    return jsonify({"cards": [c.to_dict() for c in cards]}), 200


@flashcards_bp.route("/decks/<string:deck_id>/cards", methods=["POST"])
@jwt_required()
def create_card(deck_id):
    deck = _assert_deck(deck_id, _uid())
    if not deck:
        return jsonify({"error": "Deck not found"}), 404

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()
    if not question or not answer:
        return jsonify({"error": "question and answer are required"}), 422

    card = Flashcard(
        deck_id=deck_id,
        question=question,
        answer=answer,
        difficulty=int(data.get("difficulty", 2)),
        question_type=data.get("question_type", "recall"),
        source_snippet=data.get("source_snippet"),
        ai_generated=False,
    )
    db.session.add(card)
    db.session.commit()
    return jsonify({"card": card.to_dict()}), 201


@flashcards_bp.route("/cards/<string:card_id>", methods=["PUT"])
@jwt_required()
def update_card(card_id):
    uid = _uid()
    card = Flashcard.query.get(card_id)
    if not card or card.deck.user_id != uid:
        return jsonify({"error": "Card not found"}), 404

    data = request.get_json(silent=True) or {}
    if "question" in data and data["question"]:
        card.question = data["question"]
    if "answer" in data and data["answer"]:
        card.answer = data["answer"]
    if "difficulty" in data:
        card.difficulty = int(data["difficulty"])
    if "question_type" in data:
        card.question_type = data["question_type"]

    db.session.commit()
    return jsonify({"card": card.to_dict()}), 200


@flashcards_bp.route("/cards/<string:card_id>", methods=["DELETE"])
@jwt_required()
def delete_card(card_id):
    uid = _uid()
    card = Flashcard.query.get(card_id)
    if not card or card.deck.user_id != uid:
        return jsonify({"error": "Card not found"}), 404
    db.session.delete(card)
    db.session.commit()
    return jsonify({"message": "Card deleted"}), 200


@flashcards_bp.route("/cards/<string:card_id>/suspend", methods=["POST"])
@jwt_required()
def suspend_card(card_id):
    uid = _uid()
    card = Flashcard.query.get(card_id)
    if not card or card.deck.user_id != uid:
        return jsonify({"error": "Card not found"}), 404
    card.is_suspended = not card.is_suspended
    db.session.commit()
    return jsonify({"card": card.to_dict()}), 200


@flashcards_bp.route("/cards/<string:card_id>/flag", methods=["POST"])
@jwt_required()
def flag_card(card_id):
    uid = _uid()
    card = Flashcard.query.get(card_id)
    if not card or card.deck.user_id != uid:
        return jsonify({"error": "Card not found"}), 404
    card.is_flagged = not card.is_flagged
    db.session.commit()
    return jsonify({"card": card.to_dict()}), 200


# ── Generation ─────────────────────────────────────────────────────────────────

@flashcards_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_flashcards():
    uid = _uid()
    data = request.get_json(silent=True) or {}
    page_id = data.get("page_id")
    if not page_id:
        return jsonify({"error": "page_id is required"}), 422

    page = Page.query.get(page_id)
    if not page:
        return jsonify({"error": "Page not found"}), 404

    ws = Workspace.query.filter_by(id=page.workspace_id, owner_id=uid).first()
    if not ws:
        return jsonify({"error": "Access denied"}), 403

    num_cards = int(data.get("num_cards", 10))
    deck_name = data.get("deck_name")

    try:
        deck = generate_deck_for_page(page, uid, num_cards=num_cards, deck_name=deck_name)
        return jsonify({"deck": deck.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:
        return jsonify({"error": f"Generation failed: {str(exc)}"}), 500


# ── Due cards ──────────────────────────────────────────────────────────────────

@flashcards_bp.route("/due", methods=["GET"])
@jwt_required()
def due_cards_all():
    uid = _uid()
    now = datetime.now(timezone.utc)
    decks = FlashcardDeck.query.filter_by(user_id=uid).all()
    due = []
    for deck in decks:
        for card in deck.cards:
            if card.is_suspended:
                continue
            last_review = (
                FlashcardReview.query.filter_by(flashcard_id=card.id, user_id=uid)
                .order_by(FlashcardReview.reviewed_at.desc())
                .first()
            )
            if not last_review or _is_due(last_review.next_review_at, now):
                due.append(card.to_dict())
    return jsonify({"cards": due, "count": len(due)}), 200


@flashcards_bp.route("/decks/<string:deck_id>/due", methods=["GET"])
@jwt_required()
def due_cards_deck(deck_id):
    uid = _uid()
    deck = _assert_deck(deck_id, uid)
    if not deck:
        return jsonify({"error": "Deck not found"}), 404

    now = datetime.now(timezone.utc)
    due = []
    for card in deck.cards:
        if card.is_suspended:
            continue
        last_review = (
            FlashcardReview.query.filter_by(flashcard_id=card.id, user_id=uid)
            .order_by(FlashcardReview.reviewed_at.desc())
            .first()
        )
        if not last_review or _is_due(last_review.next_review_at, now):
            due.append(card.to_dict())

    return jsonify({"cards": due, "count": len(due)}), 200


# ── Review ─────────────────────────────────────────────────────────────────────

@flashcards_bp.route("/review", methods=["POST"])
@jwt_required()
def submit_review():
    uid = _uid()
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    quality = data.get("quality")
    session_id = data.get("session_id")

    if card_id is None or quality is None:
        return jsonify({"error": "card_id and quality are required"}), 422

    card = Flashcard.query.get(card_id)
    if not card or card.deck.user_id != uid:
        return jsonify({"error": "Card not found"}), 404

    # Get last review state
    last = (
        FlashcardReview.query.filter_by(flashcard_id=card_id, user_id=uid)
        .order_by(FlashcardReview.reviewed_at.desc())
        .first()
    )
    ef = last.ease_factor if last else 2.5
    interval = last.interval_days if last else 1
    reps = last.repetitions if last else 0

    new_ef, new_interval, new_reps, next_review = compute_next_review(
        int(quality), ef, interval, reps
    )

    review = FlashcardReview(
        flashcard_id=card_id,
        user_id=uid,
        session_id=session_id,
        quality=int(quality),
        ease_factor=new_ef,
        interval_days=new_interval,
        repetitions=new_reps,
        next_review_at=next_review,
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"review": review.to_dict()}), 201


# ── Sessions ───────────────────────────────────────────────────────────────────

@flashcards_bp.route("/sessions/start", methods=["POST"])
@jwt_required()
def start_session():
    data = request.get_json(silent=True) or {}
    session = StudySession(
        user_id=_uid(),
        deck_id=data.get("deck_id"),
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({"session": session.to_dict()}), 201


@flashcards_bp.route("/sessions/<string:session_id>/end", methods=["POST"])
@jwt_required()
def end_session(session_id):
    uid = _uid()
    session = StudySession.query.filter_by(id=session_id, user_id=uid).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json(silent=True) or {}
    session.ended_at = datetime.now(timezone.utc)
    session.cards_reviewed = int(data.get("cards_reviewed", 0))
    session.cards_correct = int(data.get("cards_correct", 0))
    db.session.commit()
    return jsonify({"session": session.to_dict()}), 200


# ── Ask AI ─────────────────────────────────────────────────────────────────────

@flashcards_bp.route("/ask", methods=["POST"])
@jwt_required()
def ask_ai():
    uid = _uid()
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    question = (data.get("question") or "").strip()

    if not card_id or not question:
        return jsonify({"error": "card_id and question are required"}), 422

    card = Flashcard.query.get(card_id)
    if not card or card.deck.user_id != uid:
        return jsonify({"error": "Card not found"}), 404

    try:
        from app.services.ai_service import ask_ai_about_card
        answer = ask_ai_about_card(question, card.question, card.answer)
        return jsonify({"answer": answer}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Stats ──────────────────────────────────────────────────────────────────────

@flashcards_bp.route("/stats/overview", methods=["GET"])
@jwt_required()
def stats_overview():
    uid = _uid()
    now = datetime.now(timezone.utc)

    decks = FlashcardDeck.query.filter_by(user_id=uid).all()
    total_decks = len(decks)
    total_cards = sum(len(d.cards) for d in decks)

    # Due today
    due_count = 0
    for deck in decks:
        for card in deck.cards:
            if card.is_suspended:
                continue
            last = (
                FlashcardReview.query.filter_by(flashcard_id=card.id, user_id=uid)
                .order_by(FlashcardReview.reviewed_at.desc())
                .first()
            )
            if not last or _is_due(last.next_review_at, now):
                due_count += 1

    total_reviews = FlashcardReview.query.filter_by(user_id=uid).count()
    correct = FlashcardReview.query.filter(
        FlashcardReview.user_id == uid, FlashcardReview.quality >= 3
    ).count()

    accuracy = round((correct / total_reviews * 100), 1) if total_reviews > 0 else 0.0

    return jsonify({
        "total_decks": total_decks,
        "total_cards": total_cards,
        "due_today": due_count,
        "total_reviews": total_reviews,
        "accuracy": accuracy,
    }), 200


@flashcards_bp.route("/stats/history", methods=["GET"])
@jwt_required()
def stats_history():
    uid = _uid()
    days = int(request.args.get("days", 30))
    from datetime import timedelta

    since = datetime.now(timezone.utc) - timedelta(days=days)
    reviews = (
        FlashcardReview.query.filter(
            FlashcardReview.user_id == uid,
            FlashcardReview.reviewed_at >= since,
        )
        .order_by(FlashcardReview.reviewed_at)
        .all()
    )

    # Group by date
    by_date: dict = {}
    for r in reviews:
        date_str = r.reviewed_at.date().isoformat()
        if date_str not in by_date:
            by_date[date_str] = {"date": date_str, "total": 0, "correct": 0}
        by_date[date_str]["total"] += 1
        if r.quality >= 3:
            by_date[date_str]["correct"] += 1

    return jsonify({"history": list(by_date.values())}), 200


# ── User profile ───────────────────────────────────────────────────────────────

@flashcards_bp.route("/user/profile", methods=["GET"], endpoint="user_profile_get")
@jwt_required()
def get_profile():
    user = _user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@flashcards_bp.route("/user/profile", methods=["PUT"], endpoint="user_profile_put")
@jwt_required()
def update_profile():
    user = _user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data and data["name"]:
        user.name = data["name"][:100]
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"]

    db.session.commit()
    return jsonify({"user": user.to_dict()}), 200
