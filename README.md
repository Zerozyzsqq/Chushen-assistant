# 厨神助手 · 中华菜谱智能问答

<div align="center">
  <h2>基于 Multi-Agent 的中华菜谱 AI 助理</h2>

  ![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat&logo=python)
  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=ffffff)
  ![LangGraph](https://img.shields.io/badge/LangGraph-Flow-green?style=flat&logo=databricks)
  ![GraphRAG](https://img.shields.io/badge/GraphRAG-KG-blueviolet?style=flat)
  ![Agent](https://img.shields.io/badge/Agent-System-orange?style=flat)
  ![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)
  ![Neo4j](https://img.shields.io/badge/Neo4j-4.4-008CC1?style=flat&logo=neo4j)
  ![Milvus](https://img.shields.io/badge/Milvus-2.3-00A9E0?style=flat)
  ![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg?style=flat)
</div>

## 项目简介

中华菜谱作为世界饮食文化的瑰宝之一，拥有深厚的历史底蕴与丰富的知识体系。从八大菜系的地域特色，到食材搭配的营养学原理，再到烹饪技法的代际传承，菜谱知识既具有高度结构化的特点（如食材用量、烹饪步骤），又包含大量非结构化的文化典故与经验性描述。这种复杂性使得传统的关键词搜索难以满足用户对菜谱知识的深度探索需求。

随着大语言模型（LLM）与知识增强技术的快速发展，将菜谱知识构建为一个**多模态、结构化、可交互的 AI 系统**成为可能。本项目以中华菜谱数据为基础，构建出覆盖菜谱名称、食材、烹饪步骤、营养成分、菜系流派、历史典故等元素的**多层次知识图谱**，并结合大模型的理解与生成能力，打造了一个**专注于菜谱领域的智能问答产品**——「**厨神助手**」。

在技术架构层面，我们融合了 **LangGraph 多智能体编排**、**GraphRAG 图谱检索增强**、**Text2SQL 结构化查询**、以及**多源知识融合**技术，使用户不仅可以通过自然语言提问获得精确答案（如"宫保鸡丁怎么做？"、"川菜有多少道菜？"），还能探索菜谱的历史文化背景（如"宫保鸡丁的典故"）、获取营养建议、甚至生成菜品图片。

### 核心价值

本项目致力于打造一个**可迁移、可扩展、面向垂直领域的智能客服模板系统**。通过清晰的三层架构设计（主路由层 → 多工具子图层 → 原子工具层），你可以轻松将其迁移至其他垂直领域（如「宝可梦百科」、「中医药典」、「法律咨询」、「政务服务」等）中打造专域智能客服。仅需更换知识源与图谱结构，即可实现：

- **智能意图理解**：自动识别问题类型，路由到最优处理模块
- **多工具协作**：动态组合 Neo4j 图谱查询、MySQL 统计分析、向量检索、外部搜索等多种工具
- **PostgreSQL 优先兜底策略**：结构化数据优先 → 向量兜底 → 外部搜索，确保答案质量
- **多模态交互**：支持文本问答、图片识别/生成、文件解析等多种交互方式
- **知识来源可追溯**：每个答案都标注来源，支持多源信息融合
- **安全防护机制**：Guardrails 层确保问题在服务范围内，拒绝越界查询

### 核心功能
 
| 功能模块 | 说明 | 技术实现 |
|---------|------|---------|
| **全参微调** | 爬取和收集数据微调大模型 |  [微调厨神模型](https://pan.baidu.com/s/1vTYbUJb2feUQkb4hJdx7pg?pwd=zts4) |
| **智能路由** | 自动识别问题类型，路由到合适的处理模块 | 启发式路由 + LLM 结构化输出 |
| **知识库查询** | 支持历史文化、菜谱典故等知识查询 | Milvus + PostgreSQL pgvector + Reranker |
| **图谱推理** | 基于 Neo4j 的菜谱关系推理 | Cypher 动态生成 + Few-shot 示例检索 |
| **统计分析** | MySQL 数据库的统计和聚合查询 | Text2SQL + LLM 自然语言转换 |
| **社区检索** | Microsoft GraphRAG 社区摘要检索 | LightRAG Global/Local/Hybrid Search |
| **图片处理** | 菜品图片识别与生成 | Vision Model + CogView-4 |
| **文件处理** | 支持 Excel、TXT、Markdown 等文件上传分析 | Ingest Service + Knowledge Service |
| **对话管理** | 完整的对话历史和会话管理 | LangGraph Checkpointer + Redis |
| **虚拟冰箱** | 本地记录常备食材、临期提醒、一键排餐 | 前端 localStorage + 饮食画像 API |
| **饮食画像** | 控糖/减脂/忌口等偏好注入推荐与回答 | `dietary_profile` 上下文 |
| **识图排餐** | 拍照识食材 → 确认 → 图谱推荐菜谱 | Vision + Neo4j 子图 |
| **多媒体增强** | 结构化菜谱卡片、B站/抖音教程、AI 菜品配图 | Vue 解析 + 媒体服务 |



### 技术架构

```mermaid
flowchart TB
    subgraph FE["前端 · Vue 3"]
        Chat["对话 / 菜谱卡片 / 视频教程"]
        Kitchen["我的厨房 · 虚拟冰箱 · 饮食画像"]
    end

    subgraph API["后端 · FastAPI"]
        ChatAPI["/api/v1/chat"]
        VisionAPI["/api/v1/vision · upload · media"]
    end

    subgraph Agent["LangGraph Multi-Agent"]
        L1["L1 主路由<br/>意图识别"]
        L2A["L2 图谱子图<br/>Cypher · GraphRAG · Text2SQL"]
        L2B["L2 知识库子图<br/>RAG · Rerank"]
        L2C["识图排餐 · 饮食护栏"]
    end

    subgraph Store["数据层"]
        Neo4j[("Neo4j 菜谱图谱")]
        MySQL[("MySQL 统计")]
        PG[("PostgreSQL pgvector")]
        Milvus[("Milvus 向量")]
        LightRAG[("LightRAG")]
    end

    Chat --> ChatAPI
    Kitchen --> ChatAPI
    ChatAPI --> L1
    VisionAPI --> L2C
    L1 --> L2A
    L1 --> L2B
    L1 --> L2C
    L2A --> Neo4j
    L2A --> MySQL
    L2A --> LightRAG
    L2B --> PG
    L2B --> Milvus
```

本项目采用 **三层 Multi-Agent 架构**，将复杂的菜谱知识服务拆解为清晰的层次化设计：

#### 架构分层

| 层级 | 名称 | 职责 | 核心技术 |
|-----|------|------|---------|
| **L1** | **主路由层** | 意图识别与任务分发 | 启发式路由 + LLM 结构化输出 |
| **L2** | **多工具子图层** | 任务分解与工具编排 | LangGraph Subgraph + Map-Reduce |
| **L3** | **原子工具层** | 具体工具执行 | Neo4j / MySQL / Milvus / PostgreSQL |

#### 核心执行流程

1. **用户提问** → 主路由层意图识别 (`analyze_and_route_query`)
2. **路由决策** → 分发至不同子图 (`graphrag-query` / `kb-query` / `general-query` 等)
3. **子图执行** → Guardrails 检查 → Planner 分解 → Tool Selection → 并行工具调用
4. **结果融合** → Summarize Node 聚合 → Final Answer 生成最终回答
5. **返回用户** → 带来源标注的完整答案

### 项目特色

#### 1. 三层架构设计 - 清晰的职责分离

- **主路由层 (L1)**: 启发式关键词 + LLM 双重路由保险，快速准确识别用户意图
- **多工具子图层 (L2)**: LangGraph Subgraph 实现任务分解与并行工具编排
- **原子工具层 (L3)**: 可插拔的工具设计，轻松扩展新能力

#### 2. PostgreSQL 优先兜底策略 - 确保答案质量

```
结构化数据 (PostgreSQL pgvector) → 向量检索兜底 (Milvus) → 外部搜索补充 (External API)
```

- **优先查询 PostgreSQL**: 快速返回精准的结构化数据（菜谱名称、菜系、食材等）
- **Milvus 兜底**: PostgreSQL 无结果时，使用语义检索处理长文本和典故
- **外部搜索**: Hybrid 模式下调用外部 API 补充最新知识

#### 3. Map-Reduce 任务分解 - 处理复杂查询

- **Planner Node**: 将复杂问题拆解为多个独立子任务
- **并行执行**: 子任务并行调用不同工具（Cypher / GraphRAG / Text2SQL）
- **Summarize Node**: 聚合所有工具结果，LLM 融合生成答案

#### 4. Reranker 双阈值过滤 - 提升检索精度

```python
# 双重阈值确保结果质量
similarity >= KB_POSTGRES_SIMILARITY_THRESHOLD  # 相似度阈值
rerank_score >= KB_POSTGRES_RERANK_THRESHOLD    # 重排分数阈值
```

- 支持 Cohere / Jina / Voyage / BGE 等多种 Reranker
- 有效过滤低质量检索结果，提升答案准确性

#### 5. 多源知识融合 - 全面的信息整合

- **图谱推理** (Neo4j): 菜谱关系、食材搭配、菜系归属
- **统计分析** (MySQL): 数量统计、排行榜、聚合查询
- **语义检索** (Milvus + PostgreSQL): 历史典故、文化背景
- **社区摘要** (Microsoft GraphRAG): 全局/局部/混合检索
- **外部知识** (Search API): 实时互联网信息补充

#### 6. 可迁移的垂直领域模板 - 高度泛化

仅需替换知识源与图谱 Schema，即可快速迁移至其他领域：

| 应用领域 | 知识源示例 | 图谱节点示例 |
|---------|-----------|------------|
| **菜谱客服** | 菜谱数据、食材库 | 菜品、食材、菜系、烹饪方法 |
| **宝可梦百科** | 宝可梦图鉴 | 宝可梦、技能、属性、进化链 |
| **中医药典** | 本草纲目、方剂 | 中药、病症、方剂、炮制方法 |
| **法律咨询** | 法律条文、案例 | 法条、案件、当事人、判决 |
| **政务服务** | 政策文件、办事指南 | 政策、部门、流程、材料 |

#### 7. 多模态交互 - 丰富的用户体验

- **图片识别**: Vision Model 识别菜品，返回菜谱信息
- **图片生成**: CogView-4 根据描述生成菜品图片
- **文件处理**: 支持 Excel、TXT、Markdown、JSON 文件上传与分析
- **对话管理**: LangGraph Checkpointer + Redis 维护完整会话历史

#### 8. Guardrails 安全防护 - 拒绝越界查询

- **范围检查**: 每个查询都经过 Guardrails 节点检查是否在服务范围内
- **Schema 验证**: 验证 Neo4j 图谱 Schema，确保查询可执行
- **拒绝策略**: 明确拒绝超出菜谱领域的问题，引导用户提供有效输入

---

##  快速开始

### 环境要求

- Python 3.10
- Node.js 16+
- Docker & Docker Compose 


```bash
# 克隆项目（将仓库地址换成你的 GitHub 仓库）
git clone https://github.com/<your-username>/chushen-assistant.git
cd chushen-assistant

# 配置环境变量
cp .env.example .env # 编辑 .env 文件，配置必要的 API 密钥


# 启动后端服务（Docker）
docker-compose up -d

# 安装并启动前端（本地）
cd web
npm install
npm run dev

# 访问应用
# 前端: http://localhost:5173 （可通过 VITE_PORT 修改端口）
# 后端API: http://localhost:8000
```
 
---

## 上传到 GitHub

项目根目录尚未初始化 Git，可按以下步骤首次上传（**不要提交 `.env` 和 API 密钥**，已在 `.gitignore` 中忽略）。

### 1. 在 GitHub 创建空仓库

1. 打开 [github.com/new](https://github.com/new)
2. 仓库名建议：`chushen-assistant`
3. 选 **Public** 或 **Private**
4. **不要**勾选 “Add a README”（本地已有）
5. 创建后复制仓库地址，例如：`https://github.com/你的用户名/chushen-assistant.git`

### 2. 本地初始化并推送

在项目根目录打开终端（文件夹可重命名为 `chushen-assistant`）：

```powershell
cd d:\multi-agent\GustoBot-develop

git init
git add .
git status
git commit -m "Initial commit: 厨神助手 Multi-Agent 菜谱问答"
git branch -M main
git remote add origin https://github.com/<你的用户名>/chushen-assistant.git
git push -u origin main
```

首次 `git push` 会提示登录 GitHub（浏览器或 Personal Access Token）。

### 3. 推送前自查

| 检查项 | 说明 |
|--------|------|
| `.env` | 必须在 `.gitignore` 中，**切勿提交** |
| `node_modules/`、`.venv/` | 已忽略，不要手动 add |
| `data/recipe.json` | 约 22MB，GitHub 单文件上限 100MB，可提交 |
| 大体积缓存 | `data/lightrag/` 若很大，可考虑加入 `.gitignore` 后再 push |

### 4. 后续更新

```powershell
git add .
git commit -m "描述本次改动"
git push
```

---

## Agent 工作流详解

#### 核心流程说明

##### 第一层：主路由层 (lg_builder.py)

1. **analyze_and_route_query** - 意图识别路由节点
   - 使用 `ROUTER_SYSTEM_PROMPT` 引导 LLM 分类
   - 启发式路由 (`_heuristic_router`) + LLM 路由双保险
   - 输出 `Router` Pydantic 结构化模型
   - 支持 7 种查询类型

2. **route_query** - 条件路由决策
   - 根据 `router.type` 分发到不同处理节点
   - 检查 `config.image_path` / `config.file_path` 优先级

##### 第二层A：GraphRAG 多工具子图 (multi_tool.py - create_multi_tool_workflow)

**工作流**: `guardrails → planner → tool_selection → [工具并行执行] → summarize → final_answer`

1. **Guardrails Node** - 安全防护
   - 检查问题是否在菜谱服务范围内
   - 验证 Neo4j 图谱 Schema
   - 决策: `proceed` / `end`

2. **Planner Node** - 任务分解
   - Map-Reduce 模式
   - 将复杂问题拆解为多个子任务
   - 每个子任务独立处理

3. **Tool Selection Node** - 工具选择
   - 根据 `tool_schemas` 让 LLM 选择最优工具
   - 支持 4 个并行工具

4. **工具节点** (并行执行):
   - **Cypher Query**: 动态生成 Cypher → Neo4j 图谱查询
   - **Predefined Cypher**: 使用预定义查询模板
   - **Microsoft GraphRAG**: LightRAG 社区检索
   - **Text2SQL Query**: 自然语言转 SQL → MySQL 统计查询

5. **Summarize Node** - 结果聚合
   - 合并所有工具的返回数据
   - LLM 初步整理

6. **Final Answer Node** - 生成最终回答
   - 使用 `RAGSEARCH_SYSTEM_PROMPT`
   - 引用来源标注
   - 可选幻觉检查

##### 第二层B：知识库多工具子图 (multi_tool.py - create_kb_multi_tool_workflow)

**工作流**: `guardrails → kb_router → local_search → [reranker] → finalize`

1. **KB Guardrails Node** - 范围检查
   - 仅处理历史文化典故类问题
   - 拒绝烹饪步骤、食材搭配等

2. **KB Router Node** - 路由决策
   - LLM 决定路由类型: `local` / `external` / `hybrid`
   - 选择检索工具: `postgres` / `milvus`

3. **Local Search Node** - 本地检索 (核心)
   - **PostgreSQL 优先策略**:
     1. 先查询 PostgreSQL pgvector (结构化数据)
     2. 如果 PG 有结果 → 直接使用，跳过 Milvus
     3. 如果 PG 无结果 → Milvus 兜底 (长文本)
   - 相似度阈值过滤

4. **Reranker Process** - 重排序 (可选)
   - 使用 Reranker API (Cohere/Jina/Voyage/BGE)
   - 双重阈值过滤:
     - `similarity >= KB_POSTGRES_SIMILARITY_THRESHOLD`
     - `rerank_score >= KB_POSTGRES_RERANK_THRESHOLD`

5. **External Search Node** - 外部检索
   - 调用外部检索 API
   - 仅在本地无结果或 hybrid 模式时触发

6. **Finalize Node** - 融合生成
   - LLM 融合 Milvus + PostgreSQL + External 结果
   - 格式化 context，收集 sources
   - 生成最终回答

##### 第三层：原子工具层

- **数据库**: Neo4j (图谱)、MySQL (统计)、PostgreSQL pgvector (结构化向量)、Milvus (语义向量)
- **检索增强**: LightRAG、Reranker
- **多模态**: Vision Model、CogView-4
- **服务**: Ingest Service (Excel 导入)

#### 关键设计亮点

1. **双重路由保险**: 启发式关键词快速匹配 + LLM 深度理解
2. **Map-Reduce 任务分解**: Planner 分解 → Tool Selection 选择 → 并行执行
3. **PostgreSQL 优先兜底链**: 结构化优先 → 向量兜底 → 外部兜底
4. **Reranker 双阈值**: 相似度 + 重排分数双重过滤
5. **LangGraph Checkpointer**: 维护会话状态和对话历史
6. **多源融合**: LLM 综合 Milvus、PostgreSQL、External 多源信息
7. **安全防护**: 每个查询都经过 Guardrails 检查

---
 
## 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。

---

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [LangChain](https://python.langchain.com/) - LLM应用开发框架
- [Milvus](https://milvus.io/) - 企业级开源向量数据库
- [Cohere Rerank](https://cohere.com/rerank) / [Jina AI](https://jina.ai/) / [Voyage AI](https://www.voyageai.com/) - 二阶段重排序API服务
- [React](https://react.dev/) - 用户界面库

---

## 联系方式

- 项目主页: https://github.com/<your-username>/chushen-assistant
- 问题反馈: 请在 GitHub Issues 中提交

 
---

<div align="center">

**厨神助手** — 让 AI 成为你的厨房顾问

[回到顶部](#厨神助手--中华菜谱智能问答)

</div>
