# GustoBot Prompt 评测框架

本文档定义 GustoBot Multi-Agent 系统的 **Prompt 分层评测体系**，包含用例 Schema、指标、Rubrics、Judge Prompt 与执行流程。

---

## 1. 评测目标

| 层级 | 评测对象 | 核心问题 |
|------|----------|----------|
| **L0 路由** | `ROUTER_SYSTEM_PROMPT` | 用户问题是否分到正确的 7 类之一？ |
| **L1 护栏** | KB/图谱/Additional Guardrails | 该不该答？该不该检索？ |
| **L2 子路由** | KB Router、Tool Selection | 用哪个库/哪个工具？ |
| **L3 查询生成** | Planner、Text2Cypher、Text2SQL | 子任务/SQL/Cypher 是否正确可执行？ |
| **L4 检索** | Milvus/Postgres/Neo4j/LightRAG | Recall、来源、非空率 |
| **L5 生成** | Final/Summarize/KB finalize | 忠实度、格式、边界、语气 |
| **E2E 端到端** | 全链路 | 用户视角答案是否满意 |

---

## 2. Prompt 资产清单（评测注册表）

复制下表到 LangSmith / Excel / 自建平台，每条用例引用 `prompt_ids`。

| prompt_id | 常量/位置 | 节点 | 输入变量 | 输出结构 | 主流程是否启用 |
|-----------|-----------|------|----------|----------|----------------|
| P00 | `ROUTER_SYSTEM_PROMPT` | `analyze_and_route_query` | messages | `Router.type` | ✅ |
| P01 | `GENERAL_QUERY_SYSTEM_PROMPT` | `respond_to_general_query` | logic, messages | 自由文本 | ✅ |
| P02 | `GET_ADDITIONAL_SYSTEM_PROMPT` | `get_additional_info` | logic, messages | 自由文本 | ✅ |
| P03 | `GUARDRAILS_SYSTEM_PROMPT` (lg) | `get_additional_info` | question + scope + schema | proceed/end | ✅ |
| P04 | `GET_IMAGE_SYSTEM_PROMPT` | `create_image_query` | image_description, messages | 自由文本 | ✅ |
| P05 | `IMAGE_GENERATION_ENHANCE_PROMPT` | `_generate_image` | user_query | 优化 prompt 文本 | ✅ |
| P06 | `IMAGE_GENERATION_SUCCESS_PROMPT` | `_generate_image` | dish_name | 模板文本 | ✅ |
| P07 | Vision inline system | `create_image_query` | image base64 | 图片描述 | ✅ |
| P08 | KB guardrails (inline) | KB 子图 guardrails | question | proceed/end | ✅ |
| P09 | KB router (inline) | KB 子图 kb_router | question, history | route + tools | ✅ |
| P10 | KB final_prompt (inline) | KB 子图 finalize | question + contexts | 自由文本 | ✅ |
| P11 | `build_knowledge_system_prompt` | `knowledge_query` | context | 自由文本 | ✅ 降级/文件 |
| P12 | `GUARDRAILS_SYSTEM_PROMPT` (kg) | 图谱 guardrails | question + scope + schema | planner/end | ✅ |
| P13 | `PLANNER_SYSTEM_PROMPT` | planner | question | tasks[] | ✅ |
| P14 | `TOOL_SELECTION_SYSTEM_PROMPT` | tool_selection | question | tool call | ✅ |
| P15 | text2cypher generation | cypher_query | schema, fewshot, question | Cypher 字符串 | ✅ |
| P16 | `TEXT2CYPHER_VALIDATION_PROMPT` | cypher validation | cypher, question | 校验结论 | ✅ 可选 |
| P17 | summarize prompts | summarize | results, question | 自由文本 | ✅ |
| P18 | query_analysis prompt | text2sql | schema, question | JSON | ✅ |
| P19 | sql_generation prompt | text2sql | schema, analysis | SQL | ✅ |
| P20 | `RAGSEARCH_SYSTEM_PROMPT` | — | context | — | ❌ 未接入 |
| P21 | `GENERATE_QUERIES_SYSTEM_PROMPT` | — | — | — | ❌ 未接入 |
| P22 | `CHECK_HALLUCINATIONS` | `check_hallucinations` | documents, generation | 0/1 | ❌ 未挂主图 |

---

## 3. 用例 JSON Schema

见 [`tests/prompt_eval/schema/case_schema.json`](../../tests/prompt_eval/schema/case_schema.json)。

### 3.1 最小必填字段

```json
{
  "case_id": "ROUTER-001",
  "layer": "L0_router",
  "input": { "message": "你好" },
  "expected": { "router_type": "general-query" },
  "prompt_chain": ["P00"],
  "tags": ["greeting", "smoke"]
}
```

### 3.2 完整字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `case_id` | string | 全局唯一，建议 `{LAYER}-{序号}` |
| `layer` | enum | 见 §4 |
| `priority` | P0/P1/P2 | P0=回归必跑，P1=每周，P2=扩展 |
| `input.message` | string | 用户问题 |
| `input.history` | array | 多轮 `[{role, content}]` |
| `input.image_path` | string? | 覆盖路由 |
| `input.file_path` | string? | 覆盖路由 |
| `input.session_id` | string? | 固定会话 ID |
| `expected.router_type` | string? | 7 类路由 |
| `expected.node` | string? | LangGraph 节点名 |
| `expected.guardrails_decision` | proceed/end/planner | 护栏输出 |
| `expected.kb_route` | local/external/hybrid | KB 子路由 |
| `expected.kb_tools` | string[] | postgres/milvus |
| `expected.tools` | string[] | cypher_query/predefined_cypher/... |
| `expected.sub_tasks` | string[] | Planner 期望子任务（语义级） |
| `expected.retrieval` | object | 见 §5 |
| `expected.generation` | object | 见 §6 |
| `expected.must_not_contain` | string[] | 答案禁止出现的内容 |
| `expected.must_contain` | string[] | 答案必须包含（关键词/实体） |
| `prompt_chain` | string[] | 期望触发的 prompt_id 序列 |
| `data_dependencies` | string[] | neo4j/mysql/milvus/postgres/lightrag |
| `negative_case` | bool | true=期望拒绝/降级 |
| `notes` | string | 人工备注 |

---

## 4. 分层用例类型 (`layer`)

| layer 值 | 测什么 | 隔离方式 |
|----------|--------|----------|
| `L0_router` | 仅顶层路由 | Mock LLM 或只跑到 `analyze_and_route_query` |
| `L1_guardrails_additional` | additional 护栏 | 固定 router=additional-query |
| `L1_guardrails_kb` | KB 护栏 | 直接 invoke KB 子图 guardrails |
| `L1_guardrails_kg` | 图谱护栏 | 直接 invoke 图谱 guardrails |
| `L2_kb_router` | KB 工具路由 | guardrails=proceed 后测 router |
| `L2_tool_selection` | 图谱工具选择 | 固定 question + mock planner tasks |
| `L3_planner` | 任务分解 | 只测 planner 输出 |
| `L3_text2cypher` | Cypher 生成 | 给定子任务 + schema |
| `L3_text2sql` | SQL 分析+生成 | 给定 question + schema |
| `L4_retrieval` | 检索质量 | 不评 Prompt，评 Recall@k |
| `L5_generation_kb` | KB finalize | 固定 retrieval context |
| `L5_generation_summarize` | 图谱 summarize | 固定 tool results |
| `L5_generation_general` | 闲聊/追问/图片 | 固定 router |
| `E2E` | 全链路 | `graph.ainvoke` |

---

## 5. 检索层期望 (`expected.retrieval`)

```json
{
  "retrieval": {
    "required_sources": ["milvus"],
    "optional_sources": ["postgres"],
    "min_hits": 1,
    "max_hits": 10,
    "entity_must_appear_in_context": ["宫保鸡丁"],
    "similarity_min": 0.15,
    "rerank_min": 0.35,
    "postgres_before_milvus": true,
    "skip_milvus_if_postgres_hit": true,
    "cypher_must_contain": ["Dish", "MATCH"],
    "sql_must_contain": ["SELECT", "COUNT"],
    "neo4j_record_min": 1
  }
}
```

---

## 6. 生成层 Rubric (`expected.generation`)

```json
{
  "generation": {
    "style": "下厨房风格",
    "language": "zh-CN",
    "max_length_chars": 500,
    "must_cite_sources": false,
    "grounded_only": true,
    "forbid_cooking_steps": true,
    "forbid_medical_claims": true,
    "tone": ["亲切", "厨友"],
    "format": ["分段或条目"],
    "empty_retrieval_behavior": "明确说明暂无记载"
  }
}
```

### 6.1 按路由的生成约束（评测 checklist）

| 路由 | grounded_only | 特殊约束 |
|------|---------------|----------|
| general-query | false | 允许无检索；拒绝非菜谱要礼貌 |
| additional-query | false | 必须追问，一次一问，≤20字（prompt 要求） |
| kb-query | true | **禁止**具体步骤/用量/医疗 |
| graphrag-query | true | 应有步骤/食材；可 numbered list |
| text2sql-query | true | 必须含数字/统计结论 |
| image-query | 视模式 | 识图需引用 image_description |

---

## 7. 指标定义

### 7.1 分类/路由指标

- **Route Accuracy** = 正确路由数 / 总数
- **Route Confusion Matrix**（7×7）
- **Heuristic Override Rate** = 启发式覆盖 LLM 的比例

### 7.2 护栏指标

- **False Reject Rate (FRR)**：应 proceed 却 end
- **False Accept Rate (FAR)**：应 end 却 proceed

### 7.3 工具选择指标

- **Tool Selection F1**（macro）
- **Exact Tool Set Match**：多工具并行时集合完全一致

### 7.4 检索指标

- **Recall@k**：gold 文档/实体是否出现在 top-k
- **Context Non-empty Rate**
- **Postgres-first Compliance**：PG 有结果时是否跳过 Milvus

### 7.5 生成指标

- **Groundedness**（LLM Judge 0-1 或人工）
- **Hallucination Rate**（含未支持事实）
- **Constraint Violation Rate**（如 KB 答案出现步骤）
- **Must-contain Hit Rate**
- **Style Compliance**（可选 LLM Judge）

### 7.6 E2E 指标

- **Answer Correctness**（人工 1-5 或 LLM Judge）
- **Latency P50/P95**（按路由分桶）
- **Fallback Rate**（KB 子图失败降级比例）

---

## 8. 执行流程

### 8.1 离线 Prompt 单元测（推荐先做）

1. 从注册表加载 Prompt 模板
2. 注入 `input` + 固定 `history`
3. 调用被测 LLM（`temperature=0` 或 `0.3`）
4. 解析 structured output 或正则
5. 对比 `expected.*`

### 8.2 集成 E2E

```bash
# 需配置 .env 与 Docker 依赖
set GUSTOBOT_RUN_INTEGRATION_TESTS=1
python -m tests.prompt_eval.run_eval --suite all --layer E2E
python -m tests.prompt_eval.run_eval --case-file tests/prompt_eval/cases/L0_router.jsonl
python -m tests.prompt_eval.run_eval --layer L0_router --report reports/router.json
```

### 8.3 LLM-as-Judge

Judge Prompt 见 [`tests/prompt_eval/judge_prompts.md`](../../tests/prompt_eval/judge_prompts.md)。

原则：**Judge 与 Generator 使用不同模型或不同 temperature**，避免自嗨。

---

## 9. 用例库目录

```
tests/prompt_eval/
├── schema/case_schema.json
├── cases/
│   ├── L0_router.jsonl
│   ├── L1_guardrails.jsonl
│   ├── L2_kb_router.jsonl
│   ├── L2_tool_selection.jsonl
│   ├── L3_planner_text2cypher_sql.jsonl
│   ├── L5_generation.jsonl
│   └── E2E_full_chain.jsonl
├── judge_prompts.md
├── rubrics.yaml
└── run_eval.py
```

---

## 10. 回归集建议规模

| 集合 | 条数 | 用途 |
|------|------|------|
| Smoke | 20 | CI 快速冒烟 |
| Core | 120 | 每周回归 |
| Full | 300+ | 发版前 / Prompt 大改 |

**混淆对（必含）**：

- 做法 vs 典故：`红烧肉怎么做` vs `红烧肉的历史典故`
- 统计 vs 图谱：`有多少道川菜` vs `川菜的特点`
- 食材史 vs 营养：`蔬菜何时传入中国` vs `西兰花营养价值`
- 模糊 vs 拒答：`我想做菜` vs `今天天气怎么样`

---

## 11. 版本与变更记录

每次修改 Prompt 文件，在 PR 中更新：

| 字段 | 示例 |
|------|------|
| prompt_version | `lg_prompts@2025-05-27` |
| model | `qwen3-max` |
| eval_run_id | `eval-20250527-001` |
| core_route_accuracy | `0.94` |
| kb_groundedness | `0.88` |

---

## 12. 相关代码

- 主图：`gustobot/application/agents/lg_builder.py`
- 主 Prompt：`gustobot/application/agents/lg_prompts.py`
- KB/图谱子图：`gustobot/.../multi_agent/multi_tool.py`
- 图谱 Prompt：`gustobot/.../prompts/kg_prompts.py`
- 路由测试：`tests/test_agent_routing.py`
