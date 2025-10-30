import uuid

from sqlalchemy import (VARCHAR, Boolean, Column, DateTime, ForeignKey,
                        Integer, Numeric, String, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Mall(Base):
    __tablename__ = "mall"

    mall_id = Column(VARCHAR(26), primary_key=True, index=True)
    name = Column(Text, nullable=False)
    type = Column(Text)
    coordinates = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationship to mall_information
    mall_information = relationship("MallInformation", back_populates="mall", uselist=False)


class MallInformation(Base):
    __tablename__ = "mall_information"

    mall_information_id = Column(VARCHAR(26), primary_key=True, index=True)
    mall_id = Column(VARCHAR(26), ForeignKey("mall.mall_id"), nullable=True, index=True)
    number_of_floors = Column(Numeric(10, 0))
    total_floor_area_m2 = Column(Numeric(10, 2))
    avg_daily_visitors = Column(Integer)
    management_fee_usd = Column(Numeric(10, 2))
    motorbike_fee_vnd = Column(Numeric(12, 0))
    car_fee_vnd = Column(Numeric(12, 0))
    electricity_policy = Column(Text)
    overtime_fee_policy = Column(Text)
    lease_term = Column(Text)
    deposit_policy = Column(Text)
    payment_policy = Column(Text)
    opening_year = Column(Integer)
    operating_hours_weekday = Column(VARCHAR(100))
    operating_hours_weekend = Column(VARCHAR(100))
    contact_phone = Column(VARCHAR(30))
    contact_email = Column(VARCHAR(100))
    website = Column(VARCHAR(200))
    parking_motorbike_spaces = Column(Integer)
    parking_car_spaces = Column(Integer)
    has_public_transport_access = Column(Boolean, default=False)
    has_loading_dock = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    has_escalator = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True))

    # Relationship to mall
    mall = relationship("Mall", back_populates="mall_information")


class Business(Base):
    __tablename__ = "business"

    id = Column(String, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    category = Column(Text)
    brand_tier = Column(Text)
    budget = Column(Numeric)
    required_size = Column(Numeric)
    visitor_capacity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BusinessHistory(Base):
    __tablename__ = "business_history"

    id = Column(String, primary_key=True, index=True)
    business_id = Column(String, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    mall_id = Column(VARCHAR(26), ForeignKey("mall.mall_id", ondelete="CASCADE"), nullable=False, index=True)
    revenue = Column(Numeric)
    success = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = {"schema": "platform_service"}

    search_history_id = Column(VARCHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(VARCHAR(36), nullable=False)
    search_query = Column(Text, nullable=True)
    brand_id = Column(VARCHAR(36), nullable=True)
    action_type = Column(VARCHAR(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<SearchHistory(id={self.search_history_id}, user_id={self.user_id}, action={self.action_type})>"
