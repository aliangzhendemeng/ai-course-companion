# Feature Specification: 003 - 学生体验优化（迭代 1）

**Feature Branch**: `003-student-experience`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "第三版迭代 1：聚焦学生用户基础体验优化，包含前端模型/API 配置页面、课程处理进度条可视化、问答历史统一保存、答案 Markdown 渲染、视频跳转与时间戳去重、课程内容诊断可视化页。"

---

## 用户场景与测试

### User Story 1 - 首次使用引导与模型配置（Priority: P1）

学生第一次打开应用时，无需编辑 `.env` 文件或重启后端，即可在前端完成 API Key 和模型配置，快速开始使用。

**Why this priority**: 当前配置门槛过高，非技术学生无法独立完成。这是所有后续功能的前提。

**Independent Test**: 清空配置后首次打开前端，自动进入引导页；填完 Key 后保存，能正常进入课程库并上传/问答。

**Acceptance Scenarios**:

1. **Given** 用户首次访问应用且未配置 API Key，**When** 打开首页，**Then** 自动跳转到欢迎/配置页，显示默认推荐模型（DeepSeek）。
2. **Given** 用户在配置页，**When** 只填写一个 API Key 并保存，**Then** 系统保存配置并进入主界面，所有模型回退使用该 Key。
3. **Given** 用户在设置页，**When** 修改问答模型为 `gemini:gemini-1.5-pro` 并保存，**Then** 后续问答调用 Gemini API。

---

### User Story 2 - 课程处理进度可视化（Priority: P1）

学生上传课程后，能在课程卡片上实时看到处理百分比和当前阶段，而不是只能看到“处理中”。

**Why this priority**: 大视频处理时间长，用户需要进度反馈，减少焦虑。

**Independent Test**: 上传一个测试视频，课程卡片从 0% 逐渐增加到 100%，每个阶段文字同步更新。

**Acceptance Scenarios**:

1. **Given** 课程正在提取音频，**When** 用户查看课程卡片，**Then** 看到进度条在 0-10% 区间，文字显示“正在提取音频”。
2. **Given** 课程处理到 OCR 阶段，**When** 用户查看课程卡片，**Then** 进度条在 55-80% 区间，文字显示“正在识别课件内容”。
3. **Given** 课程处理完成，**When** 用户查看课程卡片，**Then** 进度条 100%，按钮变为“开始学习”。

---

### User Story 3 - 问答历史统一保存与查看（Priority: P2）

学生在任何页面提问后，都能在统一的“问答历史”页面找到之前的问答记录，包括单课程问答和全局搜索。

**Why this priority**: 学习是持续过程，学生需要回顾之前的问题和答案。

**Independent Test**: 在课程页提问一次，在全局搜索提问一次，打开问答历史页面能看到两条记录。

**Acceptance Scenarios**:

1. **Given** 用户在课程页提问，**When** 问题回答完成，**Then** 该记录保存到历史，包含问题、答案、来源、时间。
2. **Given** 用户在全局搜索提问，**When** 问题回答完成，**Then** 该记录也保存到历史，并标记为“全局搜索”。
3. **Given** 用户打开问答历史页，**When** 页面加载，**Then** 按时间倒序展示所有历史，支持删除单条。

---

### User Story 4 - 答案 Markdown 渲染（Priority: P2）

LLM 返回答案中的加粗、列表、标题等 Markdown 格式能被正确渲染，而不是显示原始 `**` 符号。

**Why this priority**: 答案可读性直接影响学习体验，改动小收益高。

**Independent Test**: 提问一个会触发列表/加粗格式回答的问题，答案区域正确显示格式。

**Acceptance Scenarios**:

1. **Given** 答案包含 `**加粗**`，**When** 渲染到页面，**Then** 显示为加粗文本，不带 `**`。
2. **Given** 答案包含列表，**When** 渲染到页面，**Then** 显示为有序/无序列表。
3. **Given** 答案包含来源引用 `[1]`、`[2]`，**When** 渲染到页面，**Then** 来源 chip 仍可点击跳转。

---

### User Story 5 - 视频跳转与时间戳去重（Priority: P2）

点击答案中的来源 chip，视频自动跳转到对应时间点；如果多个来源时间非常接近，合并显示避免重复 chip。

**Why this priority**: 答案与视频联动是核心学习场景，重复时间戳会让界面混乱。

**Independent Test**: 提问后点击某个来源 chip，视频 seek 到对应时间；同一 PPT 页的多个来源只显示一个 chip。

**Acceptance Scenarios**:

1. **Given** 答案有来源 timestamp=120s，**When** 用户点击该 chip，**Then** 视频播放器 seek 到 2:00。
2. **Given** 两个来源时间差小于 5 秒，**When** 渲染答案来源，**Then** 合并为一个 chip，提示“2 个来源”。
3. **Given** 视频正在播放，**When** 用户点击来源 chip，**Then** 视频从该时间点继续播放，不重新加载。

---

### User Story 6 - 课程内容诊断可视化页（Priority: P2）

学生/开发者能查看课程处理后的原始数据：时间轴上的字幕、OCR 文本、帧图，以及问答时模型拿到的上下文，方便判断是数据问题还是模型问题。

**Why this priority**: 当前处理是黑盒，用户无法判断 ASR/OCR 是否准确、模型为什么找不到答案。

**Independent Test**: 打开诊断页，能看到某课程的字幕时间轴、每帧 OCR 内容和缩略图、某次问答的完整 prompt 和模型返回。

**Acceptance Scenarios**:

1. **Given** 用户进入课程诊断页，**When** 页面加载，**Then** 显示该课程的字幕、OCR、帧图时间轴，时间可点击跳转视频。
2. **Given** 用户在诊断页查看问答 Debug，**When** 选择一次历史问答，**Then** 显示该次问答使用的完整上下文、模型名称、prompt、原始回答。
3. **Given** 用户在诊断页查看总结，**When** 点击“总结”Tab，**Then** 显示大纲、摘要、讲义的原始内容，并支持跳转到对应时间。

---

### Edge Cases

- 用户未配置 API Key 时尝试提问，系统应提示先配置，而不是静默失败。
- 课程处理失败时，进度条应停止在失败阶段，并显示失败原因。
- 历史记录为空时，问答历史页应显示友好空状态。
- 答案中包含 HTML 或脚本时，Markdown 渲染应安全过滤。
- 诊断页帧图过多时，应分页或虚拟滚动，避免页面卡顿。

---

## 需求

### Functional Requirements

- **FR-001**: 系统必须提供前端设置页，允许配置 `CHAT_MODEL`、`CHAT_API_KEY`、`SUMMARY_MODEL`、`SUMMARY_API_KEY`、`VISION_MODEL`、`VISION_API_KEY`、`ENABLE_VISION`。
- **FR-002**: 系统首次启动时必须检测配置状态，未配置则引导用户进入设置页。
- **FR-003**: `Course` 模型必须支持 `progress_percent` 字段，并在处理各阶段更新。
- **FR-004**: 前端课程卡片必须显示处理进度条和当前阶段文字。
- **FR-005**: `ChatMessage` 必须支持保存全局搜索历史（通过 `scope` 字段区分）。
- **FR-006**: 系统必须提供问答历史页面，展示所有单课程和全局搜索记录。
- **FR-007**: 答案文本必须使用 Markdown 渲染，支持加粗、列表、标题等基础格式。
- **FR-008**: 答案来源 chip 点击必须能触发视频 seek 到对应时间戳。
- **FR-009**: 系统必须对相近时间戳（默认 5 秒）的来源进行合并去重。
- **FR-010**: 系统必须提供课程诊断页，展示字幕、OCR、帧图、总结、问答 Debug 信息。
- **FR-011**: 诊断页的问答 Debug 必须显示模型名称、完整上下文、prompt、原始回答。

### Key Entities

- **Course**: 增加 `progress_percent`（整数 0-100），保留现有 `status` 和 `status_message`。
- **ChatMessage**: 增加 `scope` 字段（`course` | `all`），可选 `course_id` 在全局搜索时可空或固定值。
- **Setting/Config**: 新增运行时配置存储（数据库表或写回 `.env`），用于前端读写模型配置。

---

## 成功标准

- **SC-001**: 首次使用的非技术学生能在 2 分钟内完成配置并开始使用。
- **SC-002**: 课程处理过程中，用户能在 5 秒内看到进度变化反馈。
- **SC-003**: 问答历史页面能在 3 秒内加载并正确展示最近 50 条记录。
- **SC-004**: 答案中的 Markdown 符号不再裸露显示，渲染正确率 100%。
- **SC-005**: 点击来源 chip 后，视频在 1 秒内跳转到对应时间。
- **SC-006**: 诊断页能完整展示一门课程的字幕、OCR、帧图和问答 Debug。

---

## 假设

- 学生用户不理解 `.env` 和环境变量，所有配置必须通过 UI 完成。
- 默认推荐模型 DeepSeek 对学生来说成本和效果平衡最佳。
- 诊断页主要面向开发者和高级用户，但学生也能看懂基本的时间轴。
- 进度百分比不需要精确到秒级，阶段式估算即可满足需求。
- 全局搜索历史的 `course_id` 可以用固定值（如 0）或 NULL 表示。
