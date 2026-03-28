from app.routes.auth import auth_bp
from app.routes.workspaces import workspaces_bp
from app.routes.pages import pages_bp
from app.routes.tags import tags_bp
from app.routes.search import search_bp
from app.routes.flashcards import flashcards_bp
from app.routes.ai import ai_bp

__all__ = [
    "auth_bp",
    "workspaces_bp",
    "pages_bp",
    "tags_bp",
    "search_bp",
    "flashcards_bp",
    "ai_bp",
]
