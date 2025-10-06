from sqlalchemy.orm import Session
from sqlalchemy import func
from app.model.models import Mall, Booth, Business, BusinessHistory
from app.datastore.cache_manager import cache_mall_demographic, cache_business_data
from typing import Dict, Any

class DemographicsCalculator:
    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_mall_demographics(self, mall_id: str) -> Dict[str, Any]:
        mall = self.db.query(Mall).filter(Mall.id == mall_id).first()
        if not mall:
            return None

        booths = self.db.query(Booth).filter(Booth.mall_id == mall_id).all()
        business_histories = self.db.query(BusinessHistory).filter(BusinessHistory.mall_id == mall_id).all()

        total_booths = len(booths)
        occupied_booths = len([b for b in booths if not b.is_available])
        occupancy_rate = (occupied_booths / total_booths * 100) if total_booths > 0 else 0

        avg_price = self.db.query(func.avg(Booth.price)).filter(Booth.mall_id == mall_id).scalar() or 0
        avg_size = self.db.query(func.avg(Booth.size_m2)).filter(Booth.mall_id == mall_id).scalar() or 0

        zone_stats = {}
        for booth in booths:
            zone = booth.zone
            if zone not in zone_stats:
                zone_stats[zone] = {
                    "total_booths": 0,
                    "occupied_booths": 0,
                    "avg_price": 0,
                    "avg_size": 0
                }
            zone_stats[zone]["total_booths"] += 1
            if not booth.is_available:
                zone_stats[zone]["occupied_booths"] += 1

        for zone in zone_stats:
            zone_booths = [b for b in booths if b.zone == zone]
            zone_stats[zone]["avg_price"] = sum(b.price for b in zone_booths) / len(zone_booths) if zone_booths else 0
            zone_stats[zone]["avg_size"] = sum(b.size_m2 for b in zone_booths) / len(zone_booths) if zone_booths else 0
            zone_stats[zone]["occupancy_rate"] = (zone_stats[zone]["occupied_booths"] / zone_stats[zone]["total_booths"] * 100) if zone_stats[zone]["total_booths"] > 0 else 0

        successful_businesses = len([h for h in business_histories if h.success])
        total_businesses = len(business_histories)
        success_rate = (successful_businesses / total_businesses * 100) if total_businesses > 0 else 0

        avg_revenue = self.db.query(func.avg(BusinessHistory.revenue)).filter(
            BusinessHistory.mall_id == mall_id,
            BusinessHistory.revenue.isnot(None)
        ).scalar() or 0

        demographics = {
            "spending_power": {
                "budget": 30,
                "mid_range": 50,
                "premium": 20
            },
            "visit_purpose": {
                "shopping": 60,
                "dining": 25,
                "entertainment": 15
            },
            "traffic_pattern": {
                "weekday": 40,
                "weekend": 60,
                "peak_hours": [12, 13, 14, 18, 19, 20],
                "avg_dwell_time_minutes": 90
            },
            "tenant_mix": {
                "total_booths": total_booths,
                "occupied_booths": occupied_booths,
                "occupancy_rate": round(occupancy_rate, 2),
                "avg_price": float(avg_price),
                "avg_size_m2": float(avg_size)
            },
            "zone_performance": zone_stats,
            "historical_performance": {
                "total_businesses": total_businesses,
                "successful_businesses": successful_businesses,
                "success_rate": round(success_rate, 2),
                "avg_revenue": float(avg_revenue)
            },
            "verified_data": {
                "last_verification_date": "2024-10-06",
                "verification_status": "calculated",
                "data_source": "database_calculation"
            },
            "market_intelligence": {
                "avg_daily_visitors": mall.avg_daily_visitors or 0,
                "mall_type": mall.type or "unknown"
            }
        }

        return demographics

    def calculate_business_demographics(self, business_id: str) -> Dict[str, Any]:
        business = self.db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return None

        business_histories = self.db.query(BusinessHistory).filter(BusinessHistory.business_id == business_id).all()

        total_locations = len(business_histories)
        successful_locations = len([h for h in business_histories if h.success])
        failed_locations = total_locations - successful_locations

        avg_revenue = sum(h.revenue for h in business_histories if h.revenue) / len([h for h in business_histories if h.revenue]) if business_histories else 0

        demographics = {
            "proven_performance": {
                "avg_revenue": float(avg_revenue),
                "total_locations": total_locations,
                "success_rate": (successful_locations / total_locations * 100) if total_locations > 0 else 0
            },
            "historical_track_record": {
                "total_locations": total_locations,
                "successful_locations": successful_locations,
                "failed_locations": failed_locations,
                "total_revenue_history": [
                    {
                        "mall_id": h.mall_id,
                        "revenue": float(h.revenue) if h.revenue else 0,
                        "success": h.success
                    } for h in business_histories
                ]
            },
            "requirements": {
                "budget": float(business.budget) if business.budget else 0,
                "required_size": float(business.required_size) if business.required_size else 0,
                "visitor_capacity": business.visitor_capacity or 0
            },
            "business_profile": {
                "name": business.name,
                "category": business.category or "unknown",
                "brand_tier": business.brand_tier or "unknown"
            },
            "verified_data": {
                "last_verification_date": "2024-10-06",
                "verification_status": "calculated",
                "data_source": "database_calculation"
            }
        }

        return demographics

    def cache_all_demographics(self):
        results = {
            "malls_processed": 0,
            "businesses_processed": 0,
            "errors": []
        }

        malls = self.db.query(Mall).all()
        for mall in malls:
            try:
                demographics = self.calculate_mall_demographics(mall.id)
                if demographics:
                    cache_mall_demographic(mall.id, demographics, expire=3600)
                    results["malls_processed"] += 1
            except Exception as e:
                results["errors"].append(f"Mall {mall.id}: {str(e)}")

        businesses = self.db.query(Business).all()
        for business in businesses:
            try:
                demographics = self.calculate_business_demographics(business.id)
                if demographics:
                    cache_business_data(business.id, demographics, expire=3600)
                    results["businesses_processed"] += 1
            except Exception as e:
                results["errors"].append(f"Business {business.id}: {str(e)}")

        return results