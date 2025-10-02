from sqlalchemy import Column, String, Integer, Float, Boolean, Numeric, JSON, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())


class Mall(Base):
    __tablename__ = "mall"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, nullable=False)
    type = Column(String)
    avg_daily_visitors = Column(Integer)
    demographic = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Booth(Base):
    __tablename__ = "booth"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False)
    size_m2 = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    floor_level = Column(Integer)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Business(Base):
    __tablename__ = "business"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, nullable=False)
    category = Column(String)
    brand_tier = Column(String)
    budget = Column(Numeric)
    required_size = Column(Numeric)
    visitor_capacity = Column(Integer)
    target_demographic = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BusinessHistory(Base):
    __tablename__ = "business_history"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    business_id = Column(String, ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False)
    revenue = Column(Numeric)
    success = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
