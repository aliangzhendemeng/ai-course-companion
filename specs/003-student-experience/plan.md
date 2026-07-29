# Implementation Plan: 003 - 学生体验优化（迭代 1）

**Branch**: `003-student-experience` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-student-experience/spec.md`

## Summary

本迭代聚焦学生用户的基础体验优化，不涉及新 AI 能力。核心工作包括：

1. 前端模型/API 配置与首次使用引导
2. 课程处理进度可视化
3. 问答历史统一保存与查看
4. 答案 Markdown 渲染
5. 视频跳转与时间戳去重
6. 课程内容诊断可视化页

所有功能均围绕“降低学生使用门槛”和“提升透明度”展开。

## Technical Context

**Language/Version**: Python 3.11（后端）、TypeScript / Next.js 14（前端）

**Primary Dependencies**: FastAPI、SQLModel、Pydantic、TanStack Query、Tailwind CSS、Radix UI、react-markdown

**Storage**: SQLite（app.db）、本地文件系统（uploads、frames、chroma、bm25）

**Testing**: pytest（后端）、Playwright（前端关键路径）

**Target Platform**: macOS / Linux，Windows 尽力而为

**Project Type**: Web application（backend + frontend-next）

**Performance Goals**: 配置页加载 < 2s、历史页加载 < 3s、答案渲染无闪烁、视频 seek < 1s

**Constraints**: 学生用户不懂命令行和 `.env`；默认配置必须齐全；页面入口职责单一

**Scale/Scope**: 单用户本地部署，课程数 < 1000，单视频时长 < 3 小时

## Constitution Check

- ✅ 效果优先，成本可控：配置页面允许学生选择 cheaper 模型，不强制高级模型
- ✅ 用户数据本地优先：配置可存本地 `.env` 或 SQLite，不强制上传
- ✅ 中文课程优先优化：界面简体中文，Markdown 渲染支持中文
- ✅ 简洁可维护：每个改动职责单一，复用现有组件
- ✅ 可测试与可演示：每个用户故事可独立测试
- ✅ 渐进式交付：按用户故事优先级分阶段实现
- ✅ 符合下一版本边界：不包含桌面 App、任务队列等后期功能

## Project Structure

### Documentation (this feature)

```text
specs/003-student-experience/
├── spec.md              # Feature specification
├── plan.md              # This file
├── tasks.md             # Implementation tasks
└── checklists/
    └── validation.md    # End-to-end validation checklist
```

### Source Code (repository root)

```text
backend/
├── api/
│   ├── settings.py      # 新增：配置读写接口
│   └── chat.py          # 修改：保存 scope 到历史
├── config.py            # 修改：支持运行时读取配置/热加载准备
├── models.py            # 修改：Course.progress_percent, ChatMessage.scope
├── ai/
│   ├── processor.py     # 修改：各阶段更新 progress_percent
│   └── rag_engine.py    # 修改：提供诊断用的上下文和 prompt 信息
└── services/
    ├── settings_service.py  # 新增：配置读写服务
    └── chat_service.py      # 修改：保存全局搜索历史

frontend-next/
├── app/
│   ├── settings/page.tsx        # 新增：模型/API 配置页
│   ├── welcome/page.tsx         # 新增：首次使用引导页
│   ├── history/page.tsx         # 新增：问答历史页
│   ├── courses/[id]/debug/page.tsx  # 新增：课程诊断页
│   └── courses/[id]/page.tsx    # 修改：答案 Markdown 渲染、来源去重跳转
├── components/
│   ├── ChatPanel.tsx            # 修改：Markdown 渲染、来源去重
│   ├── CourseCard.tsx           # 修改：进度条显示
│   └── ui/                      # 复用现有组件
└── lib/api.ts                   # 修改：新增 settings/history/debug 接口
```

## Implementation Strategy

### Phase 1: 共享基础设施

- 数据库模型变更：`Course.progress_percent`、`ChatMessage.scope`
- 后端配置服务：`SettingsService` 读写 `.env`（或 SQLite）
- 前端 API 封装：settings、history、debug 相关接口

### Phase 2: 用户故事实现

按优先级 P1 → P2 顺序实现：

1. US1 首次引导与模型配置
2. US2 课程处理进度条
3. US4 答案 Markdown 渲染（改动小，可提前）
4. US5 视频跳转与时间戳去重
5. US3 问答历史统一保存
6. US6 课程内容诊断页

### Phase 3: 端到端验证

- 清空配置测试首次引导
- 上传测试视频看进度条
- 提问测试 Markdown 和来源跳转
- 全局搜索测试历史保存
- 打开诊断页验证数据展示

## Complexity Tracking

| 考虑点 | 说明 |
|---|---|
| 配置存储选 `.env` 还是 SQLite？ | 先选 `.env` 写回，简单且符合现有约束；为热加载预留 SQLite 方案。 |
| Markdown 渲染安全性 | 使用 `react-markdown` + `remark-gfm`，禁用原始 HTML。 |
| 诊断页大量帧图 | 按时间分页或虚拟滚动，默认每页 20 帧。 |
| 进度百分比估算 | 按阶段固定百分比，不要求精确计算。 |

## Notes

- 本迭代不包含：任务队列、配置热重载、Docker、Vercel、桌面 App，这些放在 003-2。
- 所有新页面必须走 SSR 或服务端预取，避免 hydration 闪跳问题重演。
- 配置页保存后提示用户“需要重启后端生效”（如果仍用 `.env` 写回方案）。
