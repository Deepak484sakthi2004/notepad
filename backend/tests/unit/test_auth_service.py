"""
Unit tests for app/services/auth_service.py

Covers:
- register_user: creates user with hashed password
- register_user: creates default workspace
- register_user: raises ValueError on duplicate email
- authenticate_user: returns user on correct credentials
- authenticate_user: raises ValueError on wrong password
- authenticate_user: raises ValueError on unknown email
- authenticate_user: raises ValueError for inactive user
- generate_otp: returns 6-digit numeric string
- verify_otp_and_reset: updates password on valid OTP
- verify_otp_and_reset: returns False on wrong OTP
- verify_otp_and_reset: returns False for unknown email
- verify_otp_and_reset: returns False on expired OTP
- blacklist_token / is_token_blacklisted: Redis interaction (mocked)
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# register_user
# ---------------------------------------------------------------------------

class TestRegisterUser:
    def test_register_user_creates_user_in_db(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user
            from app.models.user import User

            register_user("Alice", "alice@example.com", "StrongPass1")

            user = User.query.filter_by(email="alice@example.com").first()
            assert user is not None
            assert user.name == "Alice"

    def test_register_user_stores_hashed_password(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user
            from app.models.user import User

            register_user("Bob", "bob@example.com", "StrongPass1")

            user = User.query.filter_by(email="bob@example.com").first()
            assert user.password_hash is not None
            assert user.password_hash != "StrongPass1"

    def test_register_user_password_is_verifiable(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user
            from app.models.user import User

            register_user("Carol", "carol@example.com", "MyPass123")

            user = User.query.filter_by(email="carol@example.com").first()
            assert user.check_password("MyPass123") is True

    def test_register_user_stores_email_lowercased(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user
            from app.models.user import User

            register_user("Dave", "Dave@Example.COM", "Pass12345")

            user = User.query.filter_by(email="dave@example.com").first()
            assert user is not None

    def test_register_user_creates_default_workspace(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user
            from app.models.workspace import Workspace
            from app.models.user import User

            register_user("Eve", "eve@example.com", "Pass12345")

            user = User.query.filter_by(email="eve@example.com").first()
            workspaces = Workspace.query.filter_by(owner_id=user.id).all()
            assert len(workspaces) == 1

    def test_register_user_workspace_name_includes_user_name(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user
            from app.models.workspace import Workspace
            from app.models.user import User

            register_user("Frank", "frank@example.com", "Pass12345")

            user = User.query.filter_by(email="frank@example.com").first()
            workspace = Workspace.query.filter_by(owner_id=user.id).first()
            assert "Frank" in workspace.name

    def test_register_user_returns_user_dict(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user

            result = register_user("Grace", "grace@example.com", "Pass12345")

            assert isinstance(result, dict)
            assert result["email"] == "grace@example.com"
            assert "id" in result

    def test_register_user_raises_on_duplicate_email(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user

            register_user("Henry", "henry@example.com", "Pass12345")

            with pytest.raises(ValueError, match="already registered"):
                register_user("Henry2", "henry@example.com", "OtherPass1")

    def test_register_user_duplicate_email_case_insensitive(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user

            register_user("Iris", "iris@example.com", "Pass12345")

            with pytest.raises(ValueError):
                register_user("Iris2", "IRIS@example.com", "OtherPass1")


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------

class TestAuthenticateUser:
    def test_authenticate_user_returns_user_on_correct_password(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user, authenticate_user

            register_user("Jake", "jake@example.com", "Pass12345")
            user = authenticate_user("jake@example.com", "Pass12345")
            assert user is not None
            assert user.email == "jake@example.com"

    def test_authenticate_user_raises_on_wrong_password(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user, authenticate_user

            register_user("Kira", "kira@example.com", "Pass12345")

            with pytest.raises(ValueError, match="Invalid email or password"):
                authenticate_user("kira@example.com", "WrongPassword")

    def test_authenticate_user_raises_on_unknown_email(self, db, app):
        with app.app_context():
            from app.services.auth_service import authenticate_user

            with pytest.raises(ValueError, match="Invalid email or password"):
                authenticate_user("nobody@example.com", "Pass12345")

    def test_authenticate_user_email_lookup_is_case_insensitive(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user, authenticate_user

            register_user("Leo", "leo@example.com", "Pass12345")
            user = authenticate_user("LEO@EXAMPLE.COM", "Pass12345")
            assert user.email == "leo@example.com"

    def test_authenticate_user_raises_for_inactive_user(self, db, app):
        with app.app_context():
            from app.services.auth_service import register_user, authenticate_user
            from app.models.user import User
            from app.extensions import db as _db

            register_user("Mia", "mia@example.com", "Pass12345")
            user = User.query.filter_by(email="mia@example.com").first()
            user.is_active = False
            _db.session.commit()

            with pytest.raises(ValueError, match="Invalid email or password"):
                authenticate_user("mia@example.com", "Pass12345")


# ---------------------------------------------------------------------------
# generate_otp
# ---------------------------------------------------------------------------

class TestGenerateOtp:
    def test_generate_otp_returns_6_character_string(self):
        from app.services.auth_service import generate_otp
        otp = generate_otp()
        assert isinstance(otp, str)
        assert len(otp) == 6

    def test_generate_otp_contains_only_digits(self):
        from app.services.auth_service import generate_otp
        for _ in range(20):
            otp = generate_otp()
            assert otp.isdigit(), f"OTP '{otp}' contains non-digit characters"

    def test_generate_otp_produces_different_values(self):
        """Generating many OTPs should yield some variation (not all the same)."""
        from app.services.auth_service import generate_otp
        otps = {generate_otp() for _ in range(50)}
        # With 10^6 possible values the chance of all 50 being equal is negligible
        assert len(otps) > 1


# ---------------------------------------------------------------------------
# verify_otp_and_reset
# ---------------------------------------------------------------------------

class TestVerifyOtpAndReset:
    def _create_user_with_otp(self, db, app, email, password, otp, expires_delta_minutes=10):
        """Helper: register a user and manually set their OTP fields."""
        from app.services.auth_service import register_user
        from app.models.user import User
        from app.extensions import db as _db

        register_user("OTP User", email, password)
        user = User.query.filter_by(email=email).first()
        user.otp_code = otp
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
        _db.session.commit()
        return user

    def test_verify_otp_and_reset_returns_true_on_valid_otp(self, db, app):
        with app.app_context():
            from app.services.auth_service import verify_otp_and_reset

            self._create_user_with_otp(db, app, "reset1@example.com", "OldPass1", "123456")
            result = verify_otp_and_reset("reset1@example.com", "123456", "NewPass99")
            assert result is True

    def test_verify_otp_and_reset_updates_password(self, db, app):
        with app.app_context():
            from app.services.auth_service import verify_otp_and_reset
            from app.models.user import User

            self._create_user_with_otp(db, app, "reset2@example.com", "OldPass1", "654321")
            verify_otp_and_reset("reset2@example.com", "654321", "BrandNew99")

            user = User.query.filter_by(email="reset2@example.com").first()
            assert user.check_password("BrandNew99") is True

    def test_verify_otp_and_reset_clears_otp_fields(self, db, app):
        with app.app_context():
            from app.services.auth_service import verify_otp_and_reset
            from app.models.user import User

            self._create_user_with_otp(db, app, "reset3@example.com", "OldPass1", "111111")
            verify_otp_and_reset("reset3@example.com", "111111", "ClearedPass9")

            user = User.query.filter_by(email="reset3@example.com").first()
            assert user.otp_code is None
            assert user.otp_expires_at is None

    def test_verify_otp_and_reset_returns_false_on_wrong_otp(self, db, app):
        with app.app_context():
            from app.services.auth_service import verify_otp_and_reset

            self._create_user_with_otp(db, app, "reset4@example.com", "OldPass1", "999999")
            result = verify_otp_and_reset("reset4@example.com", "000000", "NewPass99")
            assert result is False

    def test_verify_otp_and_reset_returns_false_for_unknown_email(self, db, app):
        with app.app_context():
            from app.services.auth_service import verify_otp_and_reset

            result = verify_otp_and_reset("ghost@example.com", "123456", "NewPass99")
            assert result is False

    def test_verify_otp_and_reset_returns_false_on_expired_otp(self, db, app):
        with app.app_context():
            from app.services.auth_service import verify_otp_and_reset

            # Set OTP that expired 1 minute ago
            self._create_user_with_otp(
                db, app, "reset5@example.com", "OldPass1", "777777",
                expires_delta_minutes=-1,
            )
            result = verify_otp_and_reset("reset5@example.com", "777777", "NewPass99")
            assert result is False

    def test_verify_otp_and_reset_wrong_otp_does_not_change_password(self, db, app):
        with app.app_context():
            from app.services.auth_service import verify_otp_and_reset
            from app.models.user import User

            self._create_user_with_otp(db, app, "reset6@example.com", "OldPass1", "555555")
            verify_otp_and_reset("reset6@example.com", "000000", "NewPass99")

            user = User.query.filter_by(email="reset6@example.com").first()
            assert user.check_password("OldPass1") is True
            assert user.check_password("NewPass99") is False


# ---------------------------------------------------------------------------
# blacklist_token / is_token_blacklisted (Redis mocked)
# ---------------------------------------------------------------------------

class TestTokenBlacklist:
    def test_blacklist_token_calls_redis_setex(self):
        from app.services.auth_service import blacklist_token
        import app.services.auth_service as auth_mod

        mock_redis = MagicMock()
        mock_redis.setex = MagicMock()
        original = auth_mod.redis_client
        auth_mod.redis_client = mock_redis

        try:
            blacklist_token("test-jti-123", timedelta(seconds=3600))
            mock_redis.setex.assert_called_once_with("bl:test-jti-123", 3600, "1")
        finally:
            auth_mod.redis_client = original

    def test_is_token_blacklisted_returns_true_when_redis_exists_returns_1(self):
        from app.services.auth_service import is_token_blacklisted
        import app.services.auth_service as auth_mod

        mock_redis = MagicMock()
        mock_redis.exists = MagicMock(return_value=1)
        original = auth_mod.redis_client
        auth_mod.redis_client = mock_redis

        try:
            result = is_token_blacklisted("some-jti")
            assert result is True
        finally:
            auth_mod.redis_client = original

    def test_is_token_blacklisted_returns_false_when_redis_exists_returns_0(self):
        from app.services.auth_service import is_token_blacklisted
        import app.services.auth_service as auth_mod

        mock_redis = MagicMock()
        mock_redis.exists = MagicMock(return_value=0)
        original = auth_mod.redis_client
        auth_mod.redis_client = mock_redis

        try:
            result = is_token_blacklisted("some-jti")
            assert result is False
        finally:
            auth_mod.redis_client = original

    def test_blacklist_token_swallows_redis_exception(self):
        """If Redis raises, blacklist_token must not propagate the error."""
        from app.services.auth_service import blacklist_token
        import app.services.auth_service as auth_mod

        mock_redis = MagicMock()
        mock_redis.setex = MagicMock(side_effect=Exception("Redis down"))
        original = auth_mod.redis_client
        auth_mod.redis_client = mock_redis

        try:
            # Should not raise
            blacklist_token("failing-jti", timedelta(seconds=60))
        finally:
            auth_mod.redis_client = original

    def test_is_token_blacklisted_returns_false_when_redis_raises(self):
        """If Redis raises, is_token_blacklisted must return False (safe default)."""
        from app.services.auth_service import is_token_blacklisted
        import app.services.auth_service as auth_mod

        mock_redis = MagicMock()
        mock_redis.exists = MagicMock(side_effect=Exception("Redis down"))
        original = auth_mod.redis_client
        auth_mod.redis_client = mock_redis

        try:
            result = is_token_blacklisted("failing-jti")
            assert result is False
        finally:
            auth_mod.redis_client = original
