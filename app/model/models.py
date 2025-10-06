from sqlalchemy import Column, String, Integer, Float, Boolean, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())


class Mall(Base):
    __tablename__ = "mall"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(Text, nullable=False)
    type = Column(Text)
    avg_daily_visitors = Column(Integer)
    rent_price_usd = Column(Numeric(10, 2))
    management_fee_usd = Column(Numeric(10, 2))
    vat_percent = Column(Numeric(5, 2))
    motorbike_fee_vnd = Column(Numeric(12, 0))
    car_fee_vnd = Column(Numeric(12, 0))
    electricity_policy = Column(Text)
    overtime_fee_policy = Column(Text)
    lease_term = Column(Text)
    deposit_policy = Column(Text)
    payment_policy = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Zone(Base):
    __tablename__ = "zone"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Booth(Base):
    __tablename__ = "booth"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False, index=True)
    size_m2 = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    floor_level = Column(Integer)
    zone = Column(String(10), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Business(Base):
    __tablename__ = "business"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(Text, nullable=False)
    category = Column(Text)
    brand_tier = Column(Text)
    budget = Column(Numeric)
    required_size = Column(Numeric)
    visitor_capacity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BusinessHistory(Base):
    __tablename__ = "business_history"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    business_id = Column(String, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False, index=True)
    revenue = Column(Numeric)
    success = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
