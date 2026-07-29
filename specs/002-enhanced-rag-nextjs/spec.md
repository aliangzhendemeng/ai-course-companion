# Feature Specification: AI 慕课学伴下一版本增强

**Feature Branch**: `002-enhanced-rag-nextjs`

**Created**: 2026-07-24

**Status**: Draft

**Input**: User description: "在现有 AI 慕课学伴基础上，实现混合检索（向量+BM25）、全局跨课程搜索、帧处理加速、视频播放流式修复、多模型配置，并新增基于 Next.js 的现代前端，同时保留 Streamlit 作为托底。"

---

## User Scenarios & Testing（必填）

### User Story 1 - 多模型配置与视频流式播放（Priority: P1）

学习者希望为总结、问答、视觉理解分别配置最合适的模型，并在课程学习页流畅播放视频，而不是直接访问服务器本地路径。

**Why this priority**: 这是后续所有功能的基础。多模型配置让系统在不同任务上取得成本与效果平衡；视频流式修复解决当前浏览器无法直接播放本地路径的问题，是学习体验的基本保障。

**Independent Test**: 配置不同的 SUMMARY_MODEL、CHAT_MODEL、VISION_MODEL 后，系统能正常调用对应模型完成总结和问答；在课程学习页点击视频能正常加载、拖动进度条，且后端返回 206 Partial Content。

**Acceptance Scenarios**:

1. **Given** 用户在 `.env` 中配置了 `SUMMARY_MODEL=deepseek`、`CHAT_MODEL=deepseek`、`VISION_MODEL=deepseek` 及对应 API Key，**When** 系统处理课程并回答问题时，**Then** 总结、聊天、视觉理解分别使用各自配置的模型与 Key。
2. **Given** 用户只配置了旧的 `LLM_MODEL` 和 `VISION_MODEL`，**When** 系统读取配置时，**Then** 新配置项自动回退到旧配置，保持向后兼容。
3. **Given** 用户进入课程学习页面，**When** 页面加载视频，**Then** 视频通过 `/api/courses/{id}/video` 流式加载，支持进度跳转，不再直接暴露本地文件路径。
4. **Given** 后端收到带 `Range` 头的视频请求，**When** 返回响应时，**Then** 返回 206 状态码和正确的 `Content-Range`。

---

### User Story 2 - 帧处理加速（Priority: P2）

学习者上传 45 分钟课程后，不希望等待 10-20 分钟才能完成处理，希望系统更快地产出总结和问答。

**Why this priority**: 处理速度直接影响首次使用体验。通过智能视觉调用、并行 API 和场景变化抽帧，可在不明显牺牲质量的前提下大幅缩短处理时间。

**Independent Test**: 上传测试视频，记录处理耗时，确认帧处理阶段耗时明显低于原有串行方案；同时确认复杂画面仍被视觉模型理解。

**Acceptance Scenarios**:

1. **Given** 系统抽取关键帧后，**When** 对每帧做 OCR 与复杂度判断，**Then** 只有包含图表/公式/代码/复杂画面的帧才会调用付费视觉 API，纯文字 PPT 帧仅使用 OCR。
2. **Given** 存在多个需要视觉理解的帧，**When** 系统调用视觉 API 时，**Then** 使用 `ThreadPoolExecutor` 并发执行（默认 4 并发，可配置）。
3. **Given** 视频画面长时间保持不变，**When** 系统抽帧时，**Then** 基于 OpenCV 场景变化检测避免重复帧，同时保留均匀抽帧作为 fallback。
4. **Given** 某个视觉 API 调用失败，**When** 系统处理该帧时，**Then** 降级为 OCR 文本，不中断整个课程处理流程。

---

### User Story 3 - 混合检索与全局跨课程搜索（Priority: P2）

学习者在多门课程中学习后，希望能够跨课程统一搜索知识，并且检索结果兼顾语义相关与精确关键词匹配。

**Why this priority**: 混合检索提升 RAG 问答质量，全局搜索解锁“在所有已学课程中提问”的高阶场景，是产品从“单课助手”迈向“学习知识库”的关键。

**Independent Test**: 上传两门以上课程并提问，分别验证单课搜索与全局搜索都能返回相关结果；用精确关键词提问时，混合检索能召回向量检索遗漏的内容。

**Acceptance Scenarios**:

1. **Given** 用户提问用词与视频原文不完全一致，**When** 系统检索时，**Then** 向量检索召回语义相关片段。
2. **Given** 用户提问包含课程中的精确术语，**When** 系统检索时，**Then** BM25 稀疏检索召回包含该术语的片段。
3. **Given** 系统同时执行向量检索与 BM25 检索，**When** 合并结果时，**Then** 使用 RRF（Reciprocal Rank Fusion）融合，最终返回 Top-K 文档。
4. **Given** 用户在问答页选择“全部课程”搜索范围，**When** 提交问题时，**Then** 系统在全局 collection 中检索，并返回每个来源所属的课程 ID 与标题。
5. **Given** 用户删除一门课程，**When** 系统删除课程数据时，**Then** 同步清理该课程在全局 collection 和全局 BM25 索引中的文档。

---

### User Story 4 - 现代 React 前端（Priority: P3）

学习者希望使用更现代、更美观、交互更流畅的 Web 界面来管理课程、学习视频和进行知识问答。

**Why this priority**: Streamlit 适合快速验证，但难以提供精致的 AI 产品体验。新增 Next.js 前端可显著提升品牌感，同时保留 Streamlit 作为故障回退。

**Independent Test**: 启动 Next.js 前端，完成上传视频、查看课程列表、播放视频、查看三级总结、提问并查看来源卡片、切换全局搜索等完整流程。

**Acceptance Scenarios**:

1. **Given** 用户启动 Next.js 开发服务器，**When** 访问课程库页面时，**Then** 看到卡片式课程列表，包含状态标签与操作按钮。
2. **Given** 用户点击课程卡片，**When** 进入课程学习页时，**Then** 左侧播放视频，右侧展示大纲/摘要/讲义，点击时间戳可跳转。
3. **Given** 用户进入知识问答页，**When** 选择搜索范围并提问时，**Then** AI 回答以聊天流式呈现，下方显示可点击的来源卡片。
4. **Given** Next.js 前端因某种原因不可用，**When** 用户切换回 Streamlit 前端时，**Then** Streamlit 仍能完整使用所有后端功能。

---

### Edge Cases

- 当 `.env` 中同时存在新旧模型配置且冲突时，以新配置项为准，旧配置仅作为 fallback。
- 当视频文件损坏或无法打开时，处理流程应标记为 `failed` 并返回可读错误信息。
- 当 BM25 索引文件损坏或缺失时，系统应自动重建该课程的 BM25 索引，而不是直接报错。
- 当全局 collection 中某课程文档删除失败时，应记录日志并继续，不阻塞课程删除主流程。
- 当并发视觉 API 触发限流时，应自动退避重试，或暂时降级为 OCR。
- 当用户选择“全部课程”但系统中只有一门课程时，全局搜索应等价于单课搜索。
- 当 Next.js 前端请求视频流时，CORS 和 Range 头必须正确处理，否则播放器无法 seek。

---

## Requirements（必填）

### Functional Requirements

- **FR-001**: 系统必须支持为总结、聊天、视觉理解分别配置模型名称与 API Key。
- **FR-002**: 系统必须向后兼容旧的 `LLM_MODEL` 和 `VISION_MODEL` 配置。
- **FR-003**: 后端必须新增 `/api/courses/{course_id}/video` 接口，支持流式返回视频并正确处理 `Range` 请求。
- **FR-004**: `CourseDetail` 响应必须返回可访问的 `video_url`，不再直接暴露本地文件路径。
- **FR-005**: 系统必须支持基于 OpenCV 的场景变化检测抽帧，并保留均匀抽帧作为 fallback。
- **FR-006**: 系统必须先对所有帧做 OCR，再基于规则判断是否需要调用视觉 API。
- **FR-007**: 系统必须对需要视觉理解的帧使用 `ThreadPoolExecutor` 并发调用，并发数可配置。
- **FR-008**: 系统必须在 RAG 中引入 BM25 稀疏检索，并与向量检索结果通过 RRF 融合。
- **FR-009**: 系统必须维护一个 `global_courses` 向量 collection 和对应的全局 BM25 索引，支持跨课程搜索。
- **FR-010**: 问答接口必须支持 `scope` 参数，值为 `course` 或 `all`。
- **FR-011**: 删除课程时必须同步清理该课程在全局 collection 和全局 BM25 索引中的文档。
- **FR-012**: 必须新增基于 Next.js + TypeScript + Tailwind + shadcn/ui 的前端，保留现有 Streamlit 前端作为托底。
- **FR-013**: Next.js 前端必须与现有后端 API 兼容，不强制修改后端核心数据结构。
- **FR-014**: 新增功能必须同步更新 `.env.example`、`README.md` 和相关规格文档。

### Key Entities

- **Course（课程）**: 现有模型，新增 `video_url` 仅在响应层暴露，数据库仍存 `video_path`。
- **Frame（关键帧）**: 现有模型，新增复杂度评估中间结果不持久化，仅用于决定是否调用 VLM。
- **RAGDocument（RAG 文档）**: 由 transcript/ocr_text/vision_desc 生成的 Document，新增稳定 `doc_id`。
- **GlobalIndex（全局索引）**: 由 `global_courses` Chroma collection 与 `global.bm25` 索引组成，metadata 含 `course_id`。
- **ChatMessage（问答消息）**: 现有模型，全局搜索下的历史仍按课程保存，`scope` 仅在 API 层传递。
- **ModelConfig（模型配置）**: 配置层面的抽象，包含 provider、model_name、api_key、base_url 等。

---

## Success Criteria（必填）

### Measurable Outcomes

- **SC-001**: 45 分钟课程的处理时间从当前的 10-20 分钟降低到 5 分钟以内（外部 API 视觉调用场景下）。
- **SC-002**: 在包含精确关键词的问答测试中，混合检索召回率比纯向量检索提升至少 20%。
- **SC-003**: 全局跨课程搜索能正确返回至少两个不同课程的来源。
- **SC-004**: 视频流式接口能支持 HTML5 播放器正常 seek，206 响应率达到 100%。
- **SC-005**: Next.js 前端能完整跑通上传 → 处理 → 学习 → 问答 → 全局搜索流程。
- **SC-006**: 所有新增后端功能在 Streamlit 前端中保持可用，确保托底方案有效。
- **SC-007**: 核心模块单元测试覆盖率不低于 70%。

---

## Assumptions

- 用户仍主要为单用户本地使用，多用户并发不是本版本重点。
- 用户已具备 Node.js 环境，能够运行 Next.js 开发服务器。
- 外部模型 API（DeepSeek/Gemini/Claude）至少有一个可用。
- 本地 OCR 和 ASR 环境与现有版本保持一致。
- 全局搜索暂不做权限隔离，所有课程对当前用户可见。
- 知识图谱作为三期方向，本期仅通过全局 collection 支持跨课程检索。
- 设计系统参考 `design-system/MASTER.md`，Next.js 前端基于此落地。
