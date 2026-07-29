# Implementation Plan: 004 - 多课程学习集与使用门槛优化

**Branch**: `004-multi-course-sets` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-multi-course-sets/spec.md`

## Summary

本版核心新需求是**多课程学习集（US1，P1）**：让学生把若干门已完成课程保存为命名集合（如"数学必修"），之后只针对该集合提问，介于"单课程"与"全部课程"之间。技术本质是给现有全局检索加课程过滤——所有课程已索引在全局向量库且文档 metadata 带 `course_id`，`query_all` 已实现跨课程检索与多课全文拼接，因此只需：

1. 新增 `StudySet` 持久化（学习集 ↔ 课程 多对多）
2. `RAGEngine` 检索支持 `course_id` 过滤，新增 `query_multiple(course_ids, question)`
3. 前端 ChatPanel 增加"选择课程/学习集"档位与学习集管理界面

其余为用户体验延续项：一键启动脚本（US2，P1）、设置页完善（US3，P2）、桌面 App（US4，P3，可裁剪）。**本迭代优先交付 US1。**

## Technical Context

**Language/Version**: Python 3.11（后端）、TypeScript / Next.js 14（前端）

**Primary Dependencies**: FastAPI、SQLModel、Chroma 0.5.0（支持 `where={"course_id":{"$in":[...]}}` 过滤）、TanStack Query、Tailwind、Radix UI

**Storage**: SQLite（app.db，新增 StudySet 相关表）、本地文件系统（chroma/bm25 全局索引已有 course_id metadata）

**Testing**: pytest（后端）、Playwright（前端关键路径）

**Target Platform**: macOS / Linux，Windows 尽力而为

**Project Type**: Web application（backend + frontend-next）

**Performance Goals**: 多课程问答 < 30s（受 LLM 限制）、学习集列表加载 < 1s、来源跳转 < 1s

**Constraints**: 学习集为单用户本地，无权限隔离；多课程全文拼接需控制上下文长度，超限回退片段检索

**Scale/Scope**: 单用户本地部署，学习集 < 100，单集合课程数 < 50

## Constitution Check

- ✅ 效果优先，成本可控：复用现有全局索引，不新增 embedding 成本；多课拼接限制课程数防爆上下文
- ✅ 用户数据本地优先：学习集存本地 SQLite
- ✅ 中文课程优先优化：界面简体中文
- ✅ 简洁可维护：`query_multiple` 复用 `query_all` 拼接逻辑；检索层只加一个过滤参数
- ✅ 可测试与可演示：US1 可独立测试（建集合→提问→验证来源范围）
- ✅ 渐进式交付：US1（学习集）优先，US2/US3/US4 后续
- ✅ 入口职责单一：学习集是"问答范围"的扩展，不新增独立导航入口，复用现有 ChatPanel

## Project Structure

### Documentation (this feature)

```text
specs/004-multi-course-sets/
├── spec.md              # Feature specification
├── plan.md              # This file
├── tasks.md             # Implementation tasks (/speckit-tasks output)
└── checklists/
    └── validation.md    # End-to-end validation checklist
```

### Source Code (repository root)

```text
backend/
├── models.py                # 修改：新增 StudySet、StudySetCourse（多对多关联）
├── schemas.py               # 修改：StudySetCreate/StudySetItem；ChatRequest 增加 course_ids
├── api/
│   ├── study_sets.py        # 新增：学习集 CRUD（GET/POST/PATCH/DELETE /api/study-sets）
│   └── chat.py              # 修改：支持 course_ids 路由到多课程问答
├── services/
│   ├── study_set_service.py # 新增：学习集持久化与展开 course_ids
│   └── chat_service.py      # 修改：ask 支持 course_ids，保存 scope="set"
├── ai/
│   └── rag_engine.py        # 修改：_retrieve 增加 course_filter；新增 query_multiple()
└── main.py                  # 修改：挂载 study_sets 路由

frontend-next/
├── lib/api.ts               # 修改：学习集 CRUD 接口；askQuestion 支持 courseIds
├── hooks/use-api.ts         # 修改：useStudySets、useCreateStudySet 等
├── components/
│   ├── ChatPanel.tsx        # 修改：scope 增加 "set"，接入学习集选择器
│   ├── StudySetPicker.tsx   # 新增：学习集/课程多选弹层（checkbox 列表 + 新建集合）
│   └── StudySetManager.tsx  # 新增：学习集管理（重命名/增删课程/删除）
└── app/
    ├── chat/ChatPageClient.tsx      # 修改：全局搜索页支持学习集范围
    └── courses/[id]/page.tsx        # 修改：课程页 ChatPanel 支持切到学习集范围
```

## Implementation Strategy

### Phase 1: 共享基础设施

- 数据模型：新增 `StudySet(id, name, created_at)` + `StudySetCourse(set_id, course_id)` 关联表（SQLite 无迁移，提示删库或新建表）
- 后端服务：`StudySetService` 负责 CRUD 与"学习集 → course_ids"展开；校验课程存在且已完成
- 前端 API 封装：学习集 CRUD + `askQuestion` 支持 `courseIds`

### Phase 2: US1 多课程学习集（核心）

1. **检索层**：`_retrieve` 增加可选 `course_filter: list[int]`，向量检索用 `where={"course_id":{"$in":course_filter}}`；BM25 结果按 course_id 过滤
2. **回答层**：新增 `query_multiple(course_ids, question)`——过滤检索定位相关课，拼接这些课的完整文本（复用 `query_all` 的多课拼接与上下文长度控制），来源带课程名+时间戳
3. **服务/接口**：`chat_service.ask` 支持 `course_ids`；`/api/chat/{course_id}` 透传
4. **前端**：ChatPanel scope 增加 "set"；StudySetPicker 选择/新建集合；来源可跳转

### Phase 3: US2 一键启动脚本（后续）

- `start_app.sh` / `start_app.bat`：同时启动前后端、自动开浏览器、退出一起关、端口占用友好提示

### Phase 4: US3 设置页完善（后续）

- 首次引导、保存后生效提示、默认值与 Key 回退收尾

### Phase 5: 端到端验证

- 建学习集"数学"→勾选 2 门课→提问→验证答案与来源只来自这 2 门→来源可跳转
- 集合内课程删除/重处理后提问不报错

## Complexity Tracking

| 考虑点 | 说明 |
|---|---|
| 学习集与课程关联建模 | 多对多，用关联表 `StudySetCourse`；课程删除时级联清理关联，学习集保留 |
| 多课程全文拼接上下文爆炸 | 复用 `query_all` 的"限前 N 门课 + 全长上限"策略，超限回退片段检索 |
| BM25 索引不支持 metadata 过滤 | 检索后在应用层按 `course_id` 过滤 BM25 候选，再 RRF 融合 |
| 学习集内课程被删/重处理 | 展开 course_ids 时只保留 status=completed 的课程；为空时提示"集合内暂无可用课程" |
| ChatPanel 三处复用 | scope 扩展为 `"course" \| "all" \| "set"`，set 模式需携带选中的 course_ids；用 React state 上提到页面 |

## Notes

- 本迭代优先 US1；US2/US3/US4 视进度裁剪，US4（桌面 App）大概率延后到下版。
- SQLite 无迁移工具：新增表后需提示用户删除旧 `data/app.db` 或提供 `create_all` 增量建表脚本（不影响既有表）。
- 全局搜索页与课程页共用 ChatPanel，学习集选择状态建议上提到页面层，避免两页状态不一致。
- 学习集是"问答范围"维度，不作为独立导航页，避免与"入口职责单一"冲突；管理入口放在 ChatPanel 弹层内。
