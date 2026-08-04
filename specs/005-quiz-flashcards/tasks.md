# Tasks: 005 - 测验生成与闪卡（第一迭代）

**Input**: Design documents from `/specs/005-quiz-flashcards/`

**Prerequisites**: spec.md, plan.md

> 本 tasks 聚焦 **005 第一迭代：测验生成 + 闪卡**。后续迭代（掌握度/错题本/笔记/导出/学伴角色/打卡）不在本次。

## Phase 1: 数据模型与出题引擎

**Purpose**: Question/Flashcard 表 + LLM 出题解析

- [x] T001 修改 `backend/models.py`：新增 `Question`、`Flashcard` 表（含 course_id/study_set_id 范围、来源 source_timestamp/source_course_id）
- [x] T002 新建 `backend/ai/quiz_generator.py`：`generate_questions(full_text, count)` 与 `generate_flashcards(full_text, count)`——调 `create_llm()`，prompt 要求只输出 JSON 数组，正则提取首个 `[...]` 健壮解析，失败重试一次
- [x] T003 修改 `backend/schemas.py`：Question/Flashcard 响应模型、生成请求（course_id 或 study_set_id + count）、作答请求、熟悉度标记请求
- [x] T004 [P] 后端单元测试 `backend/tests/test_quiz_generator.py`：JSON 解析（含带前后废话/单题/异常情况）

**Checkpoint**: 出题引擎可独立测试

---

## Phase 2: User Story 1 - 测验生成（Priority: P1）

**Goal**: 一键生成选择/判断题，作答自动判分，来源可跳回视频

**Independent Test**: 对课程 1 生成 10 题，作答判分正确，解析可见，来源跳转

### 后端

- [x] T005 新建 `backend/services/quiz_service.py`：生成（取全文→quiz_generator→存库，追加式）、清空重生成、列表、作答判分（比对预设答案）；学习集则拼接集合内多课全文并记录 source_course_id
- [x] T006 新建 `backend/api/quiz.py`：`POST /api/quiz/generate`（course_id 或 study_set_id + count）、`GET /api/quiz?course_id=|study_set_id=`、`POST /api/quiz/{id}/answer`（判分）、`DELETE /api/quiz?...`（清空该范围）
- [x] T007 修改 `backend/main.py`：挂载 quiz 路由
- [x] T008 [P] 后端单元测试 `backend/tests/test_quiz_service.py`：生成追加、清空重生成、选择/判断判分正确

### 前端

- [x] T009 修改 `frontend-next/lib/api.ts` + `hooks/use-api.ts`：测验接口类型与 hooks（useQuestions、useGenerateQuiz、useSubmitQuizAnswer、useClearQuiz）
- [x] T010 新建 `frontend-next/components/QuizPanel.tsx`：生成按钮（含清空重生成）、题目列表、单选/判断作答、提交判分、对错+解析展示、来源 chip 跳转
- [x] T011 修改 `frontend-next/app/courses/[id]/page.tsx`：学习页加"测验"入口（Tab），嵌入 QuizPanel

**Checkpoint**: US1 可独立演示

---

## Phase 3: User Story 2 - 闪卡（Priority: P1）

**Goal**: 一键生成闪卡，翻卡 + 三档熟悉度标记 + 统计

**Independent Test**: 对课程 1 生成闪卡，翻背面，标记认识/模糊/不认识，统计持久化

### 后端

- [x] T012 新建 `backend/services/flashcard_service.py`：生成（复用 quiz_generator）、列表、三档熟悉度标记、统计计数、清空
- [x] T013 新建 `backend/api/flashcards.py`：`POST /api/flashcards/generate`、`GET /api/flashcards?...`、`PATCH /api/flashcards/{id}`（标记熟悉度）、`GET /api/flashcards/stats?...`、`DELETE /api/flashcards?...`
- [x] T014 修改 `backend/main.py`：挂载 flashcards 路由
- [x] T015 [P] 后端单元测试 `backend/tests/test_flashcard_service.py`：生成、三档标记、统计正确

### 前端

- [x] T016 修改 `frontend-next/lib/api.ts` + `hooks/use-api.ts`：闪卡接口类型与 hooks
- [x] T017 新建 `frontend-next/components/FlashcardPanel.tsx`：生成按钮、卡片翻转（正/背面）、上一张/下一张、三档标记按钮、统计与筛选（只看模糊+不认识）、来源跳转
- [x] T018 修改 `frontend-next/app/courses/[id]/page.tsx`：学习页加"闪卡"入口，嵌入 FlashcardPanel

**Checkpoint**: US2 可独立演示

---

## Phase 4: 集成与验证

- [x] T019 学习集出题入口：QuizPanel/FlashcardPanel 范围参数化（course_id 或 study_set_id），在学习集/全局搜索处提供入口
- [x] T020 端到端验证：生成→作答/翻卡→判分/标记→来源跳转→追加与清空→统计持久化，按 checklists/validation.md 跑一遍
- [x] T021 前端 `tsc --noEmit` 通过；后端全部 pytest 通过

---

## Phase 5: 第二迭代续 — 掌握度/导出/打卡/时间段总结/图片询问/章节速览

**Purpose**: 收尾 005 第二迭代剩余功能 + 用户新增的 4 个学习增强功能

- [x] T022 闪卡/错题导出（`backend/services/export_service.py` + `/api/export`）：闪卡 Markdown（按熟悉度分组）/ Anki TSV；错题 Markdown（题目/正确答案/解析/来源）。前端 FlashcardPanel、QuizPanel 错题本加导出入口（`downloadExport`）
- [x] T023 学习 streak 打卡（`backend/services/study_stats_service.py` + `/api/study-stats`）：零侵入聚合问答/做题/笔记/闪卡的 created_at 日期，算连续天数（含一天宽限）；前端 StreakCard（连续/累计天数 + 30 天热力图）放课程库页
- [x] T024 掌握度仪表盘（`backend/services/dashboard_service.py` + `/api/dashboard`）：聚合测验正确率、闪卡熟悉度、错题掌握度、笔记数、已完成课程数；前端 DashboardPanel（统计卡 + 进度条）放课程库页
- [x] T025 时间段总结（`backend/services/segment_service.py` + `/api/segment/summarize`）：取视频某时间区间内字幕/课件，LLM 要点总结；前端 SegmentSummary（当前时间 ±2/3/5 分钟）放课程页视频下方
- [x] T026 上传图片询问（`ChatService` 加 image 分支 + `ChatRequest.image`）：图片→视觉模型描述→结合问题由 chat LLM 回答，不走 RAG、不要求课程已完成；前端 ChatPanel 加图片上传（base64 data url，预览/移除）
- [x] T027 本章节速览（`Chapter` 模型 + `backend/services/chapter_service.py` + `/api/courses/{id}/chapters`）：按时间窗口自动分章（3-12 章）、AI 批量生成标题/速览、首次生成缓存到库；前端 ChaptersPanel 放课程页总结 Tab，点击跳转视频
- [x] T028 端到端验证：后端 pytest 全过（109 项，新增 38）、前端 tsc 通过、运行中后端真实接口（study-stats/dashboard/export）curl 验证通过

---

## Phase 6: 会话制问答 + 学伴增强 + 思维导图/周报（005 收尾）

**Purpose**: ChatGPT 式多轮会话 + 可拖动学伴 + 第三迭代（思维导图、学习周报）

- [x] T029 会话制问答：`Conversation` 模型 + `ChatMessage.conversation_id`；`ask` 支持 conversation_id 续写、带最近 6 条历史；RAG `query*` 加 history 参数；旧消息自动迁移成历史会话（含 reload 自愈清理）；前端 ConversationSwitcher（切换/新建/改名/删除）+ 历史页按会话分组
- [x] T030 图片询问增强：ChatPanel 支持粘贴/拖拽上传图片 → 视觉描述 + chat LLM 回答
- [x] T031 可拖动学伴：形象作拖动手柄，位置 localStorage 记忆、边界限制；收起按钮
- [x] T032 思维导图：`MindMap` 模型 + `MindMapService`（LLM 生成树状知识结构，限深限宽，缓存）；`/api/courses/{id}/mindmap`；前端 MindMapPanel 递归渲染树（课程页总结 Tab）
- [x] T033 学习周报：`WeeklyReportService` 聚合最近 7 天（答题正确率/新增闪卡/笔记/提问/学习天数）；`/api/weekly-report`；前端 WeeklyReport（课程库页）
- [x] T034 验证：后端 pytest 全过（127 项）、前端 tsc 通过

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1（模型+出题引擎）必须先完成
- Phase 2（测验）与 Phase 3（闪卡）共享出题引擎，可串行（先测验）或并行
- Phase 4（集成验证）在最后

### 推荐执行顺序

1. Phase 1（模型 + 出题引擎）
2. Phase 2（US1 测验）
3. Phase 3（US2 闪卡）
4. Phase 4（集成 + 验证）

### Parallel Opportunities

- T004（出题引擎测试）与 T005-T007（测验后端）可并行
- Phase 3 闪卡与 Phase 2 测验前端组件（T010/T017）可并行

---

## Notes

- 每个任务完成建议单独提交。
- 新表 create_all 幂等，无需删库。
- LLM JSON 解析必须容错（提取首个 `[...]` 块 + 重试一次），否则出题易失败。
- 学习集全文拼接控制长度（FULL_TEXT_MAX_CHARS），超长截断。
- 测验/闪卡入口放课程学习页 Tab，不新增顶层导航（入口职责单一）。
- 后续迭代（掌握度/错题本/学伴角色等）已在 plan 架构预留，本 tasks 不实现。
