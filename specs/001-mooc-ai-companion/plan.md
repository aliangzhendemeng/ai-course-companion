# Implementation Plan: AI 慕课学伴

**Branch**: `001-mooc-ai-companion` | **Date**: 2026-07-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-mooc-ai-companion/spec.md` and research from `/specs/001-mooc-ai-companion/research.md`

## Summary

实现一个 AI 慕课学伴系统。用户上传本地视频后，系统自动提取音频字幕、抽取关键帧并识别画面内容，生成课程大纲/摘要/讲义三级总结，并支持基于课程内容的 RAG 问答（带时间戳和关键帧定位）。

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**:
- FastAPI 0.104+（后端 API）
- Streamlit 1.28+（前端界面）
- faster-whisper 0.10+（本地 ASR）
- PaddleOCR 2.7+ + paddlepaddle 2.6+（本地 OCR）
- google-generativeai 0.3+（Gemini Vision，预留可切换）
- openai 1.3+（DeepSeek-VL 通过兼容接口调用）
- LangChain 0.1+ + langchain-community（RAG 框架）
- Chroma 0.4+（向量库）
- sentence-transformers 2.2+（中文嵌入模型）
- SQLModel 0.0.14+（SQLite ORM）
- opencv-python 4.8+、pillow 10.1+、ffmpeg-python（图像与视频处理）

**Storage**: SQLite（课程、字幕、帧、总结、问答历史、学习进度）；本地文件系统（上传视频、关键帧、Chroma 向量库）

**Testing**: pytest，包含单元测试和集成测试。核心处理链路提供示例测试视频用于回归验证。

**Target Platform**: macOS（优先）、Linux（兼容）、Windows（尽力而为）

**Project Type**: Web 应用（后端 API + Streamlit 前端）

**Performance Goals**:
- 40 分钟标准课程从上传到生成完整总结的处理时间不超过 80 分钟（CPU 环境）。
- 问答响应时间不超过 10 秒（不含首次加载模型时间）。
- Streamlit 页面加载时间不超过 3 秒。

**Constraints**:
- 月度外部 API 成本控制在 100 元人民币以内（按 10 门 40 分钟课程估算）。
- 优先本地处理音频和 OCR，降低外部调用成本。
- 所有外部模型（视觉、LLM）通过配置可切换，并预留本地 VLM 接口。
- 单课程关键帧上限 120，控制成本和内存占用。

**Scale/Scope**:
- MVP 阶段为单用户本地使用。
- 每门课程支持 5 分钟到 2 小时视频。
- 暂不支持多用户并发和云端部署。

## Constitution Check

对照项目宪法检查，无违反项：

| 宪法原则 | 本计划如何满足 |
|---|---|
| 效果优先，成本可控 | 优先本地 ASR/OCR，视觉和 LLM 选择性价比高的 DeepSeek，模型可配置切换 |
| 用户数据本地优先 | 视频、帧、向量库、数据库全部本地存储 |
| 中文课程优先优化 | PaddleOCR 中文最佳，DeepSeek 中文能力强，界面默认简体中文 |
| 简洁可维护 | 模块化设计，OCR/视觉/LLM 均通过统一接口封装 |
| 可测试与可演示 | 每个用户故事可独立验证，保留示例测试视频 |
| 渐进式交付 | 按 P1→P2→P3 顺序实现，每个阶段都有可演示产物 |

## Project Structure

### Documentation (this feature)

```text
specs/001-mooc-ai-companion/
├── spec.md              # 功能规格
├── research.md          # 技术选型研究
├── plan.md              # 本文件
├── data-model.md        # 数据模型
├── quickstart.md        # 快速开始
├── checklists/
│   └── requirements.md  # 规格质量检查
└── contracts/           # API/模块契约
```

### Source Code (repository root)

```text
ai-course-companion/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理（Pydantic Settings + .env）
│   ├── database.py                # SQLModel/SQLite 会话管理
│   ├── models/
│   │   ├── __init__.py
│   │   ├── course.py              # Course 模型
│   │   ├── transcript.py          # Transcript 模型
│   │   ├── frame.py               # Frame 模型
│   │   ├── summary.py             # Summary 模型
│   │   ├── chat_message.py        # ChatMessage 模型
│   │   └── progress.py            # Progress 模型
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audio_extractor.py     # 视频→音频（ffmpeg）
│   │   ├── frame_extractor.py     # 视频均匀抽帧
│   │   ├── asr_engine.py          # faster-whisper 语音识别
│   │   └── ocr_engine.py          # PaddleOCR 文字识别
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── vision/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # 视觉分析抽象接口
│   │   │   ├── deepseek_vision.py # DeepSeek-VL 实现
│   │   │   ├── gemini_vision.py   # Gemini Vision 实现（预留）
│   │   │   └── local_vlm_vision.py # 本地 VLM 实现（预留接口）
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # LLM 抽象接口
│   │   │   ├── deepseek_llm.py    # DeepSeek Chat 实现
│   │   │   └── gemini_llm.py      # Gemini LLM 实现（预留）
│   │   ├── summarizer.py          # 三级总结生成
│   │   ├── rag_engine.py          # RAG 检索与问答
│   │   └── processor.py           # 完整视频处理编排
│   ├── services/
│   │   ├── __init__.py
│   │   ├── course_service.py      # 课程 CRUD 与状态管理
│   │   ├── summary_service.py     # 总结服务
│   │   └── chat_service.py        # 问答服务
│   ├── api/
│   │   ├── __init__.py
│   │   ├── courses.py             # 课程相关 API
│   │   ├── summaries.py           # 总结相关 API
│   │   └── chat.py                # 问答相关 API
│   └── schemas.py                 # Pydantic 请求/响应模型
├── frontend/
│   ├── Home.py                    # Streamlit 入口 / 课程库
│   └── pages/
│       ├── 01_课程库.py           # 上传视频、查看课程列表
│       ├── 02_课程学习.py         # 播放视频、查看总结
│       └── 03_知识问答.py         # 提问、查看回答与时间戳
├── data/                          # 运行时数据（不提交到 git）
│   ├── uploads/                   # 上传视频
│   ├── frames/                    # 关键帧
│   ├── chroma/                    # 向量库
│   └── app.db                     # SQLite 数据库
├── tests/
│   ├── __init__.py
│   ├── unit/                      # 单元测试
│   ├── integration/               # 集成测试
│   └── fixtures/                  # 测试视频与期望输出
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

**Structure Decision**: 采用 backend/frontend 分离结构。后端负责多模态处理、RAG 和数据持久化；前端用 Streamlit 多页面应用提供上传、学习、问答三个核心页面。数据统一放在 `data/` 目录下，便于本地管理和清理。

## Complexity Tracking

本项目未引入超出 MVP 需要的复杂度：

| 潜在复杂度 | 是否引入 | 说明 |
|---|---|---|
| 多项目仓库 | 否 | 单一仓库，backend + frontend + specs |
| 微服务 | 否 | 单后端进程 |
| 外部任务队列（Celery/Redis） | 否 | MVP 使用 asyncio 异步处理 |
| 多用户认证 | 否 | 单用户本地使用 |
| 前端组件 | `streamlit-player` | US3 视频播放 |
| 前端组件 | `stqdm` | US1 处理进度条 |
| 二期扩展 | `yt-dlp` / `you-get` | URL 视频下载 |
| 二期扩展 | `Ollama` / `vLLM` | 本地 VLM 推理 |
| 二期扩展 | `BM25s` | 混合检索增强 |
| 二期扩展 | `huey` | 后台异步任务队列 |

所有设计选择均满足宪法中的“简洁可维护”和“渐进式交付”原则。

## 二期扩展方向

| 方向 | 可复用工具 |
|---|---|
| URL 视频下载 | `yt-dlp`、`you-get` |
| 本地 VLM 推理 | `Ollama`、`vLLM` |
| ASR 增强 | `whisperx`、`funasr` |
| 公式识别 | `nougat` |
| PDF/PPT 课件解析 | `marker`、`python-pptx` |
| 混合检索 | `BM25s` |
| 后台任务队列 | `huey` |
