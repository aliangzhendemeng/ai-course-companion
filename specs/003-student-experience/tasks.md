# Tasks: 003 - 学生体验优化（迭代 1）

**Input**: Design documents from `/specs/003-student-experience/`

**Prerequisites**: spec.md, plan.md

## Phase 1: 共享基础设施

**Purpose**: 数据库模型、配置服务、前端 API 封装

- [ ] T001 修改 `backend/models.py`：Course 增加 `progress_percent` 字段，ChatMessage 增加 `scope` 字段
- [ ] T002 创建 `backend/services/settings_service.py`：读写模型配置（`.env` 优先，兼容环境变量）
- [ ] T003 创建 `backend/api/settings.py`：GET/POST `/api/settings` 接口
- [ ] T004 修改 `backend/config.py`：读取配置时支持从 `settings_service` 覆盖
- [ ] T005 [P] 修改 `frontend-next/lib/api.ts`：新增 `getSettings`、`saveSettings`、`listChatHistory`、`getCourseDebug` 接口
- [ ] T006 [P] 修改 `frontend-next/hooks/use-api.ts`：新增 `useSettings`、`useChatHistoryAll`、`useCourseDebug` hooks

**Checkpoint**: 基础设施 ready，用户故事实现可以开始

---

## Phase 2: User Story 1 - 首次使用引导与模型配置（Priority: P1）

**Goal**: 学生首次打开应用即可在前端完成 API Key 和模型配置

**Independent Test**: 清空 `.env` 中 API Key，打开前端自动进入欢迎页，配置后能正常使用

### Implementation

- [ ] T007 创建 `frontend-next/app/welcome/page.tsx`：首次使用引导页，展示默认推荐模型
- [ ] T008 创建 `frontend-next/app/settings/page.tsx`：模型/API 配置表单页
- [ ] T009 创建 `frontend-next/components/SettingsForm.tsx`：可复用的配置表单组件
- [ ] T010 修改 `frontend-next/app/layout.tsx` 或中间件：首次访问时检测配置状态，未配置跳转 `/welcome`
- [ ] T011 修改 `frontend-next/components/Sidebar.tsx`：增加“设置”入口
- [ ] T012 后端 `SettingsService` 处理默认值和 Key 回退逻辑（CHAT_API_KEY 为空时回退到 DEEPSEEK_API_KEY）
- [ ] T013 保存配置后给出明确提示：若写入 `.env` 需重启后端生效

**Checkpoint**: US1 可独立演示

---

## Phase 3: User Story 2 - 课程处理进度可视化（Priority: P1）

**Goal**: 课程卡片实时显示处理百分比和当前阶段

**Independent Test**: 上传视频后，课程卡片显示进度条从 0% 到 100%

### Implementation

- [ ] T014 修改 `backend/ai/processor.py`：在每个处理阶段更新 `course.progress_percent`
  - extracting_audio: 0-10%
  - transcribing: 10-40%
  - extracting_frames: 40-55%
  - ocr_and_vision: 55-80%
  - generating_summary: 80-90%
  - indexing_rag: 90-100%
  - completed/failed: 100%
- [ ] T015 修改 `backend/services/course_service.py`：增加 `update_progress` 方法
- [ ] T016 修改 `frontend-next/components/CourseCard.tsx`：显示 Progress 组件和阶段文字
- [ ] T017 修改 `frontend-next/hooks/use-api.ts`：`useCourses` 轮询间隔从 5s 改为 2s，进度更新更平滑

**Checkpoint**: US2 可独立演示

---

## Phase 4: User Story 4 - 答案 Markdown 渲染（Priority: P2）

**Goal**: 答案中的 Markdown 格式正确渲染

**Independent Test**: 提问后答案里的 `**` 显示为加粗，列表显示为列表

### Implementation

- [ ] T018 安装依赖：`react-markdown`、`remark-gfm`
- [ ] T019 创建 `frontend-next/components/MarkdownRenderer.tsx`：安全的 Markdown 渲染组件
- [ ] T020 修改 `frontend-next/components/ChatPanel.tsx`：答案文本用 MarkdownRenderer 渲染
- [ ] T021 确保来源 chip 在 Markdown 渲染后仍可点击跳转

**Checkpoint**: US4 可独立演示

---

## Phase 5: User Story 5 - 视频跳转与时间戳去重（Priority: P2）

**Goal**: 点击来源 chip 视频跳转，相近时间戳合并

**Independent Test**: 点击 chip 视频 seek，同一页 PPT 的多个来源只显示一个 chip

### Implementation

- [ ] T022 创建 `frontend-next/lib/timestamp.ts`：`formatTimestamp`、`deduplicateSources`（按 5 秒阈值合并）
- [ ] T023 修改 `frontend-next/components/ChatPanel.tsx`：`SourceChip` 支持合并显示“N 个来源”
- [ ] T024 修改 `frontend-next/app/courses/[id]/page.tsx`：确保 videoRef.seek 在 chip 点击时生效
- [ ] T025 后端 `RAGEngine._format_sources` 可选增加时间戳聚类（或纯前端去重，优先前端）

**Checkpoint**: US5 可独立演示

---

## Phase 6: User Story 3 - 问答历史统一保存与查看（Priority: P2）

**Goal**: 单课程和全局搜索问答都保存到统一历史页面

**Independent Test**: 课程问答和全局搜索后，历史页能看到两条记录

### Implementation

- [ ] T026 修改 `backend/services/chat_service.py`：`ask` 方法保存 `scope` 到 ChatMessage
- [ ] T027 修改 `backend/api/chat.py`：全局搜索接口也保存历史（复用 chat_service）
- [ ] T028 创建 `backend/api/history.py`：`GET /api/history` 返回所有历史记录
- [ ] T029 创建 `frontend-next/app/history/page.tsx`：问答历史列表页
- [ ] T030 创建 `frontend-next/components/HistoryCard.tsx`：单条历史记录卡片
- [ ] T031 修改 `frontend-next/components/Sidebar.tsx`：顶部导航增加“问答历史”

**Checkpoint**: US3 可独立演示

---

## Phase 7: User Story 6 - 课程内容诊断可视化页（Priority: P2）

**Goal**: 展示字幕、OCR、帧图、总结、问答 Debug

**Independent Test**: 打开诊断页，能看到课程处理后的全部中间数据

### Implementation

- [ ] T032 创建 `backend/api/debug.py`：
  - `GET /api/courses/{course_id}/debug/transcripts`
  - `GET /api/courses/{course_id}/debug/frames`
  - `GET /api/courses/{course_id}/debug/summary`
  - `GET /api/chat/{message_id}/debug`：返回 prompt、上下文、模型、原始回答
- [ ] T033 修改 `backend/ai/rag_engine.py`：`_query_with_full_text` 和 `_answer_with_docs` 记录并返回诊断信息
- [ ] T034 创建 `frontend-next/app/courses/[id]/debug/page.tsx`：诊断页主体
- [ ] T035 创建 `frontend-next/components/DebugTimeline.tsx`：字幕/OCR/帧图时间轴
- [ ] T036 创建 `frontend-next/components/DebugChat.tsx`：问答 Debug 面板
- [ ] T037 创建 `frontend-next/components/DebugSummary.tsx`：总结原始内容面板
- [ ] T038 在“开始学习”页面增加“诊断”入口按钮

**Checkpoint**: US6 可独立演示

---

## Phase 8: 导航优化（贯穿多个 US）

**Goal**: 明确区分课程库、全局搜索、开始学习

**Independent Test**: 顶部导航只有“课程库”和“全局搜索”，开始学习从课程卡片进入

### Implementation

- [ ] T039 修改 `frontend-next/components/Sidebar.tsx`：导航改为“课程库”、“全局搜索”、“问答历史”、“设置”
- [ ] T040 修改 `frontend-next/app/chat/page.tsx`：改为全局搜索页，默认 scope=all
- [ ] T041 修改 `frontend-next/app/courses/[id]/page.tsx`：内置问答面板，移除独立“开始学习”导航入口
- [ ] T042 修改 `frontend-next/app/courses/page.tsx`：已完成课程卡片点击进入课程详情/学习页

**Checkpoint**: 导航结构符合宪法中的“入口职责单一”

---

## Phase 9: 测试与验证

**Purpose**: 每个用户故事独立可验证

- [ ] T043 [P] 后端单元测试：`SettingsService` 默认值和回退逻辑
- [ ] T044 [P] 后端单元测试：`ChatService` 保存 `scope`
- [ ] T045 [P] 后端单元测试：`CourseService.update_progress`
- [ ] T046 前端 Playwright 测试：首次引导流程
- [ ] T047 前端 Playwright 测试：问答历史页面加载
- [ ] T048 前端 Playwright 测试：点击来源 chip 视频跳转
- [ ] T049 端到端验证：按 checklists/validation.md 跑一遍

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1（基础设施）必须先完成
- Phase 2-7 的用户故事可并行或按优先级串行
- Phase 8（导航优化）建议在 US1、US3 完成后做
- Phase 9（测试）在最后

### 推荐执行顺序

1. Phase 1
2. Phase 2（US1 配置页）
3. Phase 3（US2 进度条）
4. Phase 4（US4 Markdown）+ Phase 5（US5 跳转去重）
5. Phase 6（US3 历史）
6. Phase 7（US6 诊断页）
7. Phase 8（导航优化）
8. Phase 9（测试验证）

### Parallel Opportunities

- T005/T006 与 T001-T004 可并行
- T018-T021 Markdown 渲染 与 T022-T025 跳转去重 可并行
- T043/T044/T045 后端测试 可并行

---

## Notes

- 每个任务完成建议单独提交。
- 涉及数据库模型变更时，由于使用 SQLite 无迁移工具，需要提示用户删除旧 `data/app.db` 或提供迁移脚本。
- 诊断页数据量大时注意分页，避免前端卡顿。
- 配置页保存到 `.env` 后，若未实现热重载，必须提示用户重启后端。
