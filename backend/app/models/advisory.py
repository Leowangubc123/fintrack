from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class InvestmentAdvisorySubscription(Base):
    """投资顾问签约数据模型 - 时点数据"""
    __tablename__ = "investment_advisory_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    product_type = Column(String(20), nullable=False)  # '千1', '千3', '万2', '网格', '量化T', 'GWT'
    subscription_date = Column(Date, nullable=False)  # 签约日期
    asset_amount = Column(Numeric(15, 2), nullable=False)  # 签约资产(万元)
    advisory_income = Column(Numeric(15, 2), nullable=False)  # 投顾收入(元)
    original_households = Column(Integer, default=1)  # 原始户数
    converted_households = Column(Integer, default=1)  # 折算户数
    conversion_note = Column(String(255))  # 折算说明
    record_date = Column(Date, nullable=False)  # 数据日期(用于时点更新)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    member = relationship("Member", back_populates="advisory_subscriptions")
    group = relationship("Group", back_populates="advisory_subscriptions")


class InvestmentAdvisoryTarget(Base):
    """投资顾问目标设置模型"""
    __tablename__ = "investment_advisory_targets"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, unique=True)
    year = Column(Integer, nullable=False)  # 年度
    income_target = Column(Numeric(15, 2), default=0)  # 收入目标(万元)
    households_target = Column(Integer, default=0)  # 户数目标
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    group = relationship("Group", back_populates="advisory_target")
