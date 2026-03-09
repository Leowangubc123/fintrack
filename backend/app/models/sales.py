from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ProductTarget(Base):
    __tablename__ = "product_targets"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    target_amount = Column(Numeric(15, 2), nullable=False)


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    sale_date = Column(Date, nullable=False)
    import_batch_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    operator = Column(String(100))
    import_time = Column(DateTime(timezone=True), server_default=func.now())
    total_rows = Column(Integer)
    success_rows = Column(Integer)
    fail_rows = Column(Integer)
    file_name = Column(String(255))
