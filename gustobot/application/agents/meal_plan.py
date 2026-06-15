"""Helpers for ingredient-based meal planning queries."""

from __future__ import annotations

import re
from typing import List, Literal, Optional

MealPlan = Literal["today_lunch", "today_dinner", "week"]

MEAL_PLAN_LABELS = {
    "today_lunch": "今日午餐",
    "today_dinner": "今日晚餐",
    "week": "一周菜谱",
}


def dishes_per_meal(household_size: int) -> int:
    """Recommend dish count per meal based on household size."""
    size = max(1, min(household_size, 12))
    if size <= 2:
        return 1
    if size <= 4:
        return 2
    return 3


def parse_household_size_from_question(question: str) -> Optional[int]:
    match = re.search(r"【用餐人数】\s*(\d+)\s*人", question or "")
    if match:
        return int(match.group(1))
    return None


def build_ingredient_meal_query(
    ingredients: List[str],
    meal_plan: MealPlan = "today_dinner",
    household_size: int = 2,
    dietary_block: str = "",
) -> str:
    """Build a graphrag-friendly user message from confirmed ingredients."""
    cleaned = [name.strip() for name in ingredients if name and name.strip()]
    joined = "、".join(cleaned)
    scope = MEAL_PLAN_LABELS.get(meal_plan, MEAL_PLAN_LABELS["today_dinner"])
    people = max(1, min(household_size, 12))
    per_meal = dishes_per_meal(people)

    graph_hint = (
        "请使用菜谱知识图谱工具检索候选菜（predefined_cypher：dishes_by_main_ingredient、"
        "dishes_with_ingredients、dish_complete_info、ingredients_of_dish）。"
        "检索时合并所有已有食材，优先选「主材在用户食材清单内、做法偏家常」的菜，"
        "不要为每种食材各输出一条检索列表。"
    )

    output_format_week = (
        "【输出格式 — 必须严格遵守，禁止粘贴原始检索列表】\n"
        "## 一周食谱（{people}人）\n"
        "### 周一\n"
        "- **午餐**：菜名1、菜名2\n"
        "- **晚餐**：菜名3、菜名4\n"
        "### 周二\n"
        "- **午餐**：…\n"
        "- **晚餐**：…\n"
        "（依此类推直到周日）\n"
        "### 采购提醒\n"
        "- 还缺：…\n"
        "### 说明\n"
        "- 每道菜一句话说明选用理由（需来自图谱检索结果）"
    ).format(people=people)

    output_format_today = (
        "【输出格式 — 必须严格遵守，禁止粘贴原始检索列表】\n"
        f"## {scope}（{people}人，{per_meal}道菜）\n"
        "1. **菜名**\n"
        "   - 主要食材：…（含用量，来自图谱）\n"
        "   - 关键步骤：…（来自图谱，3-5步）\n"
        "2. **菜名** …"
    )

    dietary_section = f"\n{dietary_block}\n" if dietary_block else ""

    if meal_plan == "week":
        return (
            f"【任务类型】一周家常菜谱规划\n"
            f"【食材确认】{joined}\n"
            f"【用餐人数】{people}人\n"
            f"【规划范围】{scope}\n"
            f"【每餐菜数】午餐 {per_meal} 道，晚餐 {per_meal} 道\n"
            f"{graph_hint}\n"
            f"{output_format_week}\n"
            f"{dietary_section}"
            "请从检索结果中挑选 7 天不重样的家常菜组合；"
            "若图谱无合适菜，标注「图谱暂无」并给出最接近替代，不要编造做法。"
        )

    return (
        f"【任务类型】单餐菜谱推荐\n"
        f"【食材确认】{joined}\n"
        f"【用餐人数】{people}人\n"
        f"【规划范围】{scope}\n"
        f"【本餐菜数】{per_meal} 道\n"
        f"{graph_hint}\n"
        f"{output_format_today}\n"
        f"{dietary_section}"
        "优先使用图谱中的做法与用量；若图谱无该菜，请说明并仅给出保守建议。"
    )


def format_user_display_message(
    ingredients: List[str],
    meal_plan: MealPlan = "today_dinner",
    household_size: int = 2,
) -> str:
    """Short message shown in chat history for the confirm step."""
    joined = "、".join(ingredients)
    scope = MEAL_PLAN_LABELS.get(meal_plan, MEAL_PLAN_LABELS["today_dinner"])
    people = max(1, min(household_size, 12))
    return f"已确认食材：{joined} · {scope} · {people}人用餐 · 请推荐菜谱"
