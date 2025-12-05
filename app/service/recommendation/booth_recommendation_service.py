from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.exception.recommendation_exceptions import DemographicsError
from app.service.recommendation.booth_filter_extractor import BoothFilterExtractor
from app.service.recommendation.booth_repository import BoothRepositoryInstance
from app.service.recommendation.repositories import BrandDemographicDataSource, MallDemographicDataSource
from app.service.recommendation.scoring import BoothScorer
from app.service.recommendation.services import BatchMatchService
from app.utils.logger import api_logger


class BoothRecommendationService:
    def __init__(self):
        self.booth_repository = BoothRepositoryInstance
        self.batch_match_service = BatchMatchService()
        self.filter_extractor = BoothFilterExtractor()

    def _check_waitlist_status(self, brand_id: str, booth_ids: List[str]) -> Dict[str, bool]:
        if not booth_ids:
            return {}

        db: Session = next(get_db())
        try:
            query = text(
                """
                SELECT booth_id
                FROM platform_service.brand_mall_waitlist
                WHERE brand_id = :brand_id AND booth_id = ANY(:booth_ids)
                """
            )
            results = db.execute(query, {"brand_id": brand_id, "booth_ids": booth_ids}).fetchall()
            waitlisted_booth_ids = {row.booth_id for row in results}
            return {booth_id: booth_id in waitlisted_booth_ids for booth_id in booth_ids}
        except Exception as e:
            api_logger.error(f"Error checking waitlist status: {str(e)}")
            return {booth_id: False for booth_id in booth_ids}
        finally:
            db.close()

    async def get_recommended_booths(
        self,
        brand_id: str,
        filters: Optional[Dict[str, Any]] = None,
        top_mall_limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if filters is None:
            filters = await self.filter_extractor.extract_filters_from_brand(brand_id)

        brand_data = BrandDemographicDataSource.get_by_id(brand_id)
        if not brand_data:
            raise DemographicsError(
                entity_type="brand",
                entity_id=brand_id,
                message=f"Brand demographics not found for brand_id={brand_id}",
            )

        brand_meta = brand_data.get("meta_data", brand_data)

        all_mall_ids = self._get_all_mall_ids()
        if not all_mall_ids:
            api_logger.warning("No malls found in database")
            return []

        mall_scores = self.batch_match_service.calculate_batch_scores(brand_id, all_mall_ids)
        mall_scores.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        top_malls = mall_scores[:top_mall_limit]
        top_mall_ids = [mall.get("mall_id") for mall in top_malls if mall.get("final_score") is not None]

        if not top_mall_ids:
            api_logger.warning(f"No compatible malls found for brand_id={brand_id}")
            return []

        mall_scores_dict = {mall.get("mall_id"): mall.get("final_score", 0) for mall in top_malls}

        min_size = filters.get("min_size")
        max_size = filters.get("max_size")
        max_price = filters.get("max_price")
        category_id = filters.get("category_id")
        preferred_floors = filters.get("preferred_floors")

        booths = self.booth_repository.get_available_booths_by_mall_ids(
            mall_ids=top_mall_ids,
            min_size=min_size,
            max_size=max_size,
            max_price=max_price,
            category_id=category_id,
            preferred_floors=preferred_floors,
        )

        if not booths:
            api_logger.warning(f"No available booths found for brand_id={brand_id} with filters")
            return []

        booth_ids = [booth.get("booth_id") for booth in booths if booth.get("booth_id")]
        waitlist_status = self._check_waitlist_status(brand_id, booth_ids)

        scored_booths = []
        for booth in booths:
            booth_id = booth.get("booth_id")
            mall_id = booth.get("mall_id")
            mall_score = mall_scores_dict.get(mall_id, 0)

            try:
                booth_for_scoring = booth.copy()
                if booth_id:
                    details = self.booth_repository.get_booth_with_details(booth_id)
                    if details:
                        booth_for_scoring.update(details)

                scorer = BoothScorer(brand_meta, booth_for_scoring, mall_score)
                result = scorer.compute_final_score()

                scored_booth = {
                    "booth_id": booth.get("booth_id"),
                    "booth_name": booth.get("booth_name") or booth_for_scoring.get("name"),
                    "booth_size": booth.get("frontage_width_m") or booth_for_scoring.get("frontage_width_m"),
                    "booth_price": booth.get("rent_price") or booth_for_scoring.get("rent_price"),
                    "booth_image": booth.get("booth_image") or booth_for_scoring.get("booth_image"),
                    "floor_level": booth.get("floor_level") or booth_for_scoring.get("floor_level"),
                    "mall_id": mall_id,
                    "mall_name": booth.get("mall_name"),
                    "mall_logo": booth.get("mall_logo") or booth_for_scoring.get("mall_logo"),
                    "mall_address": booth.get("mall_address") or booth_for_scoring.get("mall_address"),
                    "is_on_waitlist": waitlist_status.get(booth_id, False),
                    "_composite_score": result.get("composite_score", 0),
                }
                scored_booths.append(scored_booth)
            except Exception as e:
                api_logger.error(f"Error scoring booth {booth_id}: {str(e)}")
                continue

        scored_booths.sort(key=lambda x: x.get("_composite_score", 0), reverse=True)

        for booth in scored_booths:
            booth.pop("_composite_score", None)

        return scored_booths

    async def get_recommended_booths_by_mall(
        self,
        brand_id: str,
        mall_id: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if filters is None:
            filters = await self.filter_extractor.extract_filters_from_brand(brand_id)

        brand_data = BrandDemographicDataSource.get_by_id(brand_id)
        if not brand_data:
            raise DemographicsError(
                entity_type="brand",
                entity_id=brand_id,
                message=f"Brand demographics not found for brand_id={brand_id}",
            )

        mall_data = MallDemographicDataSource.get_by_id(mall_id)
        if not mall_data:
            raise DemographicsError(
                entity_type="mall",
                entity_id=mall_id,
                message=f"Mall demographics not found for mall_id={mall_id}",
            )

        brand_meta = brand_data.get("meta_data", brand_data)
        mall_meta = mall_data.get("meta_data", mall_data)

        from app.service.recommendation.scoring import BusinessMatchScorer

        scorer = BusinessMatchScorer(brand_meta, mall_meta)
        mall_result = scorer.compute_final_score()
        mall_score = mall_result.get("final_score", 0)

        min_size = filters.get("min_size")
        max_size = filters.get("max_size")
        max_price = filters.get("max_price")
        category_id = filters.get("category_id")
        preferred_floors = filters.get("preferred_floors")

        booths = self.booth_repository.get_available_booths_by_mall_id(
            mall_id=mall_id,
            min_size=min_size,
            max_size=max_size,
            max_price=max_price,
            category_id=category_id,
            preferred_floors=preferred_floors,
        )

        if not booths:
            api_logger.warning(f"No available booths found for mall_id={mall_id} with filters")
            return []

        booth_ids = [booth.get("booth_id") for booth in booths if booth.get("booth_id")]
        waitlist_status = self._check_waitlist_status(brand_id, booth_ids)

        scored_booths = []
        for booth in booths:
            booth_id = booth.get("booth_id")

            try:
                booth_for_scoring = booth.copy()
                if booth_id:
                    details = self.booth_repository.get_booth_with_details(booth_id)
                    if details:
                        booth_for_scoring.update(details)

                scorer = BoothScorer(brand_meta, booth_for_scoring, mall_score)
                result = scorer.compute_final_score()

                scored_booth = {
                    "booth_id": booth.get("booth_id"),
                    "booth_name": booth.get("booth_name") or booth_for_scoring.get("name"),
                    "booth_size": booth.get("frontage_width_m") or booth_for_scoring.get("frontage_width_m"),
                    "booth_price": booth.get("rent_price") or booth_for_scoring.get("rent_price"),
                    "booth_image": booth.get("booth_image") or booth_for_scoring.get("booth_image"),
                    "floor_level": booth.get("floor_level") or booth_for_scoring.get("floor_level"),
                    "mall_id": mall_id,
                    "mall_name": booth.get("mall_name"),
                    "mall_logo": booth.get("mall_logo") or booth_for_scoring.get("mall_logo"),
                    "mall_address": booth.get("mall_address") or booth_for_scoring.get("mall_address"),
                    "is_on_waitlist": waitlist_status.get(booth_id, False),
                    "_composite_score": result.get("composite_score", 0),
                }
                scored_booths.append(scored_booth)
            except Exception as e:
                api_logger.error(f"Error scoring booth {booth_id}: {str(e)}")
                continue

        scored_booths.sort(key=lambda x: x.get("_composite_score", 0), reverse=True)

        for booth in scored_booths:
            booth.pop("_composite_score", None)

        return scored_booths

    def _get_all_mall_ids(self) -> List[str]:
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        from app.config.db import get_db

        db: Session = next(get_db())
        try:
            query = text("SELECT mall_id FROM platform_service.mall WHERE status = 'ACTIVE'")
            results = db.execute(query).fetchall()
            return [row.mall_id for row in results]
        except Exception as e:
            api_logger.error(f"Error fetching mall IDs: {str(e)}")
            return []
        finally:
            db.close()
