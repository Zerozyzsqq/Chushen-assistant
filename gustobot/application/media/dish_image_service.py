"""Generate and cache dish cover images via CogView."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
from loguru import logger

from gustobot.config import settings
from gustobot.infrastructure.core.paths import DISH_IMAGE_ROOT, ensure_upload_dirs


def sanitize_dish_name(raw: str) -> str:
    """Normalize dish name for search / image generation."""
    name = (raw or "").strip().replace("**", "")
    name = re.sub(r"[\U0001F300-\U0001FAFF]", "", name)
    name = re.sub(r"^(看到|识别|分享|这是|您的|您分享的?)+", "", name)
    name = re.sub(r"(图片了?|的照片?|成品图?|的样子?|教程|做法)$", "", name)
    name = re.sub(r"[了了的]$", "", name) if len(name) > 4 else name
    name = re.sub(r"\s+", "", name)
    return name[:24]


def _cache_path(dish_name: str) -> Path:
    clean = sanitize_dish_name(dish_name)
    digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]
    safe_label = re.sub(r"[^\w\u4e00-\u9fff-]+", "", clean)[:32] or "dish"
    return DISH_IMAGE_ROOT / f"{safe_label}_{digest}.jpg"


def _public_url(path: Path) -> str:
    return f"/uploads/dish_images/{path.name}"


async def _generate_cogview_url(dish_name: str) -> str:
    api_key = settings.IMAGE_GENERATION_API_KEY
    base_url = (settings.IMAGE_GENERATION_BASE_URL or "").rstrip("/")
    if not api_key or not base_url:
        raise RuntimeError("IMAGE_GENERATION_API_KEY / IMAGE_GENERATION_BASE_URL 未配置")

    prompt = (
        f"一张精美的中式家常菜「{dish_name}」成品照，俯拍，白色餐盘，"
        "自然光，高清美食摄影，色泽诱人，无文字无水印"
    )
    payload = {
        "model": settings.IMAGE_GENERATION_MODEL,
        "prompt": prompt,
        "size": settings.IMAGE_GENERATION_SIZE,
    }
    url = f"{base_url}/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, timeout=90) as resp:
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"CogView {resp.status}: {body[:200]}")
            import json
            result = json.loads(body)

    data = result.get("data") or []
    if not data:
        raise RuntimeError("CogView 未返回图片")
    image_url = data[0].get("url") or ""
    if not image_url:
        raise RuntimeError("CogView 响应缺少 url")
    return image_url


async def _download_image(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as resp:
            if resp.status != 200:
                raise RuntimeError(f"下载图片失败 {resp.status}")
            dest.write_bytes(await resp.read())


async def get_or_create_dish_image(dish_name: str) -> Dict[str, Any]:
    """Return cached or newly generated dish cover image metadata."""
    ensure_upload_dirs()
    clean = sanitize_dish_name(dish_name)
    if not clean:
        raise ValueError("菜名无效")

    cache = _cache_path(clean)
    if cache.is_file():
        return {
            "dish_name": clean,
            "image_url": _public_url(cache),
            "source": "cached",
            "ai_generated": True,
        }

    remote_url = await _generate_cogview_url(clean)
    await _download_image(remote_url, cache)
    logger.info("Generated dish image for {} -> {}", clean, cache.name)

    return {
        "dish_name": clean,
        "image_url": _public_url(cache),
        "source": "ai_generated",
        "ai_generated": True,
    }
