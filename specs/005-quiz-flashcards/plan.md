# Implementation Plan: 005 - 测验生成与闪卡（第一迭代）

**Branch**: `005-quiz-flashcards` | **Date**: 2026-07-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-quiz-flashcards/spec.md`

## Summary

本 plan 聚焦 **005 第一迭代：测验生成 + 闪卡**（主动学习核心）。对单课程或学习集一键批量生成选择/判断题与闪卡，存库、可判分、三档熟悉度标记、来源可跳回视频。后续迭代（掌握度/错题本/笔记/导出/学伴角色/打卡）在本 plan 仅做架构预留，不实现。

**技术核心**：复用 `RAGEngine._load_course_full_text` 取课程全文（学习集则拼接多课），通过 `create_llm()` 调 LLM 以 JSON 结构化出题/出卡，解析存库。新增 Question、Flashcard 两张表与对应 CRUD/生成接口；前端新增测验与闪卡两个学习面板。

## Technical Context

**Language/Version**: Python 3.11（后端）、TypeScript / Next.js 14（前端）

**Primary Dependencies**: FastAPI、SQLModel、`create_llm()`（已有多模型工厂）、TanStack Query、Tailwind、Radix UI（tabs/card/button/badge/progress）

**Storage**: SQLite（app.db，新增 question、flashcard 表，幂等增量建表）

**Testing**: pytest（后端出题解析/判分/熟悉度逻辑）

**Target Platform**: macOS / Linux，Windows 尽力而为

**Project Type**: Web application（backend + frontend-next）

**Performance Goals**: 单次生成 ≤ 60s（一次 LLM 调用）、出题解析失败可重试、判分即时

**Constraints**: 追加式生成（不覆盖）；选择/判断自动判分；学习集全文拼接需控制上下文长度（超 FULL_TEXT_MAX_CHARS 截断）

**Scale/Scope**: 单用户本地，单范围题库 < 数千题，单集合课程 < 50

## Constitution Check

- ✅ 效果优先，成本可控：一次 LLM 调用批量出题，非逐题调用；选择/判断自动判分零额外 LLM 成本
- ✅ 用户数据本地优先：题库/卡片存本地 SQLite
- ✅ 中文课程优先：出题 prompt 要求中文、贴合课程内容
- ✅ 简洁可维护：复用 `_load_course_full_text`、`create_llm`、学习集展开；出题与判分职责分离
- ✅ 可测试与可演示：US1/US2 可独立测试
- ✅ 渐进式交付：本 plan 只做第一迭代，后续迭代架构预留
- ✅ 入口职责单一：测验/闪卡作为课程/学习集下的学习 Tab，不新增顶层导航

## Project Structure

### Documentation (this feature)

```text
specs/005-quiz-flashcards/
├── spec.md              # Feature specification
├── plan.md              # This file
├── tasks.md             # Implementation tasks
└── checklists/
    └── validation.md    # End-to-end validation checklist
```

### Source Code (repository root)

```text
backend/
├── models.py                # 修改：新增 Question、Flashcard 表
├── schemas.py               # 修改：Question/Flashcard 响应、生成请求、作答/标记请求
├── ai/
│   └── quiz_generator.py    # 新增：从课程全文生成题目/卡片（调 LLM，解析 JSON）
├── services/
│   ├── quiz_service.py      # 新增：测验 CRUD、生成（追加/清空）、判分
│   └── flashcard_service.py # 新增：闪卡 CRUD、生成、三档熟悉度标记与统计
├── api/
│   ├── quiz.py              # 新增：POST 生成、GET 列表、POST 作答判分、DELETE 清空
│   └── flashcards.py        # 新增：POST 生成、GET 列表、PATCH 标记熟悉度、GET 统计、DELETE 清空
└── main.py                  # 修改：挂载 quiz、flashcards 路由

frontend-next/
├── lib/api.ts               # 修改：测验/闪卡接口类型与方法
├── hooks/use-api.ts         # 修改：useQuestions、useGenerateQuiz、useSubmitAnswer、useFlashcards 等
├── components/
│   ├── QuizPanel.tsx        # 新增：测验面板（生成/作答/判分/解析/来源跳转）
│   └── FlashcardPanel.tsx   # 新增：闪卡面板（生成/翻卡/三档标记/统计）
└── app/
    └── courses/[id]/page.tsx        # 修改：学习页新增"测验""闪卡"入口（Tab 或按钮）
    （学习集出题入口复用同一组件，范围参数化）
```

## Implementation Strategy

### Phase 1: 数据模型与出题引擎

- `models.py`：新增 `Question`（id/course_id/study_set_id/type/question/options/answer/explanation/source_timestamp/source_course_id）与 `Flashcard`（id/course_id/study_set_id/front/back/familiarity/source_timestamp/source_course_id）
- `ai/quiz_generator.py`：输入全文文本，构造 prompt 要求 LLM 输出 JSON（题目数组 / 卡片数组），健壮解析（提取首个 JSON 块、容错、重试一次）

### Phase 2: US1 测验生成

- `quiz_service.py`：生成（取全文→出题→存库，追加式）、清空重生成、列表、作答判分（选择/判断比对预设答案）
- `api/quiz.py` + 前端 `QuizPanel.tsx`：生成按钮、答题卡、判分展示、解析、来源跳转

### Phase 3: US2 闪卡

- `flashcard_service.py`：生成、列表、三档熟悉度标记、统计（认识/模糊/不认识计数）
- `api/flashcards.py` + 前端 `FlashcardPanel.tsx`：翻卡、标记、统计、筛选

### Phase 4: 集成与验证

- 课程页加入口；学习集出题复用（范围参数：course_id 或 study_set_id）
- 端到端：生成→作答/翻卡→判分/标记→来源跳转→追加与清空→统计持久化

### Phase 5: 第二迭代续 — 学习增强功能（T022-T028）

- **导出(F)**：`ExportService` 复用 FlashcardService/QuizService 查询，闪卡出 Markdown（按熟悉度分组）/Anki TSV，错题出 Markdown；前端 `downloadExport` 直接触发浏览器下载
- **打卡(H)**：`StudyStatsService` 零侵入聚合 ChatMessage/QuestionAttempt/Note/Flashcard 的 created_at 日期算 streak（含一天宽限），不新增打卡表
- **仪表盘(A)**：`DashboardService` 全局聚合测验正确率/闪卡熟悉度/错题掌握度/笔记/课程数
- **时间段总结(#2)**：`SegmentSummaryService` 按 [start,end] 过滤 Transcript/Frame，LLM 要点总结；复用课程页 videoRef.getCurrentTime 取当前时间
- **图片询问(#6)**：`ChatService` 加 image 分支——视觉模型描述图片 + chat LLM 结合问题回答，不走 RAG、不要求课程已完成；前端 ChatPanel 图片转 base64 data url 上传
- **章节速览(#4)**：`Chapter` 表 + `ChapterService` 按时间窗口分章（3-12 章）、LLM 批量生成标题/速览、首次生成缓存到库；容错 JSON 提取（括号平衡，处理转义/字符串内括号）
- 验证：后端 pytest 109 项全过（新增 38）、前端 tsc 通过、运行中后端真实接口 curl 验证

### Phase 6: 会话制问答 + 学伴增强 + 思维导图/周报（005 收尾）

- **会话制(T029)**：`Conversation` 表 + `ChatMessage.conversation_id`；`ChatService.ask` 续写带最近 6 条历史，RAG `query*` 加 history 参数；旧消息自动迁移成历史会话（reload 自愈清理空会话）；前端会话切换/新建/改名/删除 + 历史页按会话分组
- **图片询问增强(T030)**：ChatPanel 粘贴/拖拽上传 → 视觉描述 + chat LLM 回答
- **可拖动学伴(T031)**：形象作拖动手柄，位置 localStorage 记忆 + 边界限制；收起按钮
- **思维导图(T032)**：`MindMap` 表 + `MindMapService`（LLM 生成树，限深 3 层/宽 6，缓存）；容错 JSON 对象提取；前端 MindMapPanel 递归渲染（缩进 + 连线）
- **学习周报(T033)**：`WeeklyReportService` 聚合最近 7 天（复用 study_dates）；前端 WeeklyReport 统计卡
- 验证：后端 pytest 127 项全过、前端 tsc 通过

## 架构预留（后续迭代，本 plan 不实现）

- Question/Flashcard 已含 `source_timestamp`、`source_course_id`，供学伴/错题本/掌握度复用
- 学伴角色系统（meta.json/素材隔离）与测验判分钩子（答对/答错动作）在第二迭代接入
- 错题本只需按"作答记录的错误题"查询，Question 增加 Attempt 关联即可（第二迭代）
- 数字人形象、画图、网络查询、视频链接导入 → 006

## Complexity Tracking

| 考虑点 | 说明 |
|---|---|
| LLM JSON 输出不稳定 | prompt 强调"只输出 JSON 数组"；解析用正则提取首个 `[...]` 块；失败重试一次，再失败返回错误提示 |
| 范围：课程 or 学习集 | 两表都存 `course_id`（单课时）或 `study_set_id`（学习集时）二选一；学习集生成时把集合内每门课全文拼接，并记录每题 source_course_id |
| 追加 vs 覆盖 | 默认追加；"清空重生成"显式删除该范围旧题后生成 |
| 学习集全文过长 | 拼接时累计字符，超 FULL_TEXT_MAX_CHARS 截断；出题 prompt 要求覆盖多门课 |
| 判分 | 选择/判断纯后端比对，不调 LLM；作答记录可后续供错题本 |

## Notes

- 本迭代不做：掌握度/错题本/笔记/导出/学伴角色/打卡（第二迭代），实时对话/简答/SM-2（006）。
- 新表 create_all 即可，无需 ALTER；若后续给既有表加列再走 `_ADD_COLUMN_MIGRATIONS`。
- 测验/闪卡入口放课程学习页 Tab；学习集出题在全局搜索/学习集处提供入口，范围参数化复用组件。
- 出题数量默认每范围 10-15 题/卡，可在生成接口传参调整。
