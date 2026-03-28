import uuid
from datetime import datetime, timezone
from app.extensions import db


class Workspace(db.Model):
    __tablename__ = "workspaces"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(10), default="📓")
    owner_id = db.Column(
        db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = db.relationship("User", back_populates="workspaces")
    pages = db.relationship(
        "Page", back_populates="workspace", cascade="all, delete-orphan"
    )
    tags = db.relationship(
        "Tag", back_populates="workspace", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Workspace {self.name}>"
