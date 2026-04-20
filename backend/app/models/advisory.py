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
    product_type = Column(String(20), nullable=False)  # '万2', '千1', '千3', 'ETF投顾', '量化T策略', 'GWT'
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
    current_income = Column(Numeric(15, 2), default=0)  # 实际收入(万元)
    current_households = Column(Integer, default=0)  # 实际户数
    assessed_households = Column(Integer, default=0)  # 考核户数(折算系数后)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    group = relationship("Group", back_populates="advisory_target")


class AdvisoryImportLog(Base):
    """投顾数据导入日志"""
    __tablename__ = "advisory_import_logs"

    id = Column(Integer, primary_key=True, index=True)
    import_date = Column(Date, nullable=False)
    product_type = Column(String(20), nullable=False)
    record_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    operator = Column(String(50), default='admin')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
