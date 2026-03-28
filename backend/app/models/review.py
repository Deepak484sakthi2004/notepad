import uuid
from datetime import datetime, timezone
from app.extensions import db


class FlashcardReview(db.Model):
    __tablename__ = "flashcard_reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flashcard_id = db.Column(
        db.String(36),
        db.ForeignKey("flashcards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = db.Column(db.String(36), nullable=True, index=True)
    quality = db.Column(db.SmallInteger, nullable=False)  # 0-5
    ease_factor = db.Column(db.Float, default=2.5)
    interval_days = db.Column(db.Integer, default=1)
    repetitions = db.Column(db.SmallInteger, default=0, nullable=False)
    next_review_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reviewed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    flashcard = db.relationship("Flashcard", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "flashcard_id": self.flashcard_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "quality": self.quality,
            "ease_factor": self.ease_factor,
            "interval_days": self.interval_days,
            "repetitions": self.repetitions,
            "next_review_at": (
                self.next_review_at.isoformat() if self.next_review_at else None
            ),
            "reviewed_at": (
                self.reviewed_at.isoformat() if self.reviewed_at else None
            ),
        }

    def __repr__(self):
        return f"<FlashcardReview card={self.flashcard_id} q={self.quality}>"


class StudySession(db.Model):
    __tablename__ = "study_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deck_id = db.Column(
        db.String(36),
        db.ForeignKey("flashcard_decks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cards_reviewed = db.Column(db.Integer, default=0)
    cards_correct = db.Column(db.Integer, default=0)

    # Relationships
    deck = db.relationship("FlashcardDeck", back_populates="sessions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "cards_reviewed": self.cards_reviewed,
            "cards_correct": self.cards_correct,
        }

    def __repr__(self):
        return f"<StudySession {self.id}>"
