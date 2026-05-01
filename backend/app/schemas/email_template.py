from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EmailTemplateCreate(BaseModel):
    type: str = Field(..., pattern="^(invitation|request|reminder|overdue)$")
    subject: str = Field(..., min_length=5, max_length=500)
    body_html: str = Field(..., min_length=10)
    department_id: Optional[int] = None


class EmailTemplateUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=5, max_length=500)
    body_html: Optional[str] = Field(None, min_length=10)


class EmailTemplateResponse(BaseModel):
    id: int
    department_id: Optional[int]
    type: str
    subject: str
    body_html: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
