from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class ProductBase(BaseModel):
    name: str
    alias: Optional[str] = None
    type: str
    issuer: str
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

    class Config:
        from_attributes = True
