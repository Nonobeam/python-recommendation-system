from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from .models import Base, generate_uuid


class MallDemographics(Base):
    __tablename__ = "mall_demographics"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False, unique=True)
    spending_power = Column(JSON)
    visit_purpose = Column(JSON)
    traffic_pattern = Column(JSON)
    tenant_mix = Column(JSON)
    zone_performance = Column(JSON)
    historical_performance = Column(JSON)
    verified_data = Column(JSON)
    market_intelligence = Column(JSON)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BusinessDemographics(Base):
    __tablename__ = "business_demographics"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    business_id = Column(String, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, unique=True)
    proven_performance = Column(JSON)
    historical_track_record = Column(JSON)
    requirements = Column(JSON)
    search_behavior = Column(JSON)
    business_profile = Column(JSON)
    financial_health = Column(JSON)
    market_fit_signals = Column(JSON)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())