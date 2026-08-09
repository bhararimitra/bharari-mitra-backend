"""Import all ORM models so SQLAlchemy relationship strings resolve."""

from app.modules.organizations.models import Organization
from app.modules.departments.models import Department
from app.modules.districts.models import District
from app.modules.qualifications.models import Qualification
from app.modules.recruitments.models import RecruitmentEvent
from app.modules.jobs.models import Job
from app.modules.crawlers.models import CrawlerHistory

__all__ = [
    "Organization",
    "Department",
    "District",
    "Qualification",
    "RecruitmentEvent",
    "Job",
    "CrawlerHistory",
]
