"""Media API (dish cover images)."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from gustobot.application.media.dish_image_service import get_or_create_dish_image

router = APIRouter()


class DishImageResponse(BaseModel):
    dish_name: str
    image_url: str
    source: str = Field(description="cached | ai_generated")
    ai_generated: bool = True


@router.get("/dish-image", response_model=DishImageResponse)
async def dish_image(dish_name: str = Query(..., min_length=1, max_length=64)) -> DishImageResponse:
    """Get or generate a dish cover image (cached under uploads/dish_images/)."""
    try:
        result = await get_or_create_dish_image(dish_name)
        return DishImageResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Dish image failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
