"""HTTP routes for recommender-service."""

from __future__ import annotations

from fastapi import APIRouter

from anime_shared.schemas import RecommendationRequest, RecommendationResponse

from recommender_service import recommender

router = APIRouter(tags=["recommender"])


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest) -> RecommendationResponse:
    return recommender.recommend(request.query)
