"""Pydantic schemas for Jobs module."""

import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field
from app.modules.jobs.models import JobStatus, NotificationType


class OrganizationBrief(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    official_url: str
    model_config = {"from_attributes": True}


class DepartmentBrief(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    model_config = {"from_attributes": True}


class QualificationBrief(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    model_config = {"from_attributes": True}


class DistrictBrief(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    status: JobStatus
    notification_type: NotificationType
    vacancy_count: int | None
    salary_min: int | None
    salary_max: int | None
    age_min: int | None
    age_max: int | None
    published_at: date | None
    last_date: date | None
    notification_url: str | None = None
    apply_url: str | None = None
    pdf_url: str | None = None
    recruitment_event_id: uuid.UUID | None = None
    organization: OrganizationBrief | None
    department: DepartmentBrief | None
    qualification: QualificationBrief | None
    district: DistrictBrief | None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class RecruitmentBrief(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    status: str
    model_config = {"from_attributes": True}


class JobDetail(JobListItem):
    summary: str | None
    created_at: datetime
    updated_at: datetime
    recruitment_event: RecruitmentBrief | None = None
    related_updates: list[JobListItem] = Field(default_factory=list)

class JobFilters(BaseModel):
    status: JobStatus | None = None
    organization_slug: str | None = None
    department_slug: str | None = None
    district_slug: str | None = None
    qualification_slug: str | None = None
    notification_type: NotificationType | None = None
    # When True (default for /jobs), limit to job+advertisement unless notification_type set.
    recruitment_only: bool = True
    sort_by: str = Field(default="published_at", pattern="^(published_at|last_date|vacancy_count)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
