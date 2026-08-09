import uuid
from pydantic import BaseModel


class DistrictOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    model_config = {"from_attributes": True}
