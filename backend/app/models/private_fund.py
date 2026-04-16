from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, Float, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class PrivateFundProduct(Base):
    """私募产品模型"""
    __tablename__ = "private_fund_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True)
    distribution_scope = Column(String(100), default="全国")
    strategy_type = Column(String(50), nullable=False)
    custom_strategy = Column(String(100))
    risk_level = Column(String(10), nullable=False)  # R3/R4/R5
    lock_period = Column(String(50))
    open_period = Column(String(100))
    sales_coefficient = Column(Numeric(4, 2), nullable=False, default=1.0)
    holding_coefficient = Column(Numeric(4, 2), default=1.0)
    subscription_fee = Column(Numeric(5, 2))
    service_fee = Column(Numeric(5, 2))
    management_fee = Column(Numeric(5, 2))
    performance_fee = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("PrivateFundTransaction", back_populates="product", cascade="all, delete-orphan")


class PrivateFundTransaction(Base):
    """私募交易记录模型"""
    __tablename__ = "private_fund_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("private_fund_products.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'sale' 或 'redeem'
    sales_coefficient = Column(Numeric(4, 2))
    assessed_amount = Column(Numeric(15, 2))
    holding_coefficient = Column(Numeric(4, 2))
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("PrivateFundProduct", back_populates="transactions")
    member = relationship("Member", back_populates="private_fund_transactions")


class PrivateFundHolding(Base):
    """私募保有数据模型 - 时点数据"""
    __tablename__ = "private_fund_holdings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("private_fund_products.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    holding_market_value = Column(Numeric(15, 2), nullable=False)  # 保有市值
    holding_coefficient = Column(Numeric(4, 2), nullable=False)  # 保有系数
    assessed_holding = Column(Numeric(15, 2), nullable=False)  # 考核保有量
    record_date = Column(Date, nullable=False)  # 数据日期
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("PrivateFundProduct")
    group = relationship("Group")


class PrivateFundTarget(Base):
    """私募销售考核目标模型"""
    __tablename__ = "private_fund_targets"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    year = Column(Integer, nullable=False)
    sales_target = Column(Numeric(15, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("group_id", "year", name="uix_private_fund_target_group_year"),
    )
