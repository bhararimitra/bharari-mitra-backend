"""Unit tests for expired-job cutoff math."""

from datetime import date

from app.modules.jobs.cleanup import expired_cutoff


def test_expired_cutoff_seven_days():
    cutoff = expired_cutoff(today=date(2026, 8, 11), retention_days=7)
    assert cutoff == date(2026, 8, 4)


def test_expired_cutoff_zero_retention():
    cutoff = expired_cutoff(today=date(2026, 8, 11), retention_days=0)
    assert cutoff == date(2026, 8, 11)


def test_expired_cutoff_negative_treated_as_zero():
    cutoff = expired_cutoff(today=date(2026, 8, 11), retention_days=-3)
    assert cutoff == date(2026, 8, 11)
