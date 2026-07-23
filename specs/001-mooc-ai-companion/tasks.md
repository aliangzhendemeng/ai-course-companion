---

description: "Task list for AI 慕课学伴 MVP implementation"

---

# Tasks: AI 慕课学伴

**Input**: Design documents from `/specs/001-mooc-ai-companion/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md)

**Tests**: 包含单元测试和集成测试任务。

**Organization**: 任务按用户故事分组，支持独立实现和验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3）
- 描述中包含明确的文件路径

---

## Phase 1: Setup（项目初始化与共享基础设施）

**目标**: 搭建项目结构、安装依赖、配置管理和数据库基础。

- [ ] T001 创建项目目录结构（backend/frontend/tests/data/specs）
- [ ] T002 [P] 编写 `requirements.txt`，锁定核心依赖版本
- [ ] T003 [P] 编写 `.env.example` 和 `backend/config.py`，支持配置视觉模型、LLM、抽帧参数、本地 VLM 路径和设备
- [ ] T004 配置 `.gitignore`，排除 `data/`、`venv/`、`.env`、模型缓存等
- [ ] T005 编写 `README.md`，包含项目简介、安装步骤和启动命令
- [ ] T006 初始化 SQLModel 数据库连接（`backend/database.py`）
- [ ] T007 [P] 实现所有 SQLModel 数据模型（`backend/models/course.py`、`transcript.py`、`frame.py`、`summary.py`、`chat_message.py`、`progress.py`）
- [ ] T008 创建数据库表初始化脚本（`backend/init_db.py`）
- [ ] T009 配置 pytest 和测试目录结构（`tests/conftest.py`）

**检查点**: 项目可安装依赖，数据库表可初始化，单元测试框架可用。

---

## Phase 2: Foundational（核心基础设施，阻塞所有用户故事）

**目标**: 完成视频/音频处理、OCR、ASR、视觉理解、LLM 的底层能力封装。

**⚠️ 关键**: 本阶段完成前，不能开始任何用户故事的具体实现。

- [ ] T010 [P] 实现音频提取模块（`backend/core/audio_extractor.py`）：视频 → WAV
- [ ] T011 [P] 实现视频抽帧模块（`backend/core/frame_extractor.py`）：均匀采样，上限 120 帧
- [ ] T012 实现 ASR 引擎（`backend/core/asr_engine.py`）：基于 faster-whisper，输出带时间戳字幕
- [ ] T013 实现 OCR 引擎（`backend/core/ocr_engine.py`）：基于 PaddleOCR，过滤置信度 > 0.6
- [ ] T014 实现视觉分析抽象接口和 DeepSeek-VL 实现（`backend/ai/vision/base.py`、`deepseek_vision.py`），支持 API 不可用时降级为纯 OCR
- [ ] T015 [P] 预留 Gemini Vision 实现（`backend/ai/vision/gemini_vision.py`）
- [ ] T015b [P] 预留本地 VLM 接口（`backend/ai/vision/local_vlm_vision.py`）：定义 `LocalVLMVisionAnalyzer` 类，实现 `understand_frame` 方法占位，读取 `LOCAL_VLM_MODEL_PATH` 和 `LOCAL_VLM_DEVICE` 配置
- [ ] T016 实现 LLM 抽象接口和 DeepSeek Chat 实现（`backend/ai/llm/base.py`、`deepseek_llm.py`）
- [ ] T017 [P] 预留 Gemini/Claude LLM 实现（`backend/ai/llm/gemini_llm.py`、`claude_llm.py`）
- [ ] T018 编写核心模块单元测试（`tests/unit/core/`）

**检查点**: 每个核心模块可独立运行并通过单元测试。例如：给定测试视频，能提取音频、字幕、帧、OCR 文字和视觉描述。

---

## Phase 3: User Story 1 - 上传视频并获取课程总结（Priority: P1）🎯 MVP

**目标**: 用户上传视频后，系统完成多模态处理并生成三级总结。

**独立验证**: 上传测试视频，处理完成后能在 Streamlit 课程学习页面看到大纲、摘要、讲义。

### 测试（先写先失败）

- [ ] T019 [P] [US1] 编写课程上传集成测试（`tests/integration/test_upload.py`）
- [ ] T020 [P] [US1] 编写总结生成集成测试（`tests/integration/test_summary.py`）

### 实现

- [ ] T021 [US1] 实现课程服务（`backend/services/course_service.py`）：创建课程、更新状态、查询列表
- [ ] T022 [US1] 实现课程处理编排器（`backend/ai/processor.py`）：串联音频→字幕→抽帧→OCR→视觉→总结→索引
- [ ] T023 [US1] 实现三级总结生成器（`backend/ai/summarizer.py`）：输入字幕和帧信息，输出 outline / abstract / lecture_notes
- [ ] T024 [US1] 实现课程相关 API（`backend/api/courses.py`）：上传、列表、状态查询、删除
- [ ] T025 [US1] 实现总结相关 API（`backend/api/summaries.py`）：获取课程总结
- [ ] T026 [US1] 实现 Streamlit 课程库页面（`frontend/pages/01_课程库.py`）：上传、展示处理状态、课程列表，使用 `stqdm` 展示进度
- [ ] T027 [US1] 实现 Streamlit 课程学习页面（`frontend/pages/02_课程学习.py`）：展示大纲/摘要/讲义，使用 `streamlit-player` 播放视频

**检查点**: US1 独立完成。用户上传视频后，能看到完整总结。

---

## Phase 4: User Story 2 - 基于课程内容进行知识问答（Priority: P2）

**目标**: 用户针对已处理课程提问，系统基于 RAG 返回答案、时间戳和关键帧。

**独立验证**: 在问答页面提问，得到基于课程内容的回答，并附带时间戳和关键帧。

### 测试（先写先失败）

- [ ] T028 [P] [US2] 编写 RAG 检索单元测试（`tests/unit/ai/test_rag_engine.py`）
- [ ] T029 [P] [US2] 编写问答 API 集成测试（`tests/integration/test_chat.py`）

### 实现

- [ ] T030 [US2] 实现 Chroma 向量索引构建（`backend/ai/rag_engine.py`：index_course 方法）
- [ ] T031 [US2] 实现 RAG 检索与答案生成（`backend/ai/rag_engine.py`：query 方法）
- [ ] T032 [US2] 实现问答服务（`backend/services/chat_service.py`）：保存历史、调用 RAG、组装来源
- [ ] T033 [US2] 实现问答 API（`backend/api/chat.py`）：提问、获取历史
- [ ] T034 [US2] 实现 Streamlit 知识问答页面（`frontend/pages/03_知识问答.py`）：提问、展示回答、时间戳、关键帧

**检查点**: US1 和 US2 都能独立工作。问答结果基于课程内容，能定位到时间戳。

---

## Phase 5: User Story 3 - 在视频学习页面中定位知识点（Priority: P3）

**目标**: 用户在课程学习页面播放视频，点击大纲/讲义/问答时间戳可跳转。

**独立验证**: 在学习页面点击时间戳，视频跳转到对应位置。

### 测试

- [ ] T035 [US3] 编写学习进度持久化测试（`tests/integration/test_progress.py`）

### 实现

- [ ] T036 [US3] 实现学习进度服务（`backend/services/progress_service.py`）
- [ ] T037 [US3] 实现进度 API（`backend/api/progress.py`）
- [ ] T038 [US3] 在课程学习页面集成视频播放器和时间戳跳转（`frontend/pages/02_课程学习.py`）
- [ ] T039 [US3] 在问答页面实现时间戳点击跳转学习页面（`frontend/pages/03_知识问答.py`）

**检查点**: 三个用户故事全部可用，端到端流程跑通。

---

## Phase 6: Polish & Cross-Cutting Concerns

**目标**: 完善文档、测试、性能和工程化。

- [ ] T040 [P] 补充单元测试覆盖率，核心模块覆盖 > 70%
- [ ] T041 实现错误处理和日志记录（统一异常响应、状态机失败重试）
- [ ] T042 优化长视频处理性能（异步处理、避免阻塞 Streamlit）
- [ ] T043 编写 API/模块契约文档（`specs/001-mooc-ai-companion/contracts/api.md`）
- [ ] T044 [P] 更新 `README.md`、`quickstart.md` 和项目文档
- [ ] T045 运行 `quickstart.md` 端到端验证，确保 30 分钟内可跑通
- [ ] T046 代码清理和重构，消除重复逻辑

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
User Story 3 (P3)
  ↓
Polish (Phase 6)
```

### 用户故事依赖

- **US1 (P1)**: 仅依赖 Foundational 阶段。
- **US2 (P2)**: 依赖 US1 生成的总结和索引，但实现时通过接口解耦。
- **US3 (P3)**: 依赖 US1 的课程页面和 US2 的问答结果，但主要是前端集成。

### 可并行机会

- Phase 1 中 T002-T009 标记 [P] 的任务可并行。
- Phase 2 中 T010-T018 标记 [P] 的任务可并行。
- 每个用户故事的测试任务和模型任务可并行。

---

## 实现策略

### MVP First（仅 US1）

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. **停止并验证**: 独立测试 US1
5. 如 US1 工作正常，再继续 US2

### 增量交付

1. Setup + Foundational → 基础能力就绪
2. US1 → 能上传视频并生成总结 → Demo
3. US2 → 能基于课程问答 → Demo
4. US3 → 能学习时间戳跳转 → Demo
5. Polish → 文档、测试、性能优化

---

## 文件路径速查

| 模块 | 路径 |
|---|---|
| 后端入口 | `backend/main.py` |
| 配置管理 | `backend/config.py` |
| 数据库 | `backend/database.py` |
| 数据模型 | `backend/models/*.py` |
| 核心处理 | `backend/core/*.py` |
| AI 能力 | `backend/ai/*.py` |
| 服务层 | `backend/services/*.py` |
| API 路由 | `backend/api/*.py` |
| Streamlit 入口 | `frontend/Home.py` |
| Streamlit 页面 | `frontend/pages/*.py` |
| 前端组件 | `streamlit-player`、`stqdm` |
| 单元测试 | `tests/unit/**/*.py` |
| 集成测试 | `tests/integration/**/*.py` |
| 测试数据 | `tests/fixtures/` |

---

## 注意事项

- 每个任务完成后建议提交一次代码，保持提交粒度小且逻辑完整。
- 测试任务必须先写，确保在实现前测试失败（TDD）。
- 遇到外部 API 失败时，优先实现重试和错误状态，不阻塞主流程。
- 所有用户可见文本使用中文，代码注释和文档可中英混合。
