from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    alias = Column(String(200))
    type = Column(String(50), nullable=False)  # 公募/私募/资管/其他
    issuer = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_target = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), default="募集中")  # 募集中/已结束/待开始
    is_archived = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships - cascade delete
    sales_records = relationship("SalesRecord", back_populates="product", cascade="all, delete-orphan")
    import_logs = relationship("ImportLog", back_populates="product", cascade="all, delete-orphan")
    targets = relationship("ProductTarget", back_populates="product", cascade="all, delete-orphan")
