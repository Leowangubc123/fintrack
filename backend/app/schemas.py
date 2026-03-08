from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ==================== Enums ====================

class ProductType(str, Enum):
    PUBLIC = "公募产品"
    PRIVATE = "私募产品"


class ProductStatus(str, Enum):
    COLLECTING = "COLLECTING"
    ENDED = "ENDED"
    PENDING = "PENDING"
    ARCHIVED = "ARCHIVED"


# ==================== Group Schemas ====================

class GroupBase(BaseModel):
    name: str
    leader: Optional[str] = None
    region: Optional[str] = None
    remark: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True


# ==================== Member Schemas ====================

class MemberBase(BaseModel):
    name: str
    employee_id: Optional[str] = None
    group_id: int
    phone: Optional[str] = None
    email: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberResponse(MemberBase):
    id: int
    joined_at: datetime
    status: str
    group_name: str

    class Config:
        from_attributes = True


# ==================== Product Schemas ====================

class ProductBase(BaseModel):
    name: str
    alias: Optional[str] = None
    type: ProductType
    issuer: str
    code: str
    start_date: datetime
    end_date: datetime
    total_target: Decimal
    yield_rate: Optional[Decimal] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    status: ProductStatus
    created_at: datetime
    archived_at: Optional[datetime] = None
    actual_amount: Decimal = Decimal("0")
    completion_rate: float = 0.0

    class Config:
        from_attributes = True
