"""Orchestrates AI flashcard generation and persists results."""
import uuid
import logging
from datetime import datetime, timezone
from flask import current_app
from app.extensions import db
from app.models.flashcard import Flashcard, FlashcardDeck, AIGenerationLog
from app.models.page import Page
from app.services.ai_service import generate_flashcards_from_text
from app.utils.text_extractor import extract_text_from_blocks, truncate_text

logger = logging.getLogger(__name__)


def generate_deck_for_page(
    page: Page,
    user_id: str,
    num_cards: int = 10,
    deck_name: str = None,
) -> FlashcardDeck:
    """Generate a flashcard deck from a page's content."""
    plain_text = page.plain_text or extract_text_from_blocks(page.blocks)
    plain_text = truncate_text(plain_text, max_chars=8000)

    if not plain_text.strip():
        raise ValueError("Page has no content to generate flashcards from.")

    topic = page.title or "this subject"
    name = deck_name or f"Flashcards – {page.title}"

    # Create deck
    deck = FlashcardDeck(
        user_id=user_id,
        source_page_id=page.id,
        name=name,
        auto_generated=True,
    )
    db.session.add(deck)
    db.session.flush()

    # Log entry
    log = AIGenerationLog(
        user_id=user_id,
        page_id=page.id,
        deck_id=deck.id,
        status="pending",
    )
    db.session.add(log)
    db.session.flush()

    try:
        cards_data, usage = generate_flashcards_from_text(plain_text, topic, num_cards)

        for card_data in cards_data:
            card = Flashcard(
                deck_id=deck.id,
                question=card_data.get("question", ""),
                answer=card_data.get("answer", ""),
                difficulty=int(card_data.get("difficulty", 2)),
                question_type=card_data.get("question_type", "recall"),
                source_snippet=card_data.get("source_snippet"),
                mcq_options=card_data.get("mcq_options"),
                ai_generated=True,
            )
            db.session.add(card)

        log.status = "success"
        log.prompt_tokens = usage.get("prompt_tokens", 0)
        log.completion_tokens = usage.get("completion_tokens", 0)
        log.model = usage.get("model", "gpt-4o")
        db.session.commit()

        return deck

    except Exception as exc:
        log.status = "error"
        log.error_message = str(exc)[:500]
        db.session.commit()
        raise


def regenerate_deck(deck: FlashcardDeck, num_cards: int = 10) -> FlashcardDeck:
    """Delete existing cards in a deck and regenerate from source page."""
    if not deck.source_page_id:
        raise ValueError("Deck has no source page to regenerate from.")

    page = Page.query.get(deck.source_page_id)
    if not page:
        raise ValueError("Source page not found.")

    # Remove old cards
    Flashcard.query.filter_by(deck_id=deck.id).delete()
    db.session.flush()

    plain_text = page.plain_text or extract_text_from_blocks(page.blocks)
    plain_text = truncate_text(plain_text, max_chars=8000)
    topic = page.title or "this subject"

    log = AIGenerationLog(
        user_id=deck.user_id,
        page_id=page.id,
        deck_id=deck.id,
        status="pending",
    )
    db.session.add(log)
    db.session.flush()

    try:
        cards_data, usage = generate_flashcards_from_text(plain_text, topic, num_cards)

        for card_data in cards_data:
            card = Flashcard(
                deck_id=deck.id,
                question=card_data.get("question", ""),
                answer=card_data.get("answer", ""),
                difficulty=int(card_data.get("difficulty", 2)),
                question_type=card_data.get("question_type", "recall"),
                source_snippet=card_data.get("source_snippet"),
                mcq_options=card_data.get("mcq_options"),
                ai_generated=True,
            )
            db.session.add(card)

        deck.updated_at = datetime.now(timezone.utc)
        log.status = "success"
        log.prompt_tokens = usage.get("prompt_tokens", 0)
        log.completion_tokens = usage.get("completion_tokens", 0)
        log.model = usage.get("model", "gpt-4o")
        db.session.commit()
        return deck

    except Exception as exc:
        log.status = "error"
        log.error_message = str(exc)[:500]
        db.session.commit()
        raise
