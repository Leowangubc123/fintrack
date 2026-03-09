from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GroupBase(BaseModel):
    name: str
    leader: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(GroupBase):
    pass


class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True
