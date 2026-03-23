from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class ProductBase(BaseModel):
    name: str
    alias: Optional[str] = None
    type: str
    issuer: Optional[str] = ''
    code: str
    start_date: date
    end_date: date
    total_target: Decimal
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    status: str
    is_archived: bool
    created_at: datetime
    raised_amount: Optional[float] = 0  # 已募集金额
    assigned_count: Optional[int] = 0   # 已分配人数

    class Config:
        from_attributes = True
