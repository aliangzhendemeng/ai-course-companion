# Research: AI 慕课学伴技术选型

**研究目标**: 为 AI 慕课学伴项目选择合适的技术栈，确保在效果、成本、可维护性和可扩展性之间取得平衡。

**研究范围**: 本地视频上传后的多模态处理链路，包括音频转写、关键帧抽取、OCR、视觉理解、总结生成、RAG 问答和用户界面。

**日期**: 2026-07-23

---

## 一、核心问题

技术类慕课中，大量关键信息（图表、公式、代码、PPT 重点）仅存在于视频画面中。纯音频转写只能覆盖约 60% 内容。因此系统必须同时处理音频和画面，才能生成完整的课程总结并支持精准问答。

本项目需要回答以下技术问题：

1. 如何在本地或低成本前提下，准确提取视频中的中文语音和文字？
2. 如何理解视频画面中的图表、公式、代码等非文字内容？
3. 如何将音频、文字、画面信息融合成结构化的三级总结？
4. 如何实现基于课程内容的问答，并准确定位到视频时间戳和画面？
5. 如何设计前端界面，让用户能自然地上传、学习、提问？

---

## 二、候选方案对比

### 2.1 OCR（光学字符识别）

| 方案 | 中文准确率 | 成本 | 速度 | 隐私 | 离线可用 | 评估 |
|---|---|---|---|---|---|---|
| PaddleOCR | 85% | 免费 | 快 | 本地 | 是 | 中文效果最佳，社区活跃，推荐 |
| EasyOCR | 82% | 免费 | 中等 | 本地 | 是 | 效果略逊于 PaddleOCR |
| pytesseract | 70% | 免费 | 快 | 本地 | 是 | 中文效果差，不推荐 |
| Azure OCR | 92% | 付费 | 快 | 上传 | 否 | 准确率高但成本增加约 7 倍 |
| Google Vision | 93% | 付费 | 快 | 上传 | 否 | 效果与 Azure 相近，更贵 |

**结论**: 选择 **PaddleOCR**。原因：中文识别效果好、完全免费、本地运行保护隐私、速度快且支持 GPU 加速。

---

### 2.2 ASR（自动语音识别）

| 方案 | 中文准确率 | 成本 | 速度 | 离线可用 | 评估 |
|---|---|---|---|---|---|
| faster-whisper | 85-90% | 免费 | 中等 | 是 | 本地运行，效果足够，推荐 |
| Whisper.cpp | 85-90% | 免费 | 快 | 是 | 对 C++ 构建依赖较重 |
| OpenAI Whisper API | 90%+ | 付费 | 快 | 否 | 准确率高但成本累积 |
| 讯飞/百度语音识别 | 85-90% | 付费 | 快 | 否 | 国内可用，但增加集成复杂度 |

**结论**: 选择 **faster-whisper**。原因：本地运行零成本、对中文支持良好、与 Python 生态集成简单。

---

### 2.3 视觉理解（画面内容描述）

| 方案 | 效果 | 单帧成本 | 月度成本（10 课） | 速度 | 访问 | 评估 |
|---|---|---|---|---|---|---|
| Gemini Pro Vision | 92% | 免费 | ￥0 | 快 | 需翻墙 | 免费额度大，效果最好之一 |
| DeepSeek-VL | 90% | 约 ￥0.035 | 约 ￥40 | 快 | 国内直连 | 稳定、中文好、性价比高 |
| Claude 3.5 Sonnet | 95% | 约 ￥0.07 | 约 ￥80 | 中等 | 需翻墙 | 效果最好，细节捕捉最强 |
| GPT-4V | 90% | 约 ￥0.07 | 约 ￥80 | 慢 | 需翻墙 | 贵且慢，效果不突出 |
| Qwen-VL | 80% | 免费/低价 | ￥0-20 | 中等 | 国内 | 效果较弱，不推荐 |
| 本地 VLM（Qwen2-VL / InternVL2 / LLaVA） | 75-85% | 免费（硬件成本） | ￥0 | 慢 | 本地 | 完全离线，隐私最好，但需要 GPU |

**结论**: MVP 选择 **DeepSeek-VL**。原因：用户当前已有 DeepSeek Key、国内直连稳定、中文理解好、成本可控。

**可扩展性**: 视觉模型通过统一接口封装，后续可通过配置切换为 Gemini、Claude 或本地 VLM，无需改动业务逻辑。

**托底机制**: 当外部视觉模型不可用时，系统降级为仅使用 PaddleOCR 提取画面文字，保证基础处理能力不中断。同时预留本地 VLM 接口，供有硬件条件的用户完全离线运行。

---

### 2.4 大语言模型（LLM）

| 方案 | 中文效果 | 成本 | 速度 | 访问 | 评估 |
|---|---|---|---|---|---|
| DeepSeek Chat | 强 | 低（约 ￥7/百万 token） | 快 | 国内直连 | 便宜、中文好，推荐 |
| Claude 3.5 Sonnet | 很强 | 中 | 中等 | 需翻墙 | 逻辑和代码理解更强，但贵 |
| GPT-4o | 强 | 高 | 中等 | 需翻墙 | 通用能力强，成本高 |
| Gemini Pro | 强 | 免费/低价 | 快 | 需翻墙 | 可配合 Gemini Vision 使用 |

**结论**: 选择 **DeepSeek Chat** 作为主力 LLM。原因：成本低、中文表现好、国内访问稳定。复杂推理场景可后续切换到 Claude。

---

### 2.5 向量库与嵌入模型

| 方案 | 特点 | 成本 | 评估 |
|---|---|---|---|
| Chroma | 本地向量库，易用 | 免费 | 适合 MVP，推荐 |
| FAISS | 高性能本地索引 | 免费 | 性能好但 API 较底层 |
| Milvus | 分布式向量数据库 | 部署成本高 | 不适合单用户本地场景 |
| Pinecone | 托管服务 | 付费 | 增加外部依赖 |

**结论**: 选择 **Chroma**。原因：零成本、API 简单、与 LangChain 集成好、本地持久化方便。

**嵌入模型**: 选择中文语义效果较好的 sentence-transformers 模型（如 `BAAI/bge-base-zh-v1.5` 或 `paraphrase-multilingual-MiniLM-L12-v2`），对中文课程文本和画面描述进行向量化。

---

### 2.6 前端界面

| 方案 | 开发速度 | 自定义能力 | 多媒体支持 | 部署复杂度 | 评估 |
|---|---|---|---|---|---|
| Streamlit | 很快 | 中等 | 好 | 低 | 最适合快速 Demo，推荐 |
| Gradio | 快 | 中等 | 好 | 低 | 也可选，但生态小于 Streamlit |
| Next.js + React | 中等 | 强 | 强 | 高 | 体验好但工作量大 |
| Vue 3 ESM | 中等 | 强 | 强 | 中 | 需要前端工程能力 |

**结论**: 选择 **Streamlit**。原因：MVP 阶段需要快速验证核心流程，Streamlit 能用纯 Python 完成上传、播放、问答三页面，部署简单。

---

### 2.7 后端框架

| 方案 | 特点 | 评估 |
|---|---|---|
| FastAPI | 现代、异步、类型友好、生态丰富 | 推荐 |
| Flask | 简单、成熟 | 也可以，但异步支持弱 |
| Django | 重型、功能全 | 不适合轻量 MVP |

**结论**: 选择 **FastAPI**。原因：天然支持异步处理、类型安全、与 AI/ML 工具链集成好。

---

## 三、最终技术栈

| 模块 | 选型 | 说明 |
|---|---|---|
| 后端框架 | FastAPI | 异步 API 服务 |
| 前端界面 | Streamlit | 快速 Demo 与交互 |
| ASR | faster-whisper | 本地中文语音识别 |
| OCR | PaddleOCR | 本地中文文字识别 |
| 视觉理解 | DeepSeek-VL | 画面内容描述（可配置切换） |
| LLM | DeepSeek Chat | 总结与问答（可配置切换） |
| 向量库 | Chroma | 本地语义检索 |
| 嵌入模型 | sentence-transformers | 中文语义向量 |
| 数据库 | SQLite | 课程元信息、字幕、帧、总结、问答历史 |
| 任务队列 | asyncio | MVP 阶段本地异步处理 |

---

## 四、关键参数决策

| 参数 | 取值 | 理由 |
|---|---|---|
| 抽帧策略 | 均匀采样 | 简单可靠，适合 PPT 切换较慢的慕课 |
| 单课程最大帧数 | 120 | 40 分钟课程约每 20 秒一帧，平衡效果与成本 |
| OCR 置信度阈值 | 0.6 | 过滤低质量识别结果，保留可用文字 |
| RAG 检索 top-k | 5 | 兼顾准确率与回答长度 |
| 字幕切块长度 | 300-500 字符 | 保留上下文，便于时间戳定位 |
| 视觉描述 token 上限 | 500 | 控制单帧 API 成本 |

---

## 五、风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| DeepSeek-VL 模型名或 API 格式变化 | 高 | 封装统一视觉分析接口，配置化切换模型 |
| 外部视觉模型不可用 | 中 | 降级为纯 OCR 处理；预留本地 VLM 接口，支持完全离线运行 |
| faster-whisper 在 CPU 上处理慢 | 中 | 接受 40 分钟视频 1-2 小时处理时间；后续可改用 GPU 或 Whisper API |
| PaddleOCR 安装依赖复杂 | 中 | 提供详细安装脚本和 Docker 备选方案 |
| 长视频上下文超过 LLM 窗口 | 中 | 采用三级总结策略，分段处理后再聚合 |
| 画面信息被视觉模型遗漏 | 中 | OCR 与视觉描述互补，提高覆盖率 |
| API 限流或失败 | 中 | 实现重试机制和失败状态，允许用户重跑 |

---

## 六、假设与依赖

- 用户能够本地安装 ffmpeg、Python 3.10+ 等基础依赖。
- 用户持有有效的 DeepSeek API Key。
- 上传视频分辨率足够，OCR 和视觉模型能识别画面内容。
- 课程以中文讲解为主，中英混合内容也能处理。
- MVP 为单用户本地使用，不考虑并发和云端部署。
- 视觉模型和 LLM 通过统一接口封装，未来切换成本可控。
- 当外部视觉模型不可用时，系统可降级为纯 OCR 处理，并预留本地 VLM 扩展接口。

---

## 七、可复用开源工具（二期扩展预留）

以下工具在 MVP 阶段不实现，但已有成熟开源方案可供二期直接集成：

| 模块 | 工具 | 用途 | 接入阶段 |
|---|---|---|---|
| 视频下载 | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube/B 站等 URL 视频下载 | 二期 |
| 视频下载 | [you-get](https://github.com/soimort/you-get) | 国内视频网站下载 | 二期 |
| ASR 增强 | [whisperx](https://github.com/m-bain/whisperX) | 语音转写 + 说话人分离 + 词级时间戳 | 二期 |
| ASR 增强 | [funasr](https://github.com/modelscope/FunASR) | 阿里中文语音识别，标点效果强 | 二期 |
| 公式识别 | [nougat](https://github.com/facebookresearch/nougat) | 论文/课件公式转 LaTeX | 二期 |
| PDF/PPT 解析 | [marker](https://github.com/VikParuchuri/marker) | PDF 转 Markdown | 二期 |
| 本地 VLM | [Ollama](https://github.com/ollama/ollama) | 一行命令本地运行 Qwen2-VL、LLaVA 等 | 二期 |
| 本地 VLM 推理 | [vLLM](https://github.com/vllm-project/vllm) | 高性能本地模型推理 | 二期 |
| 混合检索 | [BM25s](https://github.com/xhluca/bm25s) | 轻量 BM25 稀疏检索 | 二期 |
| 任务队列 | [huey](https://github.com/coleifer/huey) | 轻量异步任务队列，SQLite 后端 | 二期 |
| 前端组件 | [streamlit-player](https://github.com/svg-icons/streamlit-player) | 视频播放组件 | US3 |
| 前端组件 | [stqdm](https://github.com/Wirg/stqdm) | 处理进度条组件 | US1 |

## 八、参考资料

- [PaddleOCR 官方仓库](https://github.com/PaddlePaddle/PaddleOCR)
- [faster-whisper 官方仓库](https://github.com/SYSTRAN/faster-whisper)
- [DeepSeek API 文档](https://platform.deepseek.com/)
- [LangChain 文档](https://python.langchain.com/)
- [Chroma 文档](https://docs.trychroma.com/)
- [Streamlit 文档](https://docs.streamlit.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- 用户桌面文件: `AI慕课学伴-技术方案对比.md`（v4.0 最终版）

---

**研究结论**: 采用 **FastAPI + Streamlit + faster-whisper + PaddleOCR + DeepSeek-VL + DeepSeek Chat + Chroma + SQLite** 的技术组合，以低成本、本地优先、可配置切换为原则，支撑 AI 慕课学伴的三大核心功能。MVP 阶段聚焦主链路，二期可通过成熟开源工具扩展 URL 下载、本地 VLM、混合检索等能力。
