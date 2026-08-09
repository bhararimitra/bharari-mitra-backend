import uuid
from datetime import datetime
from pydantic import BaseModel


class OrganizationOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    official_url: str
    description: str | None
    active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
