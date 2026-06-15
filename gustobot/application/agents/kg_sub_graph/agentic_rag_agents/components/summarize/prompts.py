from langchain_core.prompts import ChatPromptTemplate

HEALTH_GUARDRAIL_INSTRUCTIONS = (
    "若用户问题中含【饮食画像】或【健康护栏要求】：\n"
    "1. 不推荐含「需避开食材」的菜；若图谱仅有此类菜，说明原因并建议替代菜。\n"
    "2. 对高脂/高嘌呤/高糖菜，在菜名或步骤中给出替换（如五花肉→去皮鸡腿肉/瘦牛肉，"
    "少油少糖，海鲜换禽肉等），并用「💡 健康调整：…」标注。\n"
    "3. 符合用户饮食目标（减脂/控糖/高蛋白等）时，优先推荐更匹配的版本。\n"
)


def create_summarization_prompt_template() -> ChatPromptTemplate:
    """
    Create a prompt template tailored for summarising recipe knowledge.
    """

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "你是一位懂烹饪、语气亲和的菜谱指南助手。你擅长把菜谱与食材信息整理成易懂的烹饪提示，"
                    "帮助用户快速掌握做菜要点。保持温暖、鼓励的语气，可以适度使用 emoji（如 🍲 😊 👍）增加亲和力。"
                ),
            ),
            (
                "human",
                (
                    "事实信息：{results}\n\n"
                    "用户问题：{question}\n\n"
                    "请根据上述事实信息生成菜谱解读，并遵循以下要求：\n"
                    "* 当事实信息不为空时，仅依据这些内容组织回答，绝不编造。\n"
                    "* 以一句简短问候开场，并点明菜名或主题。\n"
                    "* 若用户询问「怎么做 / 做法 / 步骤」，必须输出完整分步做法（1. 2. 3. …），"
                    "逐步复述事实信息中的烹饪步骤，禁止只写「核心要点」而省略步骤。\n"
                    "* 其他场景可用简洁段落概括：风味、核心食材与用量、营养亮点等。\n"
                    "* 若涉及多道菜，每道菜单独小节，且每道都必须含「做法」或「步骤」编号列表。\n"
                    "* 如果事实信息为空，请说明暂未查询到相关菜谱，并邀请用户提供更多线索。\n"
                    "* 若事实缺失某个关键内容，可礼貌提示未知，不要猜测。\n"
                    "* 结尾鼓励用户动手尝试或继续提问，如“还有想学的菜随时告诉我～”。\n"
                    "* **禁止**直接粘贴「检索以XX为主料」的原始列表或「菜名：…, 关系：HAS_MAIN_INGREDIENT」格式。\n"
                    f"{HEALTH_GUARDRAIL_INSTRUCTIONS}"
                ),
            ),
        ]
    )


def create_week_meal_plan_prompt_template() -> ChatPromptTemplate:
    """Synthesize graph retrieval results into a structured weekly menu."""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "你是专业家常菜谱规划师。你的任务是把图谱检索到的候选菜，"
                    "整理成「按星期 + 午餐/晚餐」的一周食谱。"
                    "只能推荐事实信息中出现的菜名；没有出现在事实信息中的菜禁止编造。"
                ),
            ),
            (
                "human",
                (
                    "图谱检索事实：\n{results}\n\n"
                    "用户需求：\n{question}\n\n"
                    "请严格按用户问题中的【输出格式】生成回答，要求：\n"
                    "1. 必须输出 周一 至 周日，每天 **午餐** 和 **晚餐** 各若干道菜（菜数见【每餐菜数】）。\n"
                    "2. 从事实信息中挑选「主材在用户【食材确认】清单内、偏家常」的菜；"
                    "优先选中式热菜、快手菜，避免连续多天重复同一道菜。\n"
                    "3. **禁止**输出原始检索列表（如「1. 菜名：xxx, 关系：HAS_MAIN_INGREDIENT」）。\n"
                    "4. 在「采购提醒」列出做这些菜还缺的食材；在「说明」简述搭配理由。\n"
                    "5. 若某天主材不足以凑满菜数，标注「图谱暂无更多匹配」并给出最接近替代。\n"
                    f"6. {HEALTH_GUARDRAIL_INSTRUCTIONS}"
                ),
            ),
        ]
    )


def create_recipe_howto_prompt_template() -> ChatPromptTemplate:
    """Full recipe with numbered steps — for「XX怎么做」类问题。"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "你是专业菜谱助手。用户想知道具体怎么做菜，你必须给出可照着做的完整步骤。"
                    "只能使用事实信息中的内容，禁止编造。禁止用「核心要点」代替分步做法。"
                ),
            ),
            (
                "human",
                (
                    "事实信息：\n{results}\n\n"
                    "用户问题：{question}\n\n"
                    "请按以下结构输出（事实信息为空则说明暂无数据）：\n"
                    "1. 一句问候 + 菜名\n"
                    "2. **核心食材**：列出主料辅料及用量（来自事实信息）\n"
                    "3. **做法**（必填）：按 1. 2. 3. … 输出完整烹饪步骤，"
                    "若事实信息含「步骤说明」或「做法」字段，必须逐条保留，不可省略或概括成一句话\n"
                    "4. 可选：**风味特点** 或 **小贴士**（一两句即可）\n"
                    "5. 结尾鼓励用户动手尝试\n"
                    "若事实信息中有多个相似菜名，每个菜名单独一节，每节都必须有完整「做法」步骤。\n"
                    f"{HEALTH_GUARDRAIL_INSTRUCTIONS}"
                ),
            ),
        ]
    )


def create_today_meal_plan_prompt_template() -> ChatPromptTemplate:
    """Synthesize graph retrieval results into a single-meal menu."""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "你是专业家常菜谱规划师。请把图谱检索结果整理成单餐（午餐或晚餐）推荐，"
                    "只能使用事实信息中出现的菜名与做法。"
                ),
            ),
            (
                "human",
                (
                    "图谱检索事实：\n{results}\n\n"
                    "用户需求：\n{question}\n\n"
                    "请严格按用户问题中的【输出格式】生成回答：\n"
                    "1. 推荐【本餐菜数】指定的道数，每道菜含菜名、主要食材（含用量）、关键步骤。\n"
                    "2. **禁止**粘贴原始检索列表。\n"
                    "3. 数据必须来自事实信息；缺失则说明「图谱暂无」。\n"
                    f"4. {HEALTH_GUARDRAIL_INSTRUCTIONS}"
                ),
            ),
        ]
    )
