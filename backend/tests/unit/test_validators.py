"""
Unit tests for app/utils/validators.py

Tests cover:
- validate_email: valid and invalid email formats
- validate_password_strength: length and character requirements
- validate_hex_color: valid and invalid hex colour strings
- sanitize_string: trimming and length truncation
"""
import pytest
from app.utils.validators import (
    validate_email,
    validate_password_strength,
    validate_hex_color,
    sanitize_string,
)


# ---------------------------------------------------------------------------
# validate_email
# ---------------------------------------------------------------------------

class TestValidateEmail:
    def test_valid_simple_email(self):
        assert validate_email("user@example.com") is True

    def test_valid_email_with_dots_in_local(self):
        assert validate_email("first.last@example.com") is True

    def test_valid_email_with_plus_tag(self):
        assert validate_email("user+tag@example.co.uk") is True

    def test_valid_email_with_underscores(self):
        assert validate_email("user_name@sub.domain.org") is True

    def test_valid_email_with_numbers(self):
        assert validate_email("user123@domain456.com") is True

    def test_valid_email_hyphen_in_domain(self):
        assert validate_email("user@my-domain.com") is True

    def test_invalid_email_missing_at_symbol(self):
        assert validate_email("userexample.com") is False

    def test_invalid_email_missing_domain(self):
        assert validate_email("user@") is False

    def test_invalid_email_missing_local_part(self):
        assert validate_email("@example.com") is False

    def test_invalid_email_missing_tld(self):
        assert validate_email("user@example") is False

    def test_invalid_email_empty_string(self):
        assert validate_email("") is False

    def test_invalid_email_spaces(self):
        assert validate_email("user @example.com") is False

    def test_invalid_email_double_at(self):
        assert validate_email("user@@example.com") is False


# ---------------------------------------------------------------------------
# validate_password_strength
# ---------------------------------------------------------------------------

class TestValidatePasswordStrength:
    """
    The actual implementation only checks length >= 8.
    Tests reflect what the code actually does.
    """

    def test_password_exactly_eight_chars_passes(self):
        ok, msg = validate_password_strength("abcdefg1")
        assert ok is True
        assert msg == ""

    def test_password_longer_than_eight_passes(self):
        ok, msg = validate_password_strength("SuperSecure99!")
        assert ok is True
        assert msg == ""

    def test_password_seven_chars_fails(self):
        ok, msg = validate_password_strength("Short1!")
        assert ok is False
        assert "8" in msg  # message mentions 8 characters

    def test_password_empty_string_fails(self):
        ok, msg = validate_password_strength("")
        assert ok is False
        assert msg != ""

    def test_password_strength_requires_minimum_length(self):
        """Boundary: 7 characters must fail, 8 must pass."""
        ok_seven, _ = validate_password_strength("1234567")
        ok_eight, _ = validate_password_strength("12345678")
        assert ok_seven is False
        assert ok_eight is True

    def test_password_all_lowercase_eight_chars_passes(self):
        # The implementation does NOT check for uppercase or digits
        ok, msg = validate_password_strength("abcdefgh")
        assert ok is True

    def test_password_all_digits_eight_chars_passes(self):
        ok, msg = validate_password_strength("12345678")
        assert ok is True

    def test_password_returns_tuple(self):
        result = validate_password_strength("Password1")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_password_failure_message_is_string(self):
        ok, msg = validate_password_strength("short")
        assert ok is False
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_password_success_message_is_empty_string(self):
        ok, msg = validate_password_strength("ValidPass123")
        assert ok is True
        assert msg == ""


# ---------------------------------------------------------------------------
# validate_hex_color
# ---------------------------------------------------------------------------

class TestValidateHexColor:
    def test_valid_lowercase_hex(self):
        assert validate_hex_color("#aabbcc") is True

    def test_valid_uppercase_hex(self):
        assert validate_hex_color("#AABBCC") is True

    def test_valid_mixed_case_hex(self):
        assert validate_hex_color("#6366f1") is True

    def test_valid_all_zeros(self):
        assert validate_hex_color("#000000") is True

    def test_valid_all_fs(self):
        assert validate_hex_color("#FFFFFF") is True

    def test_valid_numeric_only(self):
        assert validate_hex_color("#123456") is True

    def test_invalid_missing_hash(self):
        assert validate_hex_color("aabbcc") is False

    def test_invalid_too_short(self):
        assert validate_hex_color("#abc") is False

    def test_invalid_too_long(self):
        assert validate_hex_color("#aabbccdd") is False

    def test_invalid_invalid_characters(self):
        assert validate_hex_color("#gghhii") is False

    def test_invalid_empty_string(self):
        assert validate_hex_color("") is False

    def test_invalid_hash_only(self):
        assert validate_hex_color("#") is False

    def test_invalid_spaces_in_colour(self):
        assert validate_hex_color("# aabbcc") is False


# ---------------------------------------------------------------------------
# sanitize_string
# ---------------------------------------------------------------------------

class TestSanitizeString:
    def test_strips_leading_and_trailing_whitespace(self):
        assert sanitize_string("  hello  ") == "hello"

    def test_truncates_to_default_max_length(self):
        long_str = "a" * 400
        result = sanitize_string(long_str)
        assert len(result) == 300

    def test_truncates_to_custom_max_length(self):
        long_str = "b" * 50
        result = sanitize_string(long_str, max_length=10)
        assert result == "b" * 10

    def test_short_string_not_modified(self):
        assert sanitize_string("hello") == "hello"

    def test_non_string_returns_empty(self):
        assert sanitize_string(None) == ""  # type: ignore
        assert sanitize_string(123) == ""   # type: ignore

    def test_empty_string_returns_empty(self):
        assert sanitize_string("") == ""

    def test_strip_then_truncate(self):
        # "  " + "a"*300 + "  " — after strip it's exactly 300 chars, within limit
        padded = "  " + "a" * 298 + "  "
        result = sanitize_string(padded, max_length=300)
        assert result == "a" * 298
