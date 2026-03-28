"""
Pytest fixtures for the NoteSpace backend test suite.

All fixtures use an in-memory SQLite database so no real Postgres or Redis
connection is required.  External services (Redis, mail) are either disabled
via config or patched at the module level before the app is created.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Test configuration – applied BEFORE create_app() is called
# ---------------------------------------------------------------------------

class TestConfig:
    TESTING = True
    DEBUG = False

    # Use SQLite in-memory for all tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Disable the pool options that are Postgres-specific
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # JWT
    JWT_SECRET_KEY = "test-secret-key"
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_CSRF_PROTECT = False

    # General Flask secret
    SECRET_KEY = "test-secret"

    # Disable Redis – tests that need it will patch manually
    REDIS_URL = None

    # Mail – suppress all sends
    MAIL_SUPPRESS_SEND = True
    MAIL_SERVER = "localhost"
    MAIL_DEFAULT_SENDER = "test@notespace.app"

    # Rate limiting – disable so tests are not throttled
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"

    # CSRF
    WTF_CSRF_ENABLED = False

    # OpenAI – intentionally empty so no real calls happen
    OPENAI_API_KEY = "test-openai-key"
    OPENAI_MODEL = "gpt-4o"
    OPENAI_MAX_TOKENS = 200

    UPLOAD_FOLDER = "/tmp/notespace_test_uploads"
    CORS_ORIGINS = ["http://localhost:5173"]


# ---------------------------------------------------------------------------
# app fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing (session-scoped)."""
    # Patch init_redis so the app factory never tries to connect to Redis
    with patch("app.extensions.init_redis", return_value=MagicMock()):
        from app import create_app
        flask_app = create_app(config_class=TestConfig)

    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    yield flask_app


# ---------------------------------------------------------------------------
# client fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(app):
    """Flask test client."""
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# db fixture  – clean tables for every test
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(app):
    """
    Provide a clean database for each test.

    Creates all tables before the test and drops them afterwards so that
    each test starts with a completely empty schema.
    """
    from app.extensions import db as _db
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


# ---------------------------------------------------------------------------
# test_user fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_user(db, app):
    """Return a persisted User object."""
    from app.models.user import User
    with app.app_context():
        user = User(name="Test User", email="testuser@example.com")
        user.set_password("Password1")
        db.session.add(user)
        db.session.commit()
        # Refresh so the object is usable outside the with-block
        db.session.refresh(user)
        yield user


# ---------------------------------------------------------------------------
# test_workspace fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_workspace(db, app, test_user):
    """Return a Workspace owned by test_user."""
    from app.models.workspace import Workspace
    with app.app_context():
        ws = Workspace(
            name="Test Workspace",
            icon="📓",
            owner_id=test_user.id,
        )
        db.session.add(ws)
        db.session.commit()
        db.session.refresh(ws)
        yield ws


# ---------------------------------------------------------------------------
# test_page fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_page(db, app, test_workspace, test_user):
    """Return a Page inside test_workspace."""
    from app.models.page import Page
    with app.app_context():
        page = Page(
            workspace_id=test_workspace.id,
            created_by=test_user.id,
            title="Test Page",
            icon="📄",
            blocks={},
            plain_text="Hello world",
        )
        db.session.add(page)
        db.session.commit()
        db.session.refresh(page)
        yield page


# ---------------------------------------------------------------------------
# test_deck fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_deck(db, app, test_page, test_user):
    """Return a FlashcardDeck linked to test_page."""
    from app.models.flashcard import FlashcardDeck
    with app.app_context():
        deck = FlashcardDeck(
            user_id=test_user.id,
            source_page_id=test_page.id,
            name="Test Deck",
            description="A test deck",
            auto_generated=False,
        )
        db.session.add(deck)
        db.session.commit()
        db.session.refresh(deck)
        yield deck


# ---------------------------------------------------------------------------
# test_card fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_card(db, app, test_deck):
    """Return a Flashcard inside test_deck."""
    from app.models.flashcard import Flashcard
    with app.app_context():
        card = Flashcard(
            deck_id=test_deck.id,
            question="What is the capital of France?",
            answer="Paris",
            difficulty=1,
            question_type="recall",
        )
        db.session.add(card)
        db.session.commit()
        db.session.refresh(card)
        yield card


# ---------------------------------------------------------------------------
# auth_headers fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_headers(client, db, app):
    """
    Register a fresh user via the /api/auth/register endpoint and return
    JWT Authorization headers for that user.
    """
    with app.app_context():
        # Patch redis_client used inside auth_service (blacklist_token / is_token_blacklisted)
        with patch("app.services.auth_service.redis_client") as mock_redis:
            mock_redis.setex = MagicMock()
            mock_redis.exists = MagicMock(return_value=0)

            resp = client.post(
                "/api/auth/register",
                json={
                    "name": "Auth User",
                    "email": "authuser@example.com",
                    "password": "Password1",
                },
            )
            # If the user already exists from a previous call just log in
            if resp.status_code not in (200, 201):
                resp = client.post(
                    "/api/auth/login",
                    json={
                        "email": "authuser@example.com",
                        "password": "Password1",
                    },
                )

            data = resp.get_json()
            token = data.get("access_token") or data.get("token")
            assert token, f"Could not obtain JWT token. Response: {data}"
            yield {"Authorization": f"Bearer {token}"}
