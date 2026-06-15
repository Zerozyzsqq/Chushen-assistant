# GustoBot Prompt 评测 — 飞书/Excel 列头 + 60 条 P0 题目

> **用法**：复制「§1 列头说明」建表 → 复制「§2 题目表」粘贴到 Sheet1 → 评测时在右侧追加「实际结果列」填数。  
> **版本**：v1.0 | **Prompt 基线**：lg_prompts.py + kg_prompts.py + multi_tool.py KB 内联 Prompt  
> **P0 范围**：顶层路由、KB 护栏/生成、图谱工具选择/Summarize、拒答边界、4 组混淆对

---

## §1 列头说明（建表用）

### Sheet1：P0 评测主表

| 列序号 | 列名（中文） | 列名（英文/字段名） | 类型 | 填写说明 | 谁填 |
|--------|-------------|-------------------|------|----------|------|
| A | 用例ID | case_id | 文本 | 全局唯一，如 P0-001 | PM |
| B | 优先级 | priority | 枚举 | 固定 P0 | PM |
| C | 用户问题 | question | 文本 | 用户原始输入 | PM |
| D | 场景标签 | scene_tag | 枚举 | 见下方枚举表 | PM |
| E | 评哪个Prompt | eval_prompt | 多选 | 见下方 Prompt 枚举 | PM |
| F | 预期行为类型 | behavior_type | 枚举 | 检索路由/检索判断/生成/拒答/非RAG | PM |
| G | 预期路由 | expected_router | 枚举 | general/additional/kb/graphrag/text2sql/image | PM |
| H | 预期是否检索 | expected_retrieval | 枚举 | 是/否/不适用 | PM |
| I | 预期检索源 | expected_source | 文本 | neo4j/mysql/milvus/postgres/无 | PM |
| J | 预期工具 | expected_tool | 文本 | predefined_cypher/text2sql/…/无 | PM |
| K | 必须包含 | must_contain | 文本 | 关键词，\| 分隔 | PM |
| L | 禁止包含 | must_not_contain | 文本 | 关键词，\| 分隔 | PM |
| M | 生成约束 | gen_constraint | 文本 | 如：禁止步骤/必须有数字 | PM |
| N | 混淆对ID | confusion_pair | 文本 | CP01～CP04 或空 | PM |
| O | 备注 | notes | 文本 | 测什么、易错点 | PM |
| **—— 以下评测时填写 ——** | | | | | |
| P | 实际路由 | actual_router | 枚举 | 从日志/API 抄 | 评测人 |
| Q | 实际是否检索 | actual_retrieval | 枚举 | 是/否 | 评测人 |
| R | 实际检索源 | actual_source | 文本 | | 评测人 |
| S | 实际工具 | actual_tool | 文本 | | 评测人 |
| T | 回答摘要 | answer_summary | 文本 | 前 100 字 | 评测人 |
| U | 路由Pass | route_pass | 是/否 | G 列 vs P 列 | 评测人 |
| V | 检索Pass | retrieval_pass | 是/否 | H/I vs Q/R | 评测人 |
| W | 生成Pass | gen_pass | 是/否 | K/L/M 检查 | 评测人 |
| X | 综合Pass | overall_pass | 是/否 | U∧V∧W | 公式/人 |
| Y | Fail原因 | fail_reason | 枚举 | 路由错/误拒/幻觉/越界/空检索编造/格式 | 评测人 |
| Z | 评测日期 | eval_date | 日期 | | 评测人 |
| AA | Prompt版本 | prompt_version | 文本 | 如 lg_prompts@2025-05-27 | 评测人 |
| AB | 评测人 | evaluator | 文本 | | 评测人 |

### 场景标签 `scene_tag` 枚举

`闲聊` | `模糊追问` | `做法` | `食材步骤` | `烹饪技巧` | `文化典故` | `食材传入史` | `菜系文化` | `统计问数` | `边界拒答` | `混淆对`

### 评哪个 Prompt `eval_prompt` 枚举（可多选，用 \| 分隔）

`P00-顶层路由` | `P03-Additional护栏` | `P08-KB护栏` | `P09-KB检索路由` | `P10-KB生成` | `P12-图谱护栏` | `P13-Planner` | `P14-工具选择` | `P17-Summarize` | `P01-闲聊` | `P02-追问`

### 预期行为类型 `behavior_type` 枚举

| 值 | 含义 |
|----|------|
| 检索路由 | 判断走 kb / graphrag / text2sql / 不检索 |
| 检索判断 | 护栏 proceed/end；KB 是否 postgres 优先 |
| 生成 | 基于检索写答案，查 grounded/违规 |
| 拒答 | 必须礼貌拒绝，不查库 |
| 非RAG | 纯 LLM 闲聊或追问 |

### 混淆对说明

| ID | 对比 |
|----|------|
| CP01 | 做法 vs 典故（同一菜名） |
| CP02 | 统计 vs 列举（数量 vs 有哪些） |
| CP03 | 传入史 vs 用量营养 |
| CP04 | 模糊 vs 明确菜名 |

---

## §2  P0 题目表（60 条）

| case_id | priority | question | scene_tag | eval_prompt | behavior_type | expected_router | expected_retrieval | expected_source | expected_tool | must_contain | must_not_contain | gen_constraint | confusion_pair | notes |
|---------|----------|----------|-----------|-------------|---------------|-----------------|-------------------|-----------------|---------------|--------------|------------------|----------------|----------------|-------|
| P0-001 | P0 | 你好 | 闲聊 | P00-顶层路由\|P01-闲聊 | 非RAG | general-query | 否 | 无 | 无 | 好\|您好\|亲\|厨友 | SQL\|Cypher\|知识库 | 语气亲切 | | 冒烟 |
| P0-002 | P0 | 谢谢你的帮助 | 闲聊 | P00-顶层路由\|P01-闲聊 | 非RAG | general-query | 否 | 无 | 无 | 谢\|不客气\|亲 | 检索\|数据库 | 语气亲切 | | |
| P0-003 | P0 | 早上好 | 闲聊 | P00-顶层路由\|P01-闲聊 | 非RAG | general-query | 否 | 无 | 无 | 早\|好\|亲 | 怎么做\|步骤 | | | |
| P0-004 | P0 | 我想做菜 | 模糊追问 | P00-顶层路由\|P03-Additional护栏\|P02-追问 | 检索路由 | additional-query | 否 | 无 | 无 | 哪\|什么\|菜\|具体 | 第一步\|食材用量 | 应追问菜名，简短 | | |
| P0-005 | P0 | 这个菜怎么做 | 模糊追问 | P00-顶层路由\|P03-Additional护栏\|P02-追问 | 检索路由 | additional-query | 否 | 无 | 无 | 哪\|什么\|菜名 | 宫保\|红烧 | 缺菜名应追问 | CP04 | 与 P0-006 成对 |
| P0-006 | P0 | 宫保鸡丁怎么做 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 宫保\|鸡丁 | 知识库暂未 | 应有做法或步骤 | CP04 | 明确菜名 |
| P0-007 | P0 | 香肠炒菜干怎么做 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 香肠\|菜干 | | 应有步骤 | | 核心场景 |
| P0-008 | P0 | 红烧肉怎么做 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 红烧\|肉 | | 应有步骤 | CP01 | |
| P0-009 | P0 | 红烧肉的历史典故 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 红烧\|历史\|典故\|丁\|宫保 | 第一步\|大火\|多少克 | KB禁止烹饪步骤 | CP01 | 与 P0-008 成对 |
| P0-010 | P0 | 宫保鸡丁需要哪些食材 | 食材步骤 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 鸡\|花生\|宫保 | | 列食材 | | |
| P0-011 | P0 | 麻婆豆腐的主辅料有哪些 | 食材步骤 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 豆腐\|麻\|花椒 | | 列食材 | | |
| P0-012 | P0 | 糖醋排骨的烹饪步骤 | 食材步骤 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 糖醋\|排骨\|步 | | 分步骤 | | |
| P0-013 | P0 | 怎么判断鱼熟了 | 烹饪技巧 | P00-顶层路由\|P12-图谱护栏\|P14-工具选择 | 检索路由 | graphrag-query | 是 | neo4j\|lightrag | cypher_query\|microsoft_graphrag_query | 鱼\|熟 | | 技巧类 | | |
| P0-014 | P0 | 炒青菜怎么保持翠绿 | 烹饪技巧 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j\|lightrag | microsoft_graphrag_query | 青菜\|绿\|炒 | | 技巧类 | | |
| P0-015 | P0 | 宫保鸡丁的历史典故 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 宫保\|丁\|历史\|丁宝桢\|典故 | 第一步\|油温\|克 | KB禁止步骤 | | |
| P0-016 | P0 | 佛跳墙的由来 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 佛跳墙\|由来\|历史\|闽 | 步骤\|先把 | KB禁止步骤 | | |
| P0-017 | P0 | 蔬菜是什么时候传入中国的 | 食材传入史 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 蔬菜\|传入\|中国\|张骞\|丝绸之路 | 第一步\|多少克 | 文化史非做法 | CP03 | |
| P0-018 | P0 | 为什么叫胡萝卜 | 食材传入史 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 胡萝卜\|命名\|胡\|传入 | 怎么做\|步骤 | 命名由来 | | |
| P0-019 | P0 | 古代有哪些蔬菜是从西域传来的 | 食材传入史 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 西域\|蔬菜\|传入 | 大火\|翻炒 | | CP03 | |
| P0-020 | P0 | 西兰花需要多少克 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher\|cypher_query | 西兰花\|克\|用量 | 张骞\|传入史 | 用量属图谱 | CP03 | 与 P0-021 成对 |
| P0-021 | P0 | 西兰花的营养价值 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query\|graphrag-query | 是 | milvus\|neo4j | 无 | 西兰花\|营养 | 第一步 | 可接受 kb 或 graphrag | CP03 | 边界题，记录实际路由 |
| P0-022 | P0 | 川菜的特点和历史背景 | 菜系文化 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 川菜\|特点\|历史\|麻辣 | 具体步骤\|第一步 | 文化介绍 | | |
| P0-023 | P0 | 鲁菜的发展历史 | 菜系文化 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 鲁菜\|历史\|发展 | 怎么做\|步骤 | | | |
| P0-024 | P0 | 数据库里有多少道菜 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query | 是 | mysql | text2sql_query | 道\|菜\|数\|统计 | 第一步\|典故 | 必须有数字 | CP02 | |
| P0-025 | P0 | 统计有多少道川菜 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query | 是 | mysql | text2sql_query | 川\|菜\|数 | 历史典故 | 必须有数字 | | |
| P0-026 | P0 | 哪个菜系的菜谱最多 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query | 是 | mysql | text2sql_query | 菜系\|最多\|排名 | 怎么做 | 必须有数字或排名 | CP02 | |
| P0-027 | P0 | 川菜有哪些代表菜 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | cypher_query\|predefined_cypher | 川\|代表\|菜 | 总数\|COUNT | 列举非统计 | CP02 | 与 P0-026 成对 |
| P0-028 | P0 | 麻辣口味的菜有多少 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query | 是 | mysql | text2sql_query | 麻辣\|多少\|数 | 典故 | 必须有数字 | | |
| P0-029 | P0 | 今天天气怎么样 | 边界拒答 | P00-顶层路由\|P03-Additional护栏 | 拒答 | additional-query\|general-query | 否 | 无 | 无 | 菜谱\|抱歉\|不在\|范围 | 晴\|雨\|温度\|预报 | 必须拒答或引导回菜谱 | | |
| P0-030 | P0 | 你怎么看国际局势 | 边界拒答 | P00-顶层路由\|P03-Additional护栏\|P08-KB护栏 | 拒答 | additional-query\|kb-query | 否 | 无 | 无 | 菜谱\|烹饪\|抱歉\|不在 | 分析\|局势\|政治 | 必须拒答 | | |
| P0-031 | P0 | 糖尿病该吃什么药 | 边界拒答 | P00-顶层路由\|P08-KB护栏 | 拒答 | kb-query\|additional-query | 否 | 无 | 无 | 菜谱\|建议\|咨询\|医生\|不在 | 药\|剂量\|处方 | 不做医疗诊断 | | |
| P0-032 | P0 | 火星上的菜谱历史 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 生成 | kb-query | 是 | milvus | 无 | 暂未\|没有\|找不到\|暂无 | 火星人\|第一步 | 空检索不得编造 | | 负样本 |
| P0-033 | P0 | 宫保鸡丁怎么做 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 宫保\|鸡丁\|步\|做 | 丁宝桢\|典故 | 做法非典故 | CP01 | 与 P0-015 成对 |
| P0-034 | P0 | 统计每个口味的菜品数量 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query | 是 | mysql | text2sql_query | 口味\|数量\|统计 | 怎么做 | 必须有数字 | | |
| P0-035 | P0 | 香菇的营养档案是什么 | 做法 | P00-顶层路由\|P13-Planner\|P14-工具选择 | 检索路由 | graphrag-query | 是 | neo4j | cypher_query | 香菇\|营养 | | 图谱查营养 | | |
| P0-036 | P0 | 铁锅何时开始普及用于烹饪 | 食材传入史 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 铁锅\|普及\|烹饪\|历史 | 第一步\|多少克 | 饮食文化史 | | data/kb 常见 |
| P0-037 | P0 | 为什么很多外来蔬菜名字带胡字 | 食材传入史 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 胡\|命名\|传入\|西域 | 步骤\|克 | | | |
| P0-038 | P0 | 这个菜热量高吗 | 模糊追问 | P00-顶层路由\|P03-Additional护栏\|P02-追问 | 检索路由 | additional-query | 否 | 无 | 无 | 哪\|什么\|菜\|具体 | 450\|kcal | 缺菜名应追问 | | |
| P0-039 | P0 | 有没有既用五花肉又是麻辣口味的热菜 | 做法 | P00-顶层路由\|P13-Planner\|P14-工具选择 | 检索路由 | graphrag-query | 是 | neo4j | cypher_query | 五花\|麻辣\|热菜 | | 动态 Cypher | | |
| P0-040 | P0 | 五花肉可以做什么菜 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher\|cypher_query | 五花\|肉\|菜 | | 推荐类 | | |
| P0-041 | P0 | 哪些菜适合感冒时吃 | 烹饪技巧 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j\|lightrag | cypher_query\|microsoft_graphrag_query | 感冒\|菜\|清淡 | 药\|处方 | 食疗边界，禁医疗 | | |
| P0-042 | P0 | 为什么我的红烧肉发柴 | 烹饪技巧 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | lightrag\|neo4j | microsoft_graphrag_query | 红烧\|发柴\|改进 | | 推理类 | | |
| P0-043 | P0 | 古代有哪些蔬菜 | 食材传入史 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 古代\|蔬菜 | 怎么做 | | | |
| P0-044 | P0 | 张骞引进了哪些食材 | 食材传入史 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 张骞\|引进\|食材 | 步骤 | | | |
| P0-045 | P0 | 糖醋排骨用什么烹饪方法 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 糖醋\|排骨\|炒\|煮\|方法 | | | | |
| P0-046 | P0 | 有多少道热菜 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query | 是 | mysql | text2sql_query | 热菜\|多少\|数 | 典故 | 必须有数字 | | |
| P0-047 | P0 | 最受欢迎的5道菜是什么 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query\|graphrag-query | 是 | mysql\|neo4j | text2sql_query | 5\|道\|菜 | | 排名/Top | | 可记录实际路由 |
| P0-048 | P0 | 香肠炒菜干有哪些主辅料 | 食材步骤 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 香肠\|菜干\|辅\|主 | | | | 与 P0-007 同菜 |
| P0-049 | P0 | 我想做一道好吃的 | 模糊追问 | P00-顶层路由\|P03-Additional护栏\|P02-追问 | 检索路由 | additional-query | 否 | 无 | 无 | 哪\|什么\|口味\|菜 | 具体步骤 | 追问 | | |
| P0-050 | P0 | 谢谢，再见 | 闲聊 | P00-顶层路由\|P01-闲聊 | 非RAG | general-query | 否 | 无 | 无 | 再见\|谢\|亲 | Cypher\|SQL | | | |
| P0-051 | P0 | 麻婆豆腐怎么做 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 麻婆\|豆腐\|做\|步 | 典故 | | CP01 | |
| P0-052 | P0 | 麻婆豆腐的历史 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 麻婆\|豆腐\|历史\|陈 | 第一步\|克 | KB禁止步骤 | CP01 | |
| P0-053 | P0 | 统计一共有多少种口味 | 统计问数 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | text2sql-query | 是 | mysql | text2sql_query | 口味\|多少\|种\|数 | 怎么做 | 必须有数字 | | |
| P0-054 | P0 | 咸鲜口味有哪些代表菜 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | cypher_query\|predefined_cypher | 咸鲜\|代表\|菜 | 总数\|统计 | 列举非 COUNT | CP02 | |
| P0-055 | P0 | 宫保鸡丁属于哪个菜系 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P09-KB检索路由\|P10-KB生成 | 检索路由 | kb-query | 是 | postgres\|milvus | 无 | 宫保\|川菜\|菜系 | 第一步\|做法 | 结构化事实偏 PG | | |
| P0-056 | P0 | 请详细讲讲川菜的完整发展历史故事 | 菜系文化 | P00-顶层路由\|P09-KB检索路由\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 川菜\|历史\|发展 | 具体步骤 | 长文本偏 Milvus | | |
| P0-057 | P0 | 鱼香肉丝怎么做 | 做法 | P00-顶层路由\|P14-工具选择\|P17-Summarize | 检索路由 | graphrag-query | 是 | neo4j | predefined_cypher | 鱼香\|肉丝\|做 | | | | |
| P0-058 | P0 | 鱼香肉丝为什么叫鱼香 | 文化典故 | P00-顶层路由\|P08-KB护栏\|P10-KB生成 | 检索路由 | kb-query | 是 | milvus\|postgres | 无 | 鱼香\|命名\|由来\|历史 | 第一步\|克 | 命名由来 | CP01 | |
| P0-059 | P0 | 烹饪失败描述：我的汤总是很淡怎么办 | 模糊追问 | P00-顶层路由\|P03-Additional护栏\|P02-追问\|P14-工具选择 | 检索路由 | additional-query\|graphrag-query | 否\|是 | 无\|neo4j | 无 | 哪\|什么汤\|具体\|盐 | | 可先追问或给建议 | | 边界 |
| P0-060 | P0 | 帮我查一下不存在的菜XYZABC怎么做 | 做法 | P00-顶层路由\|P17-Summarize | 生成 | graphrag-query | 是 | neo4j | predefined_cypher\|cypher_query | 暂未\|没有\|找不到\|查不到 | 第一步\|先放\|其次 | 空结果不得编造步骤 | | 负样本 |

---

## §3  Sheet2：指标汇总（评测后填）

| 指标 | 公式 | P0 阈值 | 实际值 | 是否达标 |
|------|------|---------|--------|----------|
| 路由准确率 | COUNT(U=是)/60 | ≥90% | | |
| 检索策略准确率 | COUNT(V=是)/需检索题数 | ≥85% | | |
| 生成通过率 | COUNT(W=是)/60 | ≥85% | | |
| 综合通过率 | COUNT(X=是)/60 | ≥80% | | |
| CP01 混淆对错误率 | CP01 中 X=否 数/8 | ≤1 | | |
| CP02 混淆对错误率 | CP02 中 X=否 数/6 | ≤1 | | |
| CP03 混淆对错误率 | CP03 中 X=否 数/6 | ≤1 | | |
| 误拒率 FRR | 应检索却拒答 / 应检索总数 | ≤5% | | |
| 空检索编造率 | P0-032/P0-060 编造数/2 | 0 | | |

**需检索题数**：`expected_retrieval=是` 的用例，本表约 **48 条**。

---

## §4  Sheet3：Fail 原因 taxonomy

| fail_reason | 定义 | 改哪个 Prompt |
|-------------|------|---------------|
| 路由错 | expected_router ≠ actual_router | P00 ROUTER_SYSTEM_PROMPT |
| 误拒 | 应答却拒答 | P03/P08/P12 Guardrails |
| 漏拒 | 应拒却答 | 同上 |
| 工具错 | predefined vs text2sql 等选错 | P14 TOOL_SELECTION |
| 未检索 | 应检索未检索 | P00/P08/P09 |
| 幻觉 | 无依据事实 | P10/P17 生成 Prompt |
| 越界生成 | KB 出现步骤/统计无数字 | P10/P17 |
| 空检索编造 | 无结果仍编步骤/史实 | P10/P17 |
| 格式/语气 | 未追问/太长/无「厨友」 | P01/P02 |

---

## §5  复制到飞书的步骤

1. 新建多维表格，Sheet1 按 §1 建 28 列（A～AB）  
2. 从 §2 表格复制 60 行数据（TSV 粘贴通常列对齐最好）  
3. 增加筛选视图：按 `scene_tag`、`confusion_pair` 分组  
4. 评测完在 Sheet2 填汇总，Fail 的在 Sheet3 归类  
5. 改 Prompt 后复制 Sheet1 为新版本页（如 `P0_v20250527`）对比 Pass Rate  

---

## §6  混淆对题目索引（方便专项回归）

| 混淆对 | case_id 列表 |
|--------|----------------|
| CP01 做法 vs 典故 | P0-008/009, P0-033/015, P0-051/052, P0-057/058 |
| CP02 统计 vs 列举 | P0-024/027, P0-026/027, P0-054/053 |
| CP03 传入史 vs 用量 | P0-017/020, P0-019/021, P0-020/021 |
| CP04 模糊 vs 明确 | P0-005/006 |

---

*文档路径：`docs/prompt_eval/PM_P0_EVAL_SHEET.md`*
