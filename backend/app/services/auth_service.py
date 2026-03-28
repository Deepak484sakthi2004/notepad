import random
import string
from datetime import datetime, timedelta, timezone
from flask import current_app
from flask_mail import Message
from app.extensions import db, mail, redis_client
from app.models.user import User
from app.models.workspace import Workspace


def register_user(name: str, email: str, password: str) -> dict:
    """Create a new user and a default workspace. Returns user dict."""
    if User.query.filter_by(email=email.lower()).first():
        raise ValueError("Email already registered")

    user = User(name=name, email=email.lower())
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id

    # Create default workspace
    workspace = Workspace(
        name=f"{name}'s Workspace",
        icon="📓",
        owner_id=user.id,
    )
    db.session.add(workspace)
    db.session.commit()
    return user.to_dict()


def authenticate_user(email: str, password: str) -> User:
    """Authenticate user by email/password. Returns User or raises."""
    user = User.query.filter_by(email=email.lower(), is_active=True).first()
    if not user or not user.check_password(password):
        raise ValueError("Invalid email or password")
    return user


def blacklist_token(jti: str, expires_delta: timedelta):
    """Store a token JTI in Redis blacklist."""
    try:
        redis_client.setex(f"bl:{jti}", int(expires_delta.total_seconds()), "1")
    except Exception:
        pass  # Redis unavailable – best effort


def is_token_blacklisted(jti: str) -> bool:
    try:
        return redis_client.exists(f"bl:{jti}") == 1
    except Exception:
        return False


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def send_otp_email(user: User):
    """Generate OTP, store on user, and send via email."""
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.session.commit()

    try:
        msg = Message(
            subject="NoteSpace – Password Reset OTP",
            recipients=[user.email],
            body=(
                f"Hi {user.name},\n\n"
                f"Your OTP for password reset is: {otp}\n\n"
                "This code expires in 10 minutes.\n\n"
                "If you did not request this, please ignore this email."
            ),
        )
        mail.send(msg)
    except Exception as exc:
        current_app.logger.warning("Failed to send OTP email: %s", exc)


def verify_otp_and_reset(email: str, otp: str, new_password: str) -> bool:
    """Verify OTP and reset password. Returns True on success."""
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return False
    if user.otp_code != otp:
        return False
    now = datetime.now(timezone.utc)
    expires = user.otp_expires_at
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if not expires or now > expires:
        return False

    user.set_password(new_password)
    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()
    return True
