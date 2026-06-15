"""Single-user dietary profile helpers (no auth — passed from client per request)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DietaryProfile(BaseModel):
    """Client-side diet preferences / health constraints."""

    goals: List[str] = Field(default_factory=list, description="e.g. 减脂, 高蛋白, 低脂, 控糖")
    avoid_ingredients: List[str] = Field(default_factory=list, description="Allergies / dislikes")
    health_conditions: List[str] = Field(default_factory=list, description="e.g. 痛风, 高血压")
    spice_level: Optional[str] = Field(None, description="none | mild | medium | hot")
    notes: Optional[str] = Field(None, description="Free-form notes")


def parse_dietary_profile(raw: Any) -> Optional[DietaryProfile]:
    if raw is None:
        return None
    if isinstance(raw, DietaryProfile):
        return raw
    if isinstance(raw, dict):
        try:
            return DietaryProfile.model_validate(raw)
        except Exception:
            return None
    return None


def format_dietary_block(profile: Optional[DietaryProfile]) -> str:
    """Append to agent message so summarize / planner can read constraints."""
    if profile is None:
        return ""

    parts: List[str] = ["【饮食画像】"]
    if profile.goals:
        parts.append(f"- 饮食目标：{'、'.join(profile.goals)}")
    if profile.health_conditions:
        parts.append(f"- 健康状况/禁忌：{'、'.join(profile.health_conditions)}")
    if profile.avoid_ingredients:
        parts.append(f"- 需避开食材：{'、'.join(profile.avoid_ingredients)}")
    if profile.spice_level:
        level_map = {
            "none": "不辣",
            "mild": "微辣",
            "medium": "中辣",
            "hot": "重辣",
        }
        parts.append(f"- 辣度偏好：{level_map.get(profile.spice_level, profile.spice_level)}")
    if profile.notes and profile.notes.strip():
        parts.append(f"- 补充说明：{profile.notes.strip()}")

    if len(parts) == 1:
        return ""
    parts.append(
        "【健康护栏要求】推荐或总结菜谱时：① 避开上述禁忌食材；"
        "② 若原菜与用户目标冲突（如减脂却推荐重油菜），说明原因并给出食材/做法替换"
        "（例：五花肉→去皮鸡腿肉或瘦牛肉，少油少糖）；"
        "③ 在每道菜或回答末尾用「💡 健康调整」简短说明改动。"
    )
    return "\n".join(parts)


def dietary_profile_from_request(data: Optional[Dict[str, Any]]) -> Optional[DietaryProfile]:
    return parse_dietary_profile(data)
