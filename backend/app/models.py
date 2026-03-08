"""
FinTrack Database Models

SQLAlchemy models for financial product sales management system.
"""

import enum
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ProductStatus(str, enum.Enum):
    """Product status enumeration."""
    COLLECTING = "募集中"
    ENDED = "已结束"
    PENDING = "待开始"
    ARCHIVED = "已归档"


class ProductType(str, enum.Enum):
    """Product type enumeration."""
    PUBLIC = "公募产品"
    PRIVATE = "私募产品"


class Group(Base):
    """Sales groups/departments model."""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    leader = Column(String(100))
    region = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    remark = Column(Text)

    # Relationships
    members = relationship("Member", back_populates="group", cascade="all, delete-orphan")


class Member(Base):
    """Sales members model."""
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    employee_id = Column(String(50), unique=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    joined_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="active")

    # Relationships
    group = relationship("Group", back_populates="members")
    sales_records = relationship("SalesRecord", back_populates="member", cascade="all, delete-orphan")


class Product(Base):
    """Financial products model."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    alias = Column(String(200))
    type = Column(SQLEnum(ProductType), nullable=False)
    issuer = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_target = Column(Numeric(15, 2), nullable=False)
    yield_rate = Column(Numeric(5, 2))
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.COLLECTING, nullable=False)
    description = Column(Text)
    archived_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    targets = relationship("ProductTarget", back_populates="product", cascade="all, delete-orphan")
    sales_records = relationship("SalesRecord", back_populates="product", cascade="all, delete-orphan")
    import_logs = relationship("ImportLog", back_populates="product", cascade="all, delete-orphan")


class ProductTarget(Base):
    """Sales task allocation model."""
    __tablename__ = "product_targets"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    target_amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="targets")


class SalesRecord(Base):
    """Individual sales records model."""
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    sale_date = Column(Date, nullable=False)
    customer_count = Column(Integer, default=1)
    remark = Column(Text)
    import_batch_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="sales_records")
    member = relationship("Member", back_populates="sales_records")


class ImportLog(Base):
    """Import operation logs model."""
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    operator = Column(String(100))
    import_time = Column(DateTime(timezone=True), server_default=func.now())
    total_rows = Column(Integer)
    success_rows = Column(Integer)
    fail_rows = Column(Integer)
    file_name = Column(String(255))

    # Relationships
    product = relationship("Product", back_populates="import_logs")


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")  # admin, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
