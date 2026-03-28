import re
from functools import wraps
from flask import request, jsonify


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
HEX_COLOR_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def validate_hex_color(color: str) -> bool:
    return bool(HEX_COLOR_REGEX.match(color))


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    return True, ""


def require_json(*required_fields):
    """Decorator that validates JSON body and checks required fields."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 415
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"error": "Invalid JSON body"}), 400
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                return (
                    jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                    422,
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def sanitize_string(value: str, max_length: int = 300) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]
