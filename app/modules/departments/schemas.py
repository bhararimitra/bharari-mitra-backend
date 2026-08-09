import uuid
from pydantic import BaseModel


class DepartmentOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    organization_id: uuid.UUID
    model_config = {"from_attributes": True}
