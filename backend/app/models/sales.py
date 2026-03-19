from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductTarget(Base):
    __tablename__ = "product_targets"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    target_amount = Column(Numeric(15, 2), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="targets")
    group = relationship("Group", back_populates="targets")
    member = relationship("Member", back_populates="targets")


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    sale_date = Column(Date, nullable=False)
    customer_count = Column(Integer, default=1)
    remark = Column(String(500))
    import_batch_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="sales_records")
    member = relationship("Member", back_populates="sales_records")


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    operator = Column(String(100))
    import_time = Column(DateTime(timezone=True), server_default=func.now())
    total_rows = Column(Integer)
    success_rows = Column(Integer)
    fail_rows = Column(Integer)
    file_name = Column(String(255))

    # Relationships
    product = relationship("Product", back_populates="import_logs")
