from sqlalchemy import or_
from app.models.page import Page
from app.models.workspace import Workspace


def db_or(*criteria):
    return or_(*criteria)


def search_pages(query: str, user_id: str, workspace_id: str = None) -> list:
    """Full-text search over page titles and plain_text."""
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip().lower()
    base = Page.query.join(
        Workspace, Page.workspace_id == Workspace.id
    ).filter(
        Workspace.owner_id == user_id,
        Page.is_deleted == False,
    )

    if workspace_id:
        base = base.filter(Page.workspace_id == workspace_id)

    # Search title and plain_text using ILIKE
    results = base.filter(
        db_or(
            Page.title.ilike(f"%{q}%"),
            Page.plain_text.ilike(f"%{q}%"),
        )
    ).order_by(Page.updated_at.desc()).limit(30).all()

    return [
        {
            "id": p.id,
            "title": p.title,
            "icon": p.icon,
            "workspace_id": p.workspace_id,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "snippet": _get_snippet(p.plain_text, q),
        }
        for p in results
    ]


def _get_snippet(text: str, query: str, context: int = 100) -> str:
    if not text:
        return ""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:200]
    start = max(0, idx - context)
    end = min(len(text), idx + len(query) + context)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet
