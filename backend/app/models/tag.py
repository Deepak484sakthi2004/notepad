import uuid
from app.extensions import db

page_tags = db.Table(
    "page_tags",
    db.Column(
        "page_id",
        db.String(36),
        db.ForeignKey("pages.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.String(36),
        db.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(50), nullable=False)
    colour = db.Column(db.String(7), default="#6366f1")
    created_by = db.Column(
        db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    workspace = db.relationship("Workspace", back_populates="tags")
    pages = db.relationship("Page", secondary=page_tags, back_populates="tags")

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "colour": self.colour,
            "created_by": self.created_by,
        }

    def __repr__(self):
        return f"<Tag {self.name}>"
