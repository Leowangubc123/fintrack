from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    scope = Column(String(100), default="public_fund,private_fund,advisory,margin_trading")  # 功能可见范围

    group = relationship("Group", back_populates="members")
    sales_records = relationship("SalesRecord", back_populates="member", cascade="all, delete-orphan")
    targets = relationship("ProductTarget", back_populates="member")
    private_fund_transactions = relationship("PrivateFundTransaction", back_populates="member", cascade="all, delete-orphan")
    advisory_subscriptions = relationship("InvestmentAdvisorySubscription", back_populates="member", cascade="all, delete-orphan")
