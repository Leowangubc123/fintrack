from pydantic import BaseModel
from typing import Optional


class MemberBase(BaseModel):
    name: str
    phone: Optional[str] = None
    group_id: int
    scope: Optional[str] = "public_fund,private_fund,advisory,margin_trading"


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    group_id: Optional[int] = None
    scope: Optional[str] = None


class MemberResponse(MemberBase):
    id: int
    group_name: Optional[str] = None

    class Config:
        from_attributes = True
