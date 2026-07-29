# Tasks: 004 - 多课程学习集与使用门槛优化

**Input**: Design documents from `/specs/004-multi-course-sets/`

**Prerequisites**: spec.md, plan.md

> 本版核心为 **US1 多课程学习集（P1）**。US2 一键启动、US3 设置页完善、US4 桌面 App 为延续项，按进度裁剪。

## Phase 1: 共享基础设施

**Purpose**: 数据模型、学习集服务、前端 API 封装

- [ ] T001 修改 `backend/models.py`：新增 `StudySet(id, name, created_at)` 与 `StudySetCourse(set_id, course_id)` 多对多关联表
- [ ] T002 新建 `backend/services/study_set_service.py`：学习集 CRUD + 展开 `course_ids`（仅保留 status=completed 课程）+ 校验
- [ ] T003 修改 `backend/schemas.py`：新增 `StudySetCreate`、`StudySetUpdate`、`StudySetItem`；`ChatRequest` 增加可选 `course_ids: list[int]`
- [ ] T004 [P] 修改 `frontend-next/lib/api.ts`：新增学习集 CRUD 接口；`askQuestion` 支持 `courseIds`
- [ ] T005 [P] 修改 `frontend-next/hooks/use-api.ts`：新增 `useStudySets`、`useCreateStudySet`、`useUpdateStudySet`、`useDeleteStudySet`
- [ ] T006 提供增量建表：确认 `create_db_and_tables` 能为既有库新增 StudySet 表（不删旧数据），否则提供说明

**Checkpoint**: 基础设施 ready，US1 可开始

---

## Phase 2: User Story 1 - 多课程学习集（Priority: P1）⭐ 核心

**Goal**: 学生把若干门已完成课程保存为命名学习集，只针对该集合提问

**Independent Test**: 建学习集"数学"勾选 2 门课，提问后答案与来源只来自这 2 门，来源可跳转

### 后端检索与回答

- [ ] T007 修改 `backend/ai/rag_engine.py`：`_retrieve` 增加可选 `course_filter: list[int]`，向量检索用 `where={"course_id":{"$in":course_filter}}`；BM25 候选在应用层按 course_id 过滤后再 RRF 融合
- [ ] T008 修改 `backend/ai/rag_engine.py`：新增 `query_multiple(course_ids, question)`——过滤检索定位相关课，拼接这些课的完整文本（复用 `query_all` 多课拼接与上下文长度控制），来源带课程名+真实时间戳
- [ ] T009 修改 `backend/services/chat_service.py`：`ask` 支持 `course_ids`，非空时路由 `query_multiple`，保存 `scope="set"`
- [ ] T010 修改 `backend/api/chat.py`：`/{course_id}` 问答接口透传 `course_ids`

### 学习集接口

- [ ] T011 新建 `backend/api/study_sets.py`：`GET /api/study-sets`（列表）、`POST`（新建）、`PATCH /{id}`（重命名/增删课程）、`DELETE /{id}`
- [ ] T012 修改 `backend/main.py`：挂载 study_sets 路由

### 前端

- [ ] T013 新建 `frontend-next/components/StudySetPicker.tsx`：学习集/课程多选弹层（checkbox 列出已完成课程 + 新建集合 + 选择已有集合）
- [ ] T014 新建 `frontend-next/components/StudySetManager.tsx`：学习集管理（重命名/增删课程/删除）
- [ ] T015 修改 `frontend-next/components/ChatPanel.tsx`：scope 扩展为 `"course" | "all" | "set"`，set 模式接入 StudySetPicker 并携带 course_ids
- [ ] T016 修改 `frontend-next/app/chat/ChatPageClient.tsx`：全局搜索页支持学习集范围
- [ ] T017 修改 `frontend-next/app/courses/[id]/page.tsx`：课程页 ChatPanel 支持切到学习集范围；来源 chip 跨课程跳转正确

**Checkpoint**: US1 可独立演示

---

## Phase 3: User Story 2 - 一键启动脚本（Priority: P1）

**Goal**: 双击脚本同时启动前后端、自动开浏览器、退出一起关

**Independent Test**: 干净终端运行 `start_app.sh`，浏览器自动打开可用界面；Ctrl+C 后两进程都退出

- [ ] T018 新建 `start_app.sh`：同时启动后端+前端、自动打开浏览器、trap 退出清理子进程、端口占用友好提示
- [ ] T019 新建 `start_app.bat`（Windows 尽力而为）或 `launcher.py` 跨平台版

**Checkpoint**: US2 可独立演示

---

## Phase 4: User Story 3 - 设置页完善（Priority: P2）

**Goal**: 首次引导、保存后生效提示、默认值与 Key 回退收尾

- [ ] T020 完善 `frontend-next/app/welcome/page.tsx`：首次未配置自动进入引导
- [ ] T021 设置页保存后提示"需重启后端生效"（若仍 `.env` 写回）

**Checkpoint**: US3 可独立演示

---

## Phase 5: 测试与验证

- [ ] T022 [P] 后端单元测试：`StudySetService` CRUD 与 course_ids 展开（含课程缺失降级）
- [ ] T023 [P] 后端单元测试：`query_multiple` 只检索指定课程范围
- [ ] T024 端到端验证：按 checklists/validation.md 跑一遍（建集合→提问→来源范围与跳转→降级）

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1（基础设施）必须先完成
- Phase 2（US1 学习集）为本版核心，优先交付
- Phase 3/4（US2/US3）可在 US1 后并行或裁剪
- Phase 5（测试）在最后

### 推荐执行顺序

1. Phase 1（基础设施）
2. Phase 2（US1 学习集）⭐
3. Phase 3（US2 一键启动）
4. Phase 4（US3 设置页完善）
5. Phase 5（测试验证）

### Parallel Opportunities

- T004/T005（前端 API）与 T001-T003（后端模型/schema）可并行
- T013/T014（前端组件）与 T007-T010（后端检索）可并行

---

## Notes

- 每个任务完成建议单独提交。
- SQLite 无迁移工具：新增 StudySet 表后确认 `create_all` 增量建表，避免删库丢数据。
- 学习集不新增独立导航页，管理入口放 ChatPanel 弹层内，符合"入口职责单一"。
- 多课程全文拼接复用 `query_all` 的"限前 N 门 + 全长上限"策略，超限回退片段检索。
- US4 桌面 App 不在本次实现范围，视进度延后。
