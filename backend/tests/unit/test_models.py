"""
Unit tests for model methods.

Covers:
- User.set_password() / check_password()
- User.to_dict() fields and password_hash exclusion
- Page.soft_delete() and Page.restore()
- Page.to_dict() fields (with/without blocks, with/without tags)
- Workspace.to_dict() fields
"""
import pytest
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class TestUserModel:
    def test_set_password_stores_hash(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            assert user.password_hash is not None
            assert user.password_hash != "Password1"

    def test_check_password_correct_password_returns_true(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            assert user.check_password("Password1") is True

    def test_check_password_wrong_password_returns_false(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            assert user.check_password("WrongPassword") is False

    def test_check_password_empty_password_returns_false(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            assert user.check_password("") is False

    def test_check_password_no_hash_returns_false(self, app, db):
        with app.app_context():
            from app.models.user import User
            user = User(name="No Hash", email="nohash@example.com")
            # password_hash is None by default – no set_password called
            assert user.check_password("anything") is False

    def test_set_password_replaces_old_hash(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            old_hash = user.password_hash
            user.set_password("NewPassword9")
            assert user.password_hash != old_hash

    def test_to_dict_contains_expected_keys(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            d = user.to_dict()
            for key in ("id", "name", "email", "avatar_url", "is_active", "created_at"):
                assert key in d, f"Key '{key}' missing from User.to_dict()"

    def test_to_dict_does_not_expose_password_hash(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            d = user.to_dict()
            assert "password_hash" not in d

    def test_to_dict_email_is_correct(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            d = user.to_dict()
            assert d["email"] == "testuser@example.com"

    def test_to_dict_is_active_defaults_true(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            d = user.to_dict()
            assert d["is_active"] is True

    def test_to_dict_created_at_is_isoformat_string(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            d = user.to_dict()
            created_at = d["created_at"]
            assert isinstance(created_at, str)
            # Should be parseable as an ISO datetime
            datetime.fromisoformat(created_at)

    def test_repr_contains_email(self, db, app, test_user):
        with app.app_context():
            from app.models.user import User
            user = db.session.get(User, test_user.id)
            assert "testuser@example.com" in repr(user)


# ---------------------------------------------------------------------------
# Page model – soft_delete / restore
# ---------------------------------------------------------------------------

class TestPageSoftDelete:
    def test_soft_delete_sets_is_deleted_true(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            assert page.is_deleted is False
            page.soft_delete()
            assert page.is_deleted is True

    def test_soft_delete_sets_deleted_at_to_now(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            before = datetime.now(timezone.utc)
            page.soft_delete()
            after = datetime.now(timezone.utc)
            assert page.deleted_at is not None
            deleted_at = page.deleted_at
            if deleted_at.tzinfo is None:
                deleted_at = deleted_at.replace(tzinfo=timezone.utc)
            assert before <= deleted_at <= after

    def test_restore_sets_is_deleted_false(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            page.soft_delete()
            assert page.is_deleted is True
            page.restore()
            assert page.is_deleted is False

    def test_restore_clears_deleted_at(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            page.soft_delete()
            assert page.deleted_at is not None
            page.restore()
            assert page.deleted_at is None

    def test_soft_delete_then_restore_is_idempotent(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            page.soft_delete()
            page.restore()
            page.soft_delete()
            assert page.is_deleted is True


# ---------------------------------------------------------------------------
# Page model – to_dict
# ---------------------------------------------------------------------------

class TestPageToDict:
    def test_to_dict_contains_expected_keys(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict()
            expected = (
                "id", "workspace_id", "parent_page_id", "title", "icon",
                "cover_image", "is_deleted", "deleted_at", "sort_order",
                "created_by", "created_at", "updated_at",
            )
            for key in expected:
                assert key in d, f"Key '{key}' missing from Page.to_dict()"

    def test_to_dict_without_include_blocks_omits_blocks(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict(include_blocks=False)
            assert "blocks" not in d
            assert "plain_text" not in d

    def test_to_dict_with_include_blocks_includes_blocks(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict(include_blocks=True)
            assert "blocks" in d
            assert "plain_text" in d

    def test_to_dict_with_include_tags_includes_tags_list(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict(include_tags=True)
            assert "tags" in d
            assert isinstance(d["tags"], list)

    def test_to_dict_without_include_tags_omits_tags(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict(include_tags=False)
            assert "tags" not in d

    def test_to_dict_title_matches(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict()
            assert d["title"] == "Test Page"

    def test_to_dict_is_deleted_defaults_false(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict()
            assert d["is_deleted"] is False

    def test_to_dict_deleted_at_is_none_when_not_deleted(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            d = page.to_dict()
            assert d["deleted_at"] is None

    def test_to_dict_deleted_at_is_string_after_soft_delete(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            page.soft_delete()
            d = page.to_dict()
            assert isinstance(d["deleted_at"], str)
            datetime.fromisoformat(d["deleted_at"])

    def test_repr_contains_title(self, db, app, test_page):
        with app.app_context():
            from app.models.page import Page
            page = db.session.get(Page, test_page.id)
            assert "Test Page" in repr(page)


# ---------------------------------------------------------------------------
# Workspace model – to_dict
# ---------------------------------------------------------------------------

class TestWorkspaceToDict:
    def test_to_dict_contains_expected_keys(self, db, app, test_workspace):
        with app.app_context():
            from app.models.workspace import Workspace
            ws = db.session.get(Workspace, test_workspace.id)
            d = ws.to_dict()
            for key in ("id", "name", "icon", "owner_id", "created_at"):
                assert key in d, f"Key '{key}' missing from Workspace.to_dict()"

    def test_to_dict_name_matches(self, db, app, test_workspace):
        with app.app_context():
            from app.models.workspace import Workspace
            ws = db.session.get(Workspace, test_workspace.id)
            d = ws.to_dict()
            assert d["name"] == "Test Workspace"

    def test_to_dict_owner_id_matches_test_user(self, db, app, test_workspace, test_user):
        with app.app_context():
            from app.models.workspace import Workspace
            ws = db.session.get(Workspace, test_workspace.id)
            d = ws.to_dict()
            assert d["owner_id"] == test_user.id

    def test_to_dict_created_at_is_isoformat_string(self, db, app, test_workspace):
        with app.app_context():
            from app.models.workspace import Workspace
            ws = db.session.get(Workspace, test_workspace.id)
            d = ws.to_dict()
            assert isinstance(d["created_at"], str)
            datetime.fromisoformat(d["created_at"])

    def test_repr_contains_name(self, db, app, test_workspace):
        with app.app_context():
            from app.models.workspace import Workspace
            ws = db.session.get(Workspace, test_workspace.id)
            assert "Test Workspace" in repr(ws)
