"""SM-2 spaced repetition algorithm implementation."""
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass


@dataclass
class SM2State:
    ease_factor: float = 2.5
    interval_days: int = 1
    repetitions: int = 0


def compute_next_review(
    quality: int,
    ease_factor: float,
    interval_days: int,
    repetitions: int,
) -> tuple[float, int, int, datetime]:
    """
    Apply SM-2 algorithm.

    Parameters
    ----------
    quality     : 0-5 rating (0=complete blackout, 5=perfect)
    ease_factor : current ease factor (≥ 1.3)
    interval_days: current interval in days
    repetitions : number of successful repetitions

    Returns
    -------
    (new_ease_factor, new_interval_days, new_repetitions, next_review_at)
    """
    q = max(0, min(5, quality))

    if q >= 3:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval_days * ease_factor)

        new_ease = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ease = max(1.3, new_ease)
        new_repetitions = repetitions + 1
    else:
        new_interval = 1
        new_ease = ease_factor  # ease_factor unchanged on failure
        new_repetitions = 0

    next_review_at = datetime.now(timezone.utc) + timedelta(days=new_interval)

    return new_ease, new_interval, new_repetitions, next_review_at


def quality_label(quality: int) -> str:
    labels = {
        0: "Blackout",
        1: "Wrong – remembered after seeing",
        2: "Wrong – easy after seeing",
        3: "Correct – significant difficulty",
        4: "Correct – some hesitation",
        5: "Perfect response",
    }
    return labels.get(quality, "Unknown")
