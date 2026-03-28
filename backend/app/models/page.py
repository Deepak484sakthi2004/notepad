import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.tag import page_tags

page_favourites = db.Table(
    "page_favourites",
    db.Column(
        "user_id",
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "page_id",
        db.String(36),
        db.ForeignKey("pages.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Page(db.Model):
    __tablename__ = "pages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = db.Column(
        db.String(36),
        db.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_page_id = db.Column(
        db.String(36),
        db.ForeignKey("pages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(300), default="Untitled")
    icon = db.Column(db.String(10), default="📄")
    cover_image = db.Column(db.Text, nullable=True)
    blocks = db.Column(db.JSON, default=dict)
    plain_text = db.Column(db.Text, default="")
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    sort_order = db.Column(db.Float, default=0.0)
    created_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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
    workspace = db.relationship("Workspace", back_populates="pages")
    creator = db.relationship(
        "User", foreign_keys=[created_by], back_populates="pages"
    )
    children = db.relationship(
        "Page",
        foreign_keys=[parent_page_id],
        backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic",
    )
    tags = db.relationship("Tag", secondary=page_tags, back_populates="pages")
    favourited_by = db.relationship(
        "User", secondary=page_favourites, backref="favourite_pages"
    )
    flashcard_decks = db.relationship(
        "FlashcardDeck",
        foreign_keys="FlashcardDeck.source_page_id",
        back_populates="source_page",
    )

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None

    def to_dict(self, include_blocks=False, include_tags=True):
        data = {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "parent_page_id": self.parent_page_id,
            "title": self.title,
            "icon": self.icon,
            "cover_image": self.cover_image,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "sort_order": self.sort_order,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_blocks:
            data["blocks"] = self.blocks
            data["plain_text"] = self.plain_text
        if include_tags:
            data["tags"] = [t.to_dict() for t in self.tags]
        return data

    def to_tree_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "icon": self.icon,
            "parent_page_id": self.parent_page_id,
            "sort_order": self.sort_order,
            "has_children": self.children.filter_by(is_deleted=False).count() > 0,
        }

    def __repr__(self):
        return f"<Page {self.title}>"
