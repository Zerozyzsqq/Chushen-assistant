"""Vision API endpoints (ingredient recognition from photos)."""

from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from gustobot.application.agents.vision_client import recognize_ingredients
from gustobot.infrastructure.core.paths import resolve_upload_path

router = APIRouter()


class IngredientVisionRequest(BaseModel):
    image_path: str = Field(..., description="Server-side path returned by /upload/image")


class IngredientVisionResponse(BaseModel):
    success: bool = True
    ingredients: List[str]
    image_path: str


@router.post("/ingredients", response_model=IngredientVisionResponse)
async def detect_ingredients(request: IngredientVisionRequest) -> IngredientVisionResponse:
    """Recognize visible ingredients in an uploaded image (JSON array only from vision model)."""
    resolved = resolve_upload_path(request.image_path)
    if not resolved:
        raise HTTPException(status_code=404, detail="找不到上传的图片文件，请重新上传。")

    try:
        ingredients = await recognize_ingredients(str(resolved))
    except RuntimeError as exc:
        logger.error("Ingredient recognition failed: {}", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not ingredients:
        raise HTTPException(status_code=422, detail="未识别到食材，请换一张更清晰的图片。")

    return IngredientVisionResponse(
        ingredients=ingredients,
        image_path=request.image_path,
    )
