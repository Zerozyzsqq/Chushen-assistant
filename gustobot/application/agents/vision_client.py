"""Vision model helpers (Zhipu / OpenAI-compatible multimodal APIs)."""

from __future__ import annotations

import base64
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger
from PIL import Image

from gustobot.config import settings


def _chat_completions_url(base_url: str) -> str:
    base = (base_url or "").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


# glm-4.6 / glm-4 等为文本模型，识图需 *v* 系列
_VISION_MODEL_ALIASES = {
    "glm-4.6": "glm-4.6v-flash",
    "glm-4": "glm-4v-flash",
    "glm-4-plus": "glm-4v-plus",
}


def normalize_vision_model(model: str) -> str:
    model = (model or "").strip()
    if not model:
        return "glm-4.6v-flash"
    lowered = model.lower()
    if lowered in _VISION_MODEL_ALIASES:
        mapped = _VISION_MODEL_ALIASES[lowered]
        logger.warning("Vision model `%s` is text-only; using `%s` instead.", model, mapped)
        return mapped
    if lowered.startswith("glm-") and "v" not in lowered and "flash" not in lowered:
        mapped = "glm-4.6v-flash"
        logger.warning("Vision model `%s` may not support images; using `%s`.", model, mapped)
        return mapped
    return model


def encode_image_file(image_path: str, *, max_size: int = 1024) -> str:
    with Image.open(image_path) as img:
        width, height = img.size
        ratio = min(max_size / width, max_size / height, 1.0)
        if ratio < 1.0:
            img = img.resize((int(width * ratio), int(height * ratio)), Image.LANCZOS)
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8")


def build_vision_messages(user_query: str, image_b64: str) -> List[Dict[str, Any]]:
    prompt = (user_query or "").strip() or "请识别图片中的菜品名称和所有可见食材。"
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ],
        }
    ]


async def analyze_image(
    image_path: str,
    user_query: str = "",
    *,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> str:
    """Call vision API and return model text output."""
    api_key = settings.VISION_API_KEY or settings.LLM_API_KEY
    base_url = settings.VISION_BASE_URL or settings.LLM_BASE_URL
    model = normalize_vision_model(settings.VISION_MODEL)

    if not api_key or not base_url:
        raise RuntimeError("VISION_API_KEY / VISION_BASE_URL（或 LLM 回退配置）未设置")

    image_b64 = encode_image_file(image_path)
    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(build_vision_messages(user_query, image_b64))

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    url = _chat_completions_url(base_url)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    logger.info("Vision request model={} url={} image={}", model, url, image_path)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, timeout=90) as response:
            body_text = await response.text()
            if response.status != 200:
                logger.error(
                    "Vision API failed status={} body={}",
                    response.status,
                    body_text[:500],
                )
                raise RuntimeError(f"Vision API {response.status}: {body_text[:200]}")
            result = json.loads(body_text)

    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected vision API response: {result!r}") from exc


INGREDIENT_RECOGNITION_PROMPT = """你是一个食材识别助手。请识别图中所有可见食材，
只返回 JSON 数组，格式：["食材1","食材2",...]，
不要任何其他文字。"""


def parse_ingredients_json(text: str) -> List[str]:
    """Parse vision model output into a deduplicated ingredient name list."""
    raw = (text or "").strip()
    if not raw:
        return []

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()

    start = raw.find("[")
    end = raw.rfind("]")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]

    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")

    seen: set[str] = set()
    ingredients: List[str] = []
    for item in parsed:
        name = str(item).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ingredients.append(name)
    return ingredients


async def recognize_ingredients(image_path: str) -> List[str]:
    """Identify visible ingredients in an image; returns normalized name list."""
    raw = await analyze_image(
        image_path,
        INGREDIENT_RECOGNITION_PROMPT,
        temperature=0.1,
        max_tokens=512,
    )
    try:
        return parse_ingredients_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse ingredient JSON: {} raw={}", exc, raw[:300])
        raise RuntimeError(f"食材识别结果解析失败: {raw[:120]}") from exc
