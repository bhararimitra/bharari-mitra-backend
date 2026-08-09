"""Unit tests for BaseCrawler helpers."""

import pytest
from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.shared.exceptions import ValidationError


class _ConcreteTestCrawler(BaseCrawler):
    """Minimal concrete crawler for testing BaseCrawler methods."""
    name = "test_crawler"
    source_url = "https://example.gov.in"

    async def fetch(self):
        return "<html></html>"

    async def parse(self, raw):
        return []


def test_content_hash_deterministic(db):
    """Same title+url must always produce the same hash."""
    # We test the pure method without DB
    class FakeDb:
        pass

    raw = RawJobData(
        title="MPSC State Services 2025",
        notification_url="https://mpsc.gov.in/notification/1",
        organization_slug="mpsc",
        organization_name="MPSC",
        organization_url="https://mpsc.gov.in",
    )

    # Build hash manually to verify
    import hashlib
    expected = hashlib.sha256(
        "mpsc state services 2025|https://mpsc.gov.in/notification/1".encode()
    ).hexdigest()
    # Use a mock db-less instance via object.__new__
    instance = object.__new__(_ConcreteTestCrawler)
    result = instance.build_content_hash(raw)
    assert result == expected


def test_content_hash_changes_with_title():
    raw1 = RawJobData(
        title="Job A", notification_url="https://example.gov.in/1",
        organization_slug="org", organization_name="Org", organization_url="https://example.gov.in"
    )
    raw2 = RawJobData(
        title="Job B", notification_url="https://example.gov.in/1",
        organization_slug="org", organization_name="Org", organization_url="https://example.gov.in"
    )
    instance = object.__new__(_ConcreteTestCrawler)
    assert instance.build_content_hash(raw1) != instance.build_content_hash(raw2)


def test_validate_raises_on_empty_title():
    raw = RawJobData(
        title="",
        notification_url="https://example.gov.in",
        organization_slug="org",
        organization_name="Org",
        organization_url="https://example.gov.in",
    )
    instance = object.__new__(_ConcreteTestCrawler)
    with pytest.raises(ValidationError) as exc_info:
        instance.validate(raw)
    assert "title" in str(exc_info.value)


def test_validate_raises_on_invalid_url():
    raw = RawJobData(
        title="Some Job",
        notification_url="not-a-url",
        organization_slug="org",
        organization_name="Org",
        organization_url="https://example.gov.in",
    )
    instance = object.__new__(_ConcreteTestCrawler)
    with pytest.raises(ValidationError) as exc_info:
        instance.validate(raw)
    assert "notification_url" in str(exc_info.value)


def test_normalize_strips_whitespace():
    raw = RawJobData(
        title="  MPSC   Exam   2025  ",
        notification_url="https://mpsc.gov.in",
        organization_slug="mpsc",
        organization_name="MPSC",
        organization_url="https://mpsc.gov.in",
    )
    instance = object.__new__(_ConcreteTestCrawler)
    normalized = instance.normalize(raw)
    assert normalized.title == "MPSC Exam 2025"


def test_build_slug_is_url_safe():
    instance = object.__new__(_ConcreteTestCrawler)
    slug = instance.build_slug("MPSC State Services Exam 2025", "mpsc")
    assert " " not in slug
    assert slug == slug.lower()
