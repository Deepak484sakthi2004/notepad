import uuid
from datetime import datetime, timezone
from app.extensions import db


class FlashcardDeck(db.Model):
    __tablename__ = "flashcard_decks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_page_id = db.Column(
        db.String(36),
        db.ForeignKey("pages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    auto_generated = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="flashcard_decks")
    source_page = db.relationship(
        "Page", foreign_keys=[source_page_id], back_populates="flashcard_decks"
    )
    cards = db.relationship(
        "Flashcard", back_populates="deck", cascade="all, delete-orphan"
    )
    sessions = db.relationship(
        "StudySession", back_populates="deck", cascade="all, delete-orphan"
    )

    def to_dict(self, include_card_count=True):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "source_page_id": self.source_page_id,
            "name": self.name,
            "description": self.description,
            "auto_generated": self.auto_generated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_card_count:
            data["card_count"] = len(self.cards)
        return data

    def __repr__(self):
        return f"<FlashcardDeck {self.name}>"


class Flashcard(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deck_id = db.Column(
        db.String(36),
        db.ForeignKey("flashcard_decks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.SmallInteger, default=2)
    question_type = db.Column(db.String(30), default="recall")
    source_snippet = db.Column(db.Text, nullable=True)
    mcq_options = db.Column(db.JSON, nullable=True)
    ai_generated = db.Column(db.Boolean, default=True)
    is_suspended = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    deck = db.relationship("FlashcardDeck", back_populates="cards")
    reviews = db.relationship(
        "FlashcardReview", back_populates="flashcard", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "deck_id": self.deck_id,
            "question": self.question,
            "answer": self.answer,
            "difficulty": self.difficulty,
            "question_type": self.question_type,
            "source_snippet": self.source_snippet,
            "mcq_options": self.mcq_options,
            "ai_generated": self.ai_generated,
            "is_suspended": self.is_suspended,
            "is_flagged": self.is_flagged,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Flashcard {self.id}>"


class AIGenerationLog(db.Model):
    __tablename__ = "ai_generation_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    page_id = db.Column(
        db.String(36), db.ForeignKey("pages.id", ondelete="SET NULL"), nullable=True
    )
    deck_id = db.Column(
        db.String(36),
        db.ForeignKey("flashcard_decks.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    model = db.Column(db.String(50), default="gpt-4o")
    status = db.Column(db.String(20), default="pending")
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "page_id": self.page_id,
            "deck_id": self.deck_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "model": self.model,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
