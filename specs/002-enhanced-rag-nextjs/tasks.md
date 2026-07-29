---

description: "Task list for AI 慕课学伴下一版本增强"

---

# Tasks: AI 慕课学伴下一版本增强

**Input**: Design documents from `/specs/002-enhanced-rag-nextjs/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: 包含单元测试和集成测试任务。

**Organization**: 任务按用户故事分组，支持独立实现和验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3, US4）
- 描述中包含明确的文件路径

---

## Phase 1: Setup（项目初始化与共享基础设施）

**目标**: 准备本版本所需的目录、依赖、配置模板。

- [ ] T001 创建 `data/bm25/` 目录并在 `.gitignore` 中排除
- [ ] T002 [P] 更新 `requirements.txt`：新增 `bm25s`、`jieba`、`tenacity`
- [ ] T003 [P] 更新 `.env.example`：新增 `SUMMARY_MODEL`、`CHAT_MODEL`、`VISION_MODEL`、`SUMMARY_API_KEY`、`CHAT_API_KEY`、`VISION_API_KEY`、`FRAME_EXTRACTION_MODE`、`SCENE_CHANGE_THRESHOLD`、`MIN_SCENE_INTERVAL`、`VISION_MAX_WORKERS`、`RAG_VECTOR_K`、`RAG_BM25_K`、`RAG_RRF_K`、`FRONTEND_ORIGIN`
- [ ] T004 创建 `frontend-next/` 目录并初始化 Next.js + shadcn/ui 项目骨架
- [ ] T005 创建 `start_frontend_next.sh` 启动脚本

**检查点**: 后端依赖可安装，Next.js 项目可初始化，新增配置项有示例。

---

## Phase 2: Foundational（核心基础设施，阻塞所有用户故事）

**目标**: 完成配置管理、模型工厂、公共工具类的改造。

**⚠️ 关键**: 本阶段完成前，不能开始任何用户故事的具体实现。

- [ ] T010 重构 `backend/config.py`：新增多模型配置字段与回退逻辑，关闭 `extra="ignore"` 改为 `extra="forbid"` 或至少记录未知键
- [ ] T011 重构 `backend/ai/factory.py`：新增 `create_summary_llm()`、`create_chat_llm()`、改造 `create_vision_analyzer()`；实现配置字典驱动的 provider 选择
- [ ] T012 [P] 改造 `backend/ai/llm/deepseek_llm.py`：支持通过构造函数传入 `api_key`、`model_name`、`base_url`
- [ ] T013 [P] 实现 `backend/ai/llm/gemini_llm.py`：`GeminiLLM.chat()` 使用 `google.generativeai`
- [ ] T014 [P] 实现 `backend/ai/llm/claude_llm.py`：`ClaudeLLM.chat()` 使用 `anthropic` SDK
- [ ] T015 [P] 改造 `backend/ai/vision/deepseek_vision.py`：支持通过构造函数传入 `api_key`、`model_name`
- [ ] T016 [P] 实现 `backend/ai/vision/gemini_vision.py`：`GeminiVisionAnalyzer.understand_frame()`
- [ ] T017 [P] 新增 `backend/ai/vision/claude_vision.py`：`ClaudeVisionAnalyzer.understand_frame()` 使用 base64 图片 + Claude Messages API
- [ ] T018 新增 `backend/ai/text_utils.py`：`tokenize_for_bm25(texts)` 使用 jieba 分词
- [ ] T019 新增 `backend/ai/rank_utils.py`：`rrf_fuse(list[list[dict]], k=60, top_n=5)` 实现 RRF 融合
- [ ] T020 更新 `backend/schemas.py`：`CourseDetail` 增加 `video_url: str`；`ChatRequest` 增加 `scope: str = "course"`；新增 `Source` 强类型模型
- [ ] T021 更新 `backend/main.py`：配置 `CORSMiddleware`，放行 `FRONTEND_ORIGIN`、`localhost:3000`、`localhost:8501`

**检查点**: 工厂函数可通过配置创建不同模型；CORS 配置正确；schema 扩展不破坏旧接口。

---

## Phase 3: User Story 1 - 多模型配置与视频流式播放（Priority: P1）🎯 MVP

**目标**: 用户可为总结、聊天、视觉配置不同模型；课程学习页通过后端 URL 流式播放视频。

**独立验证**: 配置多模型后上传处理一门课程，Streamlit 学习页能正常播放视频；使用 curl 测试 `/api/courses/{id}/video` 返回 206。

### 测试（先写先失败）

- [ ] T022 [P] [US1] 更新 `tests/unit/test_factory.py`：验证 `create_summary_llm`、`create_chat_llm`、API Key 回退逻辑
- [ ] T023 [P] [US1] 新增 `tests/unit/test_video_api.py`：使用 `TestClient` 验证 200 与 206 Range 响应

### 实现

- [ ] T024 [US1] 更新 `backend/ai/summarizer.py`：`Summarizer` 使用 `create_summary_llm()`
- [ ] T025 [US1] 更新 `backend/ai/rag_engine.py`：`RAGEngine` 使用 `create_chat_llm()`
- [ ] T026 [US1] 更新 `backend/api/courses.py`：
  - `get_course` 构造 `video_url`
  - 新增 `GET /{course_id}/video` 接口，支持 Range 请求
- [ ] T027 [US1] 更新 `frontend/pages/02_课程学习.py`：使用 `course["video_url"]` 播放视频
- [ ] T028 [US1] 更新 `backend/ai/processor.py`：视觉分析器使用 `create_vision_analyzer()`

**检查点**: US1 独立完成。多模型配置生效，视频流式播放可用。

---

## Phase 4: User Story 2 - 帧处理加速（Priority: P2）

**目标**: 通过场景变化抽帧、智能视觉调用、并发 VLM 显著缩短处理时间。

**独立验证**: 上传测试视频，记录处理耗时；确认复杂帧被视觉理解，简单帧仅 OCR；确认并发数不超过配置。

### 测试（先写先失败）

- [ ] T029 [P] [US2] 新增 `tests/unit/core/test_frame_extractor.py`：合成两段明显不同的视频，验证 `scene` 模式返回合理帧数
- [ ] T030 [P] [US2] 新增 `tests/unit/ai/test_frame_complexity.py`：验证规则能区分简单帧与复杂帧
- [ ] T031 [P] [US2] 新增 `tests/unit/ai/test_frame_enricher.py`：验证简单帧不触发 VLM、复杂帧并发调用、失败回退 OCR

### 实现

- [ ] T032 [US2] 更新 `backend/core/frame_extractor.py`：新增 `mode` 参数，实现场景变化检测 + 均匀抽帧 fallback
- [ ] T033 [US2] 新增 `backend/ai/frame_complexity.py`：`FrameComplexityAnalyzer` 基于 OCR 结果判断是否需要 VLM
- [ ] T034 [US2] 新增 `backend/ai/frame_enricher.py`：`FrameEnricher.enrich()` 实现顺序 OCR → 复杂度判定 → ThreadPoolExecutor 并发 VLM → 失败回退
- [ ] T035 [US2] 更新 `backend/ai/processor.py`：`_enrich_frames` 替换为 `FrameEnricher.enrich()`；`frame_extractor` 使用新配置
- [ ] T036 [US2] 更新 `backend/config.py`：新增帧加速相关配置项

**检查点**: US2 独立完成。处理速度提升，复杂帧仍被理解，单帧失败不影响整体流程。

---

## Phase 5: User Story 3 - 混合检索与全局跨课程搜索（Priority: P2）

**目标**: RAG 同时支持向量检索与 BM25 稀疏检索并 RRF 融合；新增全局 collection 支持跨课程搜索。

**独立验证**: 索引两门课程后，分别测试单课问答、全局问答、精确关键词召回、删除课程后全局索引清理。

### 测试（先写先失败）

- [ ] T037 [P] [US3] 新增 `tests/unit/ai/test_rrf.py`：固定两组排序，验证 RRF 融合公式
- [ ] T038 [P] [US3] 更新 `tests/unit/ai/test_rag_engine.py`：
  - 验证混合检索结果优于纯向量检索的精确关键词召回
  - 验证 `query_all` 返回多课程来源
  - 验证 `delete_index` 同步清理全局 collection

### 实现

- [ ] T039 [US3] 更新 `backend/ai/rag_engine.py`：
  - 生成稳定 `doc_id`
  - 同时写入课程 collection、全局 collection、课程 BM25、全局 BM25
  - 新增 `query_all(question)` 方法
  - 删除时同步清理全局索引并重建全局 BM25
- [ ] T040 [US3] 更新 `backend/services/chat_service.py`：`ask()` 增加 `scope` 参数，根据 scope 调用 `query` 或 `query_all`
- [ ] T041 [US3] 更新 `backend/api/chat.py`：从 `ChatRequest` 读取 `scope` 并传给 `ChatService`
- [ ] T042 [US3] 更新 `backend/services/course_service.py`：`delete_course` 确保全局索引同步清理
- [ ] T043 [US3] 更新 `frontend/pages/03_知识问答.py`：支持选择搜索范围 `course` / `all`

**检查点**: US3 独立完成。混合检索与全局搜索可用，删除课程后全局索引干净。

---

## Phase 6: User Story 4 - 现代 React 前端（Priority: P3）

**目标**: 新增 Next.js 前端，覆盖课程库、课程学习、知识问答三页，保留 Streamlit 托底。

**独立验证**: 启动 Next.js 前端，完成上传 → 处理 → 学习 → 问答 → 全局搜索完整流程。

### 测试（可选）

- [ ] T044 [P] [US4] 新增 `frontend-next/__tests__/components/VideoPlayer.test.tsx`：验证播放器渲染
- [ ] T045 [P] [US4] 新增 `frontend-next/__tests__/components/SourceCard.test.tsx`：验证来源卡片渲染与点击

### 实现

- [ ] T046 [US4] 配置 `frontend-next/tailwind.config.ts` 与 `app/globals.css`，绑定 design-system/MASTER.md 颜色变量
- [ ] T047 [US4] 新增 `frontend-next/lib/api.ts`：封装后端 API 调用
- [ ] T048 [US4] 新增 `frontend-next/hooks/`：TanStack Query hooks（`useCourses`、`useCourse`、`useSummary`、`useAsk`）
- [ ] T049 [US4] 新增 `frontend-next/components/CourseCard.tsx`：课程卡片组件
- [ ] T050 [US4] 新增 `frontend-next/components/VideoPlayer.tsx`：HTML5 视频播放器，支持时间戳跳转
- [ ] T051 [US4] 新增 `frontend-next/components/SummaryTabs.tsx`：大纲/摘要/讲义标签页
- [ ] T052 [US4] 新增 `frontend-next/components/ChatPanel.tsx`：聊天流式展示 + 来源卡片
- [ ] T053 [US4] 新增 `frontend-next/components/UploadModal.tsx`：上传课程弹窗
- [ ] T054 [US4] 新增 `frontend-next/app/courses/page.tsx`：课程库页面
- [ ] T055 [US4] 新增 `frontend-next/app/courses/[id]/page.tsx`：课程学习页面
- [ ] T056 [US4] 新增 `frontend-next/app/chat/page.tsx`：知识问答页面（支持 scope 切换）
- [ ] T057 [US4] 新增 `frontend-next/app/layout.tsx`：根布局 + 侧边导航
- [ ] T058 [US4] 更新 `README.md`：补充 Next.js 启动说明

**检查点**: US4 独立完成。Next.js 前端可完成全流程，Streamlit 仍可托底使用。

---

## Phase 7: Polish & Cross-Cutting Concerns

**目标**: 文档、测试、性能优化与工程化收尾。

- [ ] T059 [P] 补充单元测试覆盖率，核心模块覆盖 > 70%
- [ ] T060 新增 `tests/integration/test_enhanced_flow.py`：使用 Fake 组件验证上传 → 处理 → 单课问答 → 全局问答 → 删除完整流程
- [ ] T061 给视觉 API 调用添加 `tenacity` 指数退避重试
- [ ] T062 优化 `RAGEngine` 嵌入模型加载：在 `ChatService` 级别复用 `RAGEngine` 实例，避免重复加载
- [ ] T063 编写 `specs/002-enhanced-rag-nextjs/checklists/requirements.md` 验收检查清单
- [ ] T064 [P] 更新 `README.md`、`.env.example`、相关启动脚本
- [ ] T065 运行端到端验证：真实视频 + DeepSeek key，记录处理耗时
- [ ] T066 代码清理与重构，消除重复逻辑

---

## 依赖关系与执行顺序

### 阶段依赖

```text
Setup (Phase 1)
  ↓
Foundational (Phase 2)  ← 阻塞所有用户故事
  ↓
User Story 1 (P1)
  ↓
User Story 2 (P2)
  ↓
User Story 3 (P2)
  ↓
User Story 4 (P3)
  ↓
Polish (Phase 7)
```

### 用户故事依赖

- **US1 (P1)**: 仅依赖 Foundational 阶段。
- **US2 (P2)**: 依赖 US1 的多模型配置与 processor 结构，但实现时通过接口解耦。
- **US3 (P2)**: 依赖 US1 的 RAG 结构，可与 US2 并行开发。
- **US4 (P3)**: 依赖 US1/US2/US3 的后端接口，主要是前端集成。

### 可并行机会

- Phase 1 中 T002-T005 标记 [P] 的任务可并行。
- Phase 2 中 T012-T017 标记 [P] 的任务可并行。
- US2 与 US3 可并行开发（都依赖 Foundational，互不阻塞）。
- US4 的组件任务可并行开发。

---

## 实现策略

### 增量交付

1. Setup + Foundational → 基础能力就绪
2. US1 → 多模型 + 视频流式 → Demo
3. US2 → 帧加速 → Demo
4. US3 → 混合检索 + 全局搜索 → Demo
5. US4 → Next.js 前端 → Demo
6. Polish → 文档、测试、性能优化

---

## 文件路径速查

| 模块 | 路径 |
|---|---|
| 后端配置 | `backend/config.py` |
| 模型工厂 | `backend/ai/factory.py` |
| RAG 引擎 | `backend/ai/rag_engine.py` |
| 帧抽取 | `backend/core/frame_extractor.py` |
| 帧增强器 | `backend/ai/frame_enricher.py` |
| 视频流 API | `backend/api/courses.py` |
| 问答 API | `backend/api/chat.py` |
| Streamlit 前端 | `frontend/pages/*.py` |
| Next.js 前端 | `frontend-next/` |
| 设计系统 | `design-system/MASTER.md` |

---

## 注意事项

- 每个任务完成后建议提交一次代码，保持提交粒度小且逻辑完整。
- 测试任务必须先写，确保在实现前测试失败（TDD）。
- 遇到外部 API 失败时，优先实现重试和错误状态，不阻塞主流程。
- 所有用户可见文本使用中文，代码注释和文档可中英混合。
- 保留 Streamlit 前端，任何后端改动都需验证 Streamlit 是否仍可用。
