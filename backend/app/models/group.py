from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    leader = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("Member", back_populates="group", cascade="all, delete-orphan")
