# Implementation Plan: AI 慕课学伴下一版本增强

**Branch**: `002-enhanced-rag-nextjs` | **Date**: 2026-07-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-enhanced-rag-nextjs/spec.md`

---

## Summary

在现有 AI 慕课学伴基础上，完成五个后端增强（多模型配置、视频流式播放、帧处理加速、混合检索、全局跨课程搜索）和一个现代前端增强（Next.js + TypeScript + Tailwind + shadcn/ui）。保留 Streamlit 前端作为托底，确保任一前端不可用时不影响后端核心能力。

---

## Technical Context

**Language/Version**: Python 3.10+（后端），TypeScript / Node 18+（前端）

**Primary Dependencies**:
- FastAPI 0.104+（后端 API）
- SQLModel 0.0.14+（SQLite ORM）
- Chroma 0.5+（向量库）
- langchain-community 0.2+（Chroma 封装）
- bm25s 0.2+（BM25 稀疏检索）
- jieba 0.42+（中文分词）
- openai 1.3+（DeepSeek 兼容客户端）
- google-generativeai、anthropic（Gemini / Claude 可选实现）
- Next.js 14+、React 18+、Tailwind CSS、shadcn/ui、Framer Motion、TanStack Query

**Storage**:
- SQLite（课程、字幕、帧、总结、问答历史、学习进度）
- 本地文件系统（上传视频、关键帧、Chroma 向量库、BM25 索引）

**Testing**: pytest（后端），Vitest + React Testing Library（前端，可选）

**Target Platform**: macOS（优先）、Linux（兼容）、Windows（尽力而为）

**Project Type**: Web 应用（后端 API + 双前端：Streamlit 托底 + Next.js 新版）

**Performance Goals**:
- 45 分钟课程处理时间从 10-20 分钟降至 5 分钟以内。
- 问答响应时间不超过 10 秒（不含模型首 token 延迟）。
- 视频流式接口支持任意位置 seek，首帧加载不超过 3 秒。

**Constraints**:
- 月度外部 API 成本可控，优先减少不必要视觉 API 调用。
- 所有外部模型可配置切换，避免供应商锁定。
- 保持 Streamlit 前端可用，不破坏现有 API 契约。
- 全局搜索暂不做权限隔离。

**Scale/Scope**:
- 单用户本地使用。
- 课程数量本期目标不超过 100 门。
- BM25 索引按课程文件存储，全局 BM25 定期重建。

---

## Constitution Check

对照项目宪法检查：

| 宪法原则 | 本计划如何满足 |
|---|---|
| 效果优先，成本可控 | 多模型配置让不同任务选最优模型；智能视觉调用减少付费 API 次数；场景变化抽帧减少冗余帧 |
| 用户数据本地优先 | 视频、帧、向量库、BM25 索引全部本地存储 |
| 中文课程优先优化 | BM25 使用 jieba 中文分词；保留中文 OCR/ASR |
| 简洁可维护 | 模块化设计，RAG/视觉/配置各自独立；保留 Streamlit 托底 |
| 可测试与可演示 | 每个用户故事可独立验证；新增单元测试与集成测试 |
| 渐进式交付 | 按 P1→P2→P3 顺序实现；Next.js 前端与后端改造解耦 |

---

## Project Structure

### Documentation（本功能）

```text
specs/002-enhanced-rag-nextjs/
├── spec.md              # 功能规格
├── plan.md              # 本文件
├── tasks.md             # 任务清单
└── checklists/
    └── requirements.md  # 验收检查清单
```

### Source Code（仓库根目录）

```text
ai-course-companion/
├── backend/
│   ├── config.py                  # 扩展多模型配置
│   ├── main.py                    # 新增 CORS、视频流路由
│   ├── schemas.py                 # 新增 video_url、scope、来源强类型
│   ├── ai/
│   │   ├── factory.py             # create_summary_llm / create_chat_llm / create_vision_analyzer
│   │   ├── llm/
│   │   │   ├── deepseek_llm.py    # 支持配置化 model/api_key
│   │   │   ├── gemini_llm.py      # 实现 Gemini 聊天
│   │   │   └── claude_llm.py      # 实现 Claude 聊天
│   │   ├── vision/
│   │   │   ├── deepseek_vision.py # 支持配置化 model/api_key
│   │   │   ├── gemini_vision.py   # 实现 Gemini Vision
│   │   │   └── claude_vision.py   # 新增 Claude Vision
│   │   ├── frame_enricher.py      # 新增：OCR + 复杂度判定 + 并发 VLM
│   │   ├── frame_complexity.py    # 新增：帧复杂度规则判断
│   │   ├── text_utils.py          # 新增：jieba 分词工具
│   │   ├── rank_utils.py          # 新增：RRF 融合
│   │   ├── rag_engine.py          # 混合检索 + 全局索引
│   │   └── summarizer.py          # 使用 create_summary_llm
│   ├── core/
│   │   └── frame_extractor.py     # 场景变化抽帧 + 均匀抽帧 fallback
│   ├── api/
│   │   ├── courses.py             # 新增 /{id}/video 流式接口
│   │   └── chat.py                # 支持 scope 参数
│   └── services/
│       ├── chat_service.py        # 支持全局搜索
│       └── course_service.py      # 删除时同步清理全局索引
├── frontend/                      # 现有 Streamlit（保留并做最小适配）
├── frontend-next/                 # 新增 Next.js 前端
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── app/
│   │   ├── globals.css
│   │   ├── providers.tsx
│   │   ├── courses/page.tsx
│   │   ├── courses/[id]/page.tsx
│   │   └── chat/page.tsx
│   ├── components/
│   ├── hooks/
│   └── lib/api.ts
├── design-system/
│   └── MASTER.md                  # 已生成，Next.js 样式依据
├── data/                          # 运行时数据
│   ├── uploads/
│   ├── frames/
│   ├── chroma/
│   └── bm25/                      # 新增 BM25 索引目录
├── tests/
│   ├── unit/ai/test_rag_engine.py
│   ├── unit/ai/test_rrf.py
│   ├── unit/ai/test_frame_enricher.py
│   ├── unit/core/test_frame_extractor.py
│   ├── unit/test_video_api.py
│   └── unit/test_factory.py
├── .env.example
├── requirements.txt
├── start_frontend_next.sh         # 新增 Next.js 启动脚本
└── README.md
```

**Structure Decision**: 保留现有 backend/frontend 结构，新增 frontend-next/ 作为下一代前端。BM25 索引存放在 `data/bm25/`，与 Chroma 向量库并列。所有新后端功能对 Streamlit 保持兼容。

---

## Complexity Tracking

| 潜在复杂度 | 是否引入 | 说明 |
|---|---|---|
| 双前端并存 | 是 | Streamlit 托底 + Next.js 新版。理由：新版前端如果走不通，旧版仍可立即使用，符合宪法“渐进式交付”。 |
| 新增搜索引擎 | 是 | BM25 稀疏检索。理由：纯向量检索对精确关键词弱，是本期核心目标。 |
| 全局索引 | 是 | global_courses collection + 全局 BM25。理由：跨课程搜索需要，否则要遍历所有课程 collection。 |
| 任务队列 | 否 | 仍使用 FastAPI BackgroundTasks。 |
| 微服务 | 否 | 单后端进程。 |
| 多用户认证 | 否 | 单用户本地使用。 |
| 模型注册表 | 是 | factory.py 中通过配置字典创建模型，避免 if/else 无限膨胀。 |

---

## 关键设计决策

### 1. 多模型配置

- 新配置项：`SUMMARY_MODEL`、`CHAT_MODEL`、`VISION_MODEL` 以及 `SUMMARY_API_KEY`、`CHAT_API_KEY`、`VISION_API_KEY`。
- 回退逻辑：新项为空时，依次回退到 `LLM_MODEL` / `VISION_MODEL` / `DEEPSEEK_API_KEY`。
- factory.py 提供 `create_summary_llm()`、`create_chat_llm()`、`create_vision_analyzer()`，内部根据配置字典选择 provider 和 model。

### 2. 视频流式播放

- `CourseDetail.video_path` 改为响应层 `video_url`（不改动数据库）。
- 新增 `GET /api/courses/{course_id}/video`，返回 `FileResponse` 或手动 `Range` 分块。
- 根据文件后缀设置 `Content-Type`，支持 mp4/mkv/mov/avi。

### 3. 帧处理加速

- `FrameExtractor` 支持 `mode=uniform|scene`，默认 `scene`，阈值和最小间隔可配置。
- 新增 `FrameComplexityAnalyzer`，基于 OCR 文本长度、公式/代码符号、图表关键词做规则判断。
- 新增 `FrameEnricher`，顺序 OCR → 批量判定 → ThreadPoolExecutor 并发调用 VLM → 失败回退 OCR。
- `VideoProcessor._enrich_frames` 替换为调用 `FrameEnricher.enrich()`。

### 4. 混合检索

- 引入 `bm25s` + `jieba` 中文分词。
- 生成稳定 `doc_id`，同一文档写入课程 collection、全局 collection、课程 BM25、全局 BM25。
- 查询时使用 RRF 融合向量检索 Top-K 与 BM25 Top-K。
- 配置项：`rag_vector_k`、`rag_bm25_k`、`rag_rrf_k`、`rag_top_k`。

### 5. 全局跨课程搜索

- 新增 `global_courses` Chroma collection，metadata 含 `course_id`。
- 新增全局 BM25 索引文件 `data/bm25/global.bm25`。
- `RAGEngine.query_all(question)` 在全局 collection 和全局 BM25 上检索，返回结果带 `course_id`。
- `ChatService.ask(course_id, question, scope)` 根据 scope 选择 query 或 query_all。
- 删除课程时同步删除全局 collection 中该课程 docs，并重建全局 BM25。

### 6. Next.js 前端

- 技术栈：Next.js 14 App Router + TypeScript + Tailwind CSS + shadcn/ui + Framer Motion + TanStack Query。
- 页面：课程库 `/courses`、课程学习 `/courses/[id]`、知识问答 `/chat`。
- 样式严格遵循 `design-system/MASTER.md`：青绿色主调、Inter 字体、卡片式布局、流式聊天、来源卡片。
- 保留 `frontend/` Streamlit 不变，仅把 `video_path` 改为 `video_url`。

---

## 验证策略

### 后端验证

1. 单元测试：
   - `test_factory.py`：多模型配置与回退。
   - `test_video_api.py`：Range 请求返回 206。
   - `test_frame_extractor.py`：场景模式返回合理帧数。
   - `test_frame_enricher.py`：简单帧不触发 VLM，复杂帧并发，失败回退。
   - `test_rrf.py`：RRF 融合公式正确。
   - `test_rag_engine.py`：混合检索、全局搜索、删除清理。

2. 集成测试：
   - 使用合成短视频 + FakeASR/FakeOCR/FakeVision/FakeLLM 验证上传 → 处理 → 单课问答 → 全局问答 → 删除完整流程。

3. 手动端到端：
   - 使用真实 10-20 分钟视频和 DeepSeek key 跑一遍，记录处理耗时。
   - 在 Next.js 前端和 Streamlit 前端分别验证视频播放、问答、全局搜索。

### 前端验证

1. 手动 QA：
   - 课程库上传、状态展示、进入学习页。
   - 视频播放、seek、进度保存。
   - 三级总结标签页、时间戳跳转。
   - 单课问答、全局问答切换、来源卡片跳转。
   - 响应式：375px / 768px / 1024px / 1440px。

2. 可选组件测试：
   - `VideoPlayer`、`SourceCard`、`ChatPanel` 使用 Vitest + React Testing Library。

---

## 风险与应对

| 风险 | 应对 |
|---|---|
| BM25s 对中文支持差 | 强制使用 jieba 分词，不依赖库默认分词 |
| 并发 VLM 触发限流 | 可配置 `vision_max_workers`，加 tenacity 指数退避 |
| 场景变化阈值难调 | 默认保守阈值，提供配置项，先以 uniform 跑通再切 scene |
| 全局 BM25 重建慢 | 课程数少时全量重建，后续再优化增量删除 |
| Streamlit 与 Next.js 前端状态不同步 | 两者都消费同一后端 API，状态由后端决定 |
| Next.js 开发环境 CORS | main.py 配置 CORS，放行 localhost:3000 和 localhost:8501 |
| 视频 Range 请求实现不当导致无法 seek | 必须实现 206 + Content-Range，用 HTML5 播放器验证 |

---

## Critical Files for Implementation

- `/Users/conglin/Projects/ai-course-companion/backend/config.py`
- `/Users/conglin/Projects/ai-course-companion/backend/ai/factory.py`
- `/Users/conglin/Projects/ai-course-companion/backend/ai/rag_engine.py`
- `/Users/conglin/Projects/ai-course-companion/backend/core/frame_extractor.py`
- `/Users/conglin/Projects/ai-course-companion/backend/ai/frame_enricher.py`
- `/Users/conglin/Projects/ai-course-companion/backend/api/courses.py`
- `/Users/conglin/Projects/ai-course-companion/backend/api/chat.py`
- `/Users/conglin/Projects/ai-course-companion/backend/services/course_service.py`
- `/Users/conglin/Projects/ai-course-companion/frontend-next/`
