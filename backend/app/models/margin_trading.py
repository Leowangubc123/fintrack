from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class MarginBalanceMember(Base):
    """个人两融余额（时点/日均）"""
    __tablename__ = "margin_balance_members"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    development_balance = Column(Numeric(15, 2), default=0)  # 开发关系余额(万)
    service_balance = Column(Numeric(15, 2), default=0)    # 服务关系余额(万)
    balance_type = Column(String(10), nullable=False)       # 'spot' 时点 / 'daily' 日均
    record_week = Column(String(10), nullable=False)        # '2026-W20'
    record_date = Column(Date, nullable=False)              # 数据截止日期
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarginBalanceGroup(Base):
    """营业部两融余额"""
    __tablename__ = "margin_balance_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    spot_balance = Column(Numeric(15, 2), default=0)        # 时点余额(万)
    daily_balance = Column(Numeric(15, 2), default=0)       # 日均余额(万)
    record_week = Column(String(10), nullable=False)
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarginIncome(Base):
    """营业部息费收入"""
    __tablename__ = "margin_income"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    income_amount = Column(Numeric(15, 2), default=0)       # 本周息费收入(万)
    record_week = Column(String(10), nullable=False)
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarginNewAccount(Base):
    """两融新开户"""
    __tablename__ = "margin_new_accounts"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    customer_name = Column(String(50), nullable=False)
    asset_amount = Column(Numeric(15, 2), default=0)        # 开户资产(万)
    account_date = Column(Date, nullable=False)             # 开户日期
    record_week = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarginTarget(Base):
    """两融考核指标"""
    __tablename__ = "margin_targets"
    __table_args__ = (
        UniqueConstraint('group_id', 'year', name='uq_margin_target_group_year'),
    )

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    year = Column(Integer, nullable=False)
    income_target = Column(Numeric(15, 2), default=0)       # 息费收入目标(万)
    account_target = Column(Integer, default=0)             # 开户数量目标
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MarginImportLog(Base):
    """两融数据导入日志"""
    __tablename__ = "margin_import_logs"

    id = Column(Integer, primary_key=True, index=True)
    import_date = Column(Date, nullable=False)
    data_type = Column(String(20), nullable=False)          # 'member_balance', 'group_balance', 'income', 'new_account'
    record_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    operator = Column(String(50), default='admin')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
