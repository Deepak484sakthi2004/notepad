"""
Unit tests for app/services/spaced_repetition.py

Tests cover every branch of the SM-2 algorithm implementation:
- quality 0 (blackout): interval → 1, repetitions → 0, ease_factor unchanged
- quality 1 (wrong):    interval → 1, repetitions → 0, ease_factor unchanged
- quality 2 (hard):     interval → 1, repetitions → 0, ease_factor unchanged
- quality 3 (ok):       first review (reps=0) → interval=1
- quality 3:            second review (reps=1) → interval=6
- quality 3:            third review (reps=2) → interval = round(prev * ef)
- quality 4 (hesitant): ease_factor update formula verified
- quality 5 (perfect):  ease_factor increases above initial
- ease_factor never goes below 1.3
- next_review_at is in the future
- quality_label returns correct strings for all 6 levels
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.spaced_repetition import compute_next_review, quality_label, SM2State


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_EF = 2.5
DEFAULT_INTERVAL = 1
DEFAULT_REPS = 0


def call(quality, ease_factor=DEFAULT_EF, interval_days=DEFAULT_INTERVAL, repetitions=DEFAULT_REPS):
    """Thin wrapper to keep test call sites concise."""
    return compute_next_review(quality, ease_factor, interval_days, repetitions)


# ---------------------------------------------------------------------------
# Failing qualities (0, 1, 2) – interval resets to 1
# ---------------------------------------------------------------------------

class TestFailingQualities:
    def test_quality_0_blackout_interval_resets_to_1(self):
        _, new_interval, _, _ = call(0, ease_factor=2.5, interval_days=10, repetitions=5)
        assert new_interval == 1

    def test_quality_0_blackout_repetitions_reset_to_0(self):
        _, _, new_reps, _ = call(0, ease_factor=2.5, interval_days=10, repetitions=5)
        assert new_reps == 0

    def test_quality_0_blackout_ease_factor_unchanged(self):
        new_ef, _, _, _ = call(0, ease_factor=2.5, interval_days=10, repetitions=5)
        assert new_ef == 2.5

    def test_quality_1_wrong_interval_resets_to_1(self):
        _, new_interval, _, _ = call(1, ease_factor=2.5, interval_days=6, repetitions=2)
        assert new_interval == 1

    def test_quality_1_wrong_repetitions_reset_to_0(self):
        _, _, new_reps, _ = call(1, ease_factor=2.5, interval_days=6, repetitions=2)
        assert new_reps == 0

    def test_quality_1_wrong_ease_factor_unchanged(self):
        new_ef, _, _, _ = call(1, ease_factor=2.2, interval_days=6, repetitions=2)
        assert new_ef == 2.2

    def test_quality_2_hard_interval_resets_to_1(self):
        _, new_interval, _, _ = call(2, ease_factor=2.5, interval_days=15, repetitions=3)
        assert new_interval == 1

    def test_quality_2_hard_repetitions_reset_to_0(self):
        _, _, new_reps, _ = call(2, ease_factor=2.5, interval_days=15, repetitions=3)
        assert new_reps == 0

    def test_quality_2_hard_ease_factor_unchanged(self):
        new_ef, _, _, _ = call(2, ease_factor=1.8, interval_days=15, repetitions=3)
        assert new_ef == 1.8


# ---------------------------------------------------------------------------
# Passing qualities (3, 4, 5) – interval progression
# ---------------------------------------------------------------------------

class TestPassingQualityIntervalProgression:
    def test_quality_3_first_review_interval_is_1(self):
        """First review (reps=0) → interval should be 1."""
        _, new_interval, _, _ = call(3, repetitions=0)
        assert new_interval == 1

    def test_quality_3_first_review_repetitions_become_1(self):
        _, _, new_reps, _ = call(3, repetitions=0)
        assert new_reps == 1

    def test_quality_3_second_review_interval_is_6(self):
        """Second review (reps=1) → interval should be 6."""
        _, new_interval, _, _ = call(3, repetitions=1)
        assert new_interval == 6

    def test_quality_3_second_review_repetitions_become_2(self):
        _, _, new_reps, _ = call(3, repetitions=1)
        assert new_reps == 2

    def test_quality_3_third_review_interval_uses_ease_factor(self):
        """Third review (reps=2) → interval = round(prev_interval * ease_factor)."""
        ef = 2.5
        prev_interval = 6
        _, new_interval, _, _ = call(3, ease_factor=ef, interval_days=prev_interval, repetitions=2)
        assert new_interval == round(prev_interval * ef)

    def test_quality_4_third_review_interval_uses_ease_factor(self):
        ef = 2.5
        prev_interval = 6
        _, new_interval, _, _ = call(4, ease_factor=ef, interval_days=prev_interval, repetitions=2)
        assert new_interval == round(prev_interval * ef)

    def test_quality_5_third_review_interval_uses_ease_factor(self):
        ef = 2.5
        prev_interval = 6
        _, new_interval, _, _ = call(5, ease_factor=ef, interval_days=prev_interval, repetitions=2)
        assert new_interval == round(prev_interval * ef)

    def test_quality_5_first_review_interval_is_1(self):
        _, new_interval, _, _ = call(5, repetitions=0)
        assert new_interval == 1

    def test_quality_5_second_review_interval_is_6(self):
        _, new_interval, _, _ = call(5, repetitions=1)
        assert new_interval == 6


# ---------------------------------------------------------------------------
# Ease-factor updates
# ---------------------------------------------------------------------------

class TestEaseFactorUpdates:
    """
    SM-2 formula: new_ef = ef + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
    For q=5: delta = 0.1 - 0*... = +0.10
    For q=4: delta = 0.1 - 1*(0.08 + 0.02) = 0.0
    For q=3: delta = 0.1 - 2*(0.08 + 0.08) = 0.1 - 0.32 = -0.22  (wait: let's compute properly)
         (5-3) = 2; delta = 0.1 - 2*(0.08 + 2*0.02) = 0.1 - 2*0.12 = 0.1 - 0.24 = -0.14
    For q=4: (5-4)=1; delta = 0.1 - 1*(0.08 + 1*0.02) = 0.1 - 0.10 = 0.0
    """

    def test_quality_5_increases_ease_factor(self):
        ef = 2.5
        new_ef, _, _, _ = call(5, ease_factor=ef, repetitions=1)
        assert new_ef > ef

    def test_quality_5_ease_factor_delta_is_0_1(self):
        ef = 2.5
        new_ef, _, _, _ = call(5, ease_factor=ef, repetitions=1)
        assert abs(new_ef - (ef + 0.10)) < 1e-9

    def test_quality_4_ease_factor_unchanged(self):
        ef = 2.5
        new_ef, _, _, _ = call(4, ease_factor=ef, repetitions=1)
        # delta for q=4 is 0.0
        assert abs(new_ef - ef) < 1e-9

    def test_quality_3_decreases_ease_factor(self):
        ef = 2.5
        new_ef, _, _, _ = call(3, ease_factor=ef, repetitions=1)
        assert new_ef < ef

    def test_quality_3_ease_factor_delta_is_minus_0_14(self):
        ef = 2.5
        new_ef, _, _, _ = call(3, ease_factor=ef, repetitions=1)
        expected = ef + (0.1 - (5 - 3) * (0.08 + (5 - 3) * 0.02))
        expected = max(1.3, expected)
        assert abs(new_ef - expected) < 1e-9

    def test_ease_factor_never_goes_below_1_3(self):
        """Even with repeated quality-3 reviews from a low ease factor."""
        ef = 1.3
        new_ef, _, _, _ = call(3, ease_factor=ef, repetitions=1)
        assert new_ef >= 1.3

    def test_ease_factor_floor_enforced_at_1_3_when_ef_very_low(self):
        """Start from 1.3, quality-3 would push below floor; must clamp."""
        ef = 1.3
        new_ef, _, _, _ = call(3, ease_factor=ef, repetitions=1)
        assert new_ef == 1.3  # clamped at floor

    def test_failing_quality_does_not_change_ease_factor(self):
        """Qualities 0-2 leave ease_factor unchanged."""
        for q in (0, 1, 2):
            ef = 2.1
            new_ef, _, _, _ = call(q, ease_factor=ef, repetitions=3)
            assert new_ef == ef, f"ease_factor changed for quality {q}"


# ---------------------------------------------------------------------------
# next_review_at
# ---------------------------------------------------------------------------

class TestNextReviewAt:
    def test_next_review_at_is_in_the_future(self):
        _, _, _, next_at = call(3, repetitions=0)
        assert next_at > datetime.now(timezone.utc)

    def test_next_review_at_is_timezone_aware(self):
        _, _, _, next_at = call(3, repetitions=0)
        assert next_at.tzinfo is not None

    def test_next_review_at_is_roughly_interval_days_away(self):
        """next_review_at should be approximately now + interval_days."""
        _, new_interval, _, next_at = call(3, repetitions=1)  # interval = 6
        expected_lower = datetime.now(timezone.utc) + timedelta(days=new_interval - 1)
        expected_upper = datetime.now(timezone.utc) + timedelta(days=new_interval + 1)
        assert expected_lower <= next_at <= expected_upper

    def test_next_review_at_after_failure_is_one_day_away(self):
        """Failing review → interval=1 → next_review_at ≈ tomorrow."""
        _, new_interval, _, next_at = call(0, interval_days=30, repetitions=10)
        assert new_interval == 1
        tomorrow_lower = datetime.now(timezone.utc) + timedelta(hours=23)
        tomorrow_upper = datetime.now(timezone.utc) + timedelta(hours=25)
        assert tomorrow_lower <= next_at <= tomorrow_upper


# ---------------------------------------------------------------------------
# quality clamping
# ---------------------------------------------------------------------------

class TestQualityClamping:
    def test_quality_above_5_clamped_to_5(self):
        """Quality > 5 is clamped to 5 by the implementation."""
        new_ef_6, interval_6, reps_6, _ = call(6, ease_factor=2.5, repetitions=0)
        new_ef_5, interval_5, reps_5, _ = call(5, ease_factor=2.5, repetitions=0)
        assert new_ef_6 == new_ef_5
        assert interval_6 == interval_5
        assert reps_6 == reps_5

    def test_quality_below_0_clamped_to_0(self):
        """Quality < 0 is clamped to 0 by the implementation."""
        new_ef_neg, interval_neg, reps_neg, _ = call(-1, ease_factor=2.5, repetitions=3)
        new_ef_0, interval_0, reps_0, _ = call(0, ease_factor=2.5, repetitions=3)
        assert new_ef_neg == new_ef_0
        assert interval_neg == interval_0
        assert reps_neg == reps_0


# ---------------------------------------------------------------------------
# quality_label
# ---------------------------------------------------------------------------

class TestQualityLabel:
    def test_quality_0_label_is_blackout(self):
        assert quality_label(0) == "Blackout"

    def test_quality_1_label_contains_wrong(self):
        label = quality_label(1)
        assert "Wrong" in label

    def test_quality_2_label_contains_wrong(self):
        label = quality_label(2)
        assert "Wrong" in label

    def test_quality_3_label_contains_correct(self):
        label = quality_label(3)
        assert "Correct" in label

    def test_quality_4_label_contains_correct(self):
        label = quality_label(4)
        assert "Correct" in label

    def test_quality_5_label_is_perfect(self):
        assert quality_label(5) == "Perfect response"

    def test_unknown_quality_returns_unknown(self):
        assert quality_label(99) == "Unknown"
        assert quality_label(-1) == "Unknown"

    def test_all_defined_qualities_return_non_empty_string(self):
        for q in range(6):
            label = quality_label(q)
            assert isinstance(label, str) and len(label) > 0


# ---------------------------------------------------------------------------
# SM2State dataclass defaults
# ---------------------------------------------------------------------------

class TestSM2StateDefaults:
    def test_default_ease_factor(self):
        state = SM2State()
        assert state.ease_factor == 2.5

    def test_default_interval_days(self):
        state = SM2State()
        assert state.interval_days == 1

    def test_default_repetitions(self):
        state = SM2State()
        assert state.repetitions == 0
