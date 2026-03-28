"""
Shared pytest fixtures for NoteSpace integration tests.

Every test gets a fresh in-memory SQLite database so no Postgres or Redis
connection is needed.  Redis calls are intercepted by a fakeredis server
and mail sending is suppressed.
"""
import pytest
from unittest.mock import MagicMock, patch
import fakeredis


# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------

class IntegrationTestConfig:
    TESTING = True
    DEBUG = False

    # SQLite in-memory – recreated for every test via the db fixture
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Disable Postgres-specific pool options
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # JWT – header-only so we don't have to deal with cookie transport
    JWT_SECRET_KEY = "test-secret-key"
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_REFRESH_COOKIE_PATH = "/api/auth/refresh"

    # Flask secret
    SECRET_KEY = "test-secret"

    # Mail – never actually send
    MAIL_SUPPRESS_SEND = True
    MAIL_SERVER = "localhost"
    MAIL_DEFAULT_SENDER = "test@notespace.app"

    # Rate limiting – disabled entirely
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"

    # CSRF
    WTF_CSRF_ENABLED = False

    # OpenAI – empty key so no real calls happen
    OPENAI_API_KEY = "test-openai-key"
    OPENAI_MODEL = "gpt-4o"
    OPENAI_MAX_TOKENS = 200

    UPLOAD_FOLDER = "/tmp/notespace_test_uploads"
    CORS_ORIGINS = ["http://localhost:5173"]

    # Redis placeholder (real fakeredis is injected via fixture)
    REDIS_URL = "redis://localhost:6379/0"


# ---------------------------------------------------------------------------
# session-scoped app
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """
    Create a Flask application for the integration test session.

    init_redis is patched so the factory never opens a real Redis socket.
    After the app is created we swap the global redis_client for a
    fakeredis instance so token-blacklist logic works without a real server.
    """
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    with patch("app.extensions.init_redis", return_value=fake_redis):
        from app import create_app
        flask_app = create_app(config_class=IntegrationTestConfig)

    # Inject fakeredis into every module that imported redis_client directly
    import app.extensions as _ext
    _ext.redis_client = fake_redis

    import app.services.auth_service as _auth_svc
    _auth_svc.redis_client = fake_redis

    yield flask_app


# ---------------------------------------------------------------------------
# Per-test: clean tables
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(app):
    """
    Provide a freshly created schema for a single test.

    All tables are created before the test and dropped after so that
    every test starts with a completely empty database.
    """
    from app.extensions import db as _db
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


# ---------------------------------------------------------------------------
# Per-test: Flask test client
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(app, db):
    """Return a Flask test client backed by a clean database."""
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Helper used by many tests
# ---------------------------------------------------------------------------

def register_and_login(client, email="test@example.com", password="Password123",
                       name="Test User"):
    """
    Register *and* log in a user, returning Authorization headers.

    If the user already exists (409), falls back to login directly.
    """
    reg = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    if reg.status_code == 201:
        token = reg.get_json()["access_token"]
    else:
        login = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        token = login.get_json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def get_default_workspace(client, headers):
    """Return the first workspace created for a freshly registered user."""
    resp = client.get("/api/workspaces", headers=headers)
    assert resp.status_code == 200
    workspaces = resp.get_json()["workspaces"]
    assert len(workspaces) >= 1, "Expected at least the default workspace"
    return workspaces[0]


def create_workspace(client, headers, name="My Workspace", icon="📚"):
    resp = client.post(
        "/api/workspaces",
        json={"name": name, "icon": icon},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.get_json()["workspace"]


def create_page(client, headers, workspace_id, title="My Page", parent_page_id=None):
    body = {"title": title, "icon": "📄"}
    if parent_page_id:
        body["parent_page_id"] = parent_page_id
    resp = client.post(
        f"/api/workspaces/{workspace_id}/pages",
        json=body,
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.get_json()["page"]


def create_deck(client, headers, name="Test Deck"):
    resp = client.post(
        "/api/flashcards/decks",
        json={"name": name, "description": "A test deck"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.get_json()["deck"]


def create_card(client, headers, deck_id, question="What is 2+2?", answer="4"):
    resp = client.post(
        f"/api/flashcards/decks/{deck_id}/cards",
        json={"question": question, "answer": answer, "difficulty": 1},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.get_json()["card"]
