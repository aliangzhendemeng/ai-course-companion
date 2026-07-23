# AI 慕课学伴

基于 SpecKit 方法构建的 AI 慕课学习助手，支持视频上传、字幕提取、关键帧 OCR/VLM 解析、RAG 知识问答和学习进度跟踪。

## 环境要求

- Python 3.11+
- macOS / Linux / Windows
- 建议预留 5GB+ 磁盘空间（用于视频、帧图、向量数据库）

## 快速启动

### 1. 创建并激活虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY
```

### 3. 启动后端

```bash
./start_backend.sh
```

后端服务将运行在 http://127.0.0.1:8000

### 4. 启动前端

新起一个终端，执行：

```bash
./start_frontend.sh
```

前端将运行在 http://localhost:8501

> 两个启动脚本会自动切换到项目根目录、激活虚拟环境，并从正确路径读取 `.streamlit/config.toml` 中的 2GB 上传限制。

## 项目结构

```
ai-course-companion/
├── backend/              # FastAPI 后端
│   ├── api/              # REST API 路由
│   ├── ai/               # AI / RAG / VLM 处理
│   ├── core/             # 视频、音频、OCR 等核心处理
│   ├── services/         # 业务逻辑
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库连接
│   └── main.py           # FastAPI 入口
├── frontend/             # Streamlit 前端
│   ├── Home.py
│   └── pages/
├── data/                 # 上传视频、帧图、数据库、向量库
├── specs/                # SpecKit 规格说明
├── tests/                # 测试
├── requirements.txt
├── run.py                # 后端启动脚本（Python）
├── run_frontend.py       # 前端启动脚本（Python）
├── start_backend.sh      # 后端一键启动脚本（Bash）
└── start_frontend.sh     # 前端一键启动脚本（Bash）
```

## 视频上传说明

- 支持格式：mp4、mkv、mov、avi
- 最大支持 2GB，适合 45 分钟左右的慕课视频
- 上传后会在后台异步完成字幕提取、关键帧分析和总结生成

## 常见问题

**Q: 启动后端时报 `ModuleNotFoundError: No module named 'backend'`？**

A: 请使用项目提供的 `run.py` 启动，它会自动将项目根目录加入 Python 模块搜索路径。

**Q: 启动后端时报 `sqlite3.OperationalError: unable to open database file`？**

A: 数据库路径已改为基于项目根目录的绝对路径。如果仍有问题，请检查 `data/` 目录是否存在且可写。

**Q: 上传大视频时提示超过 200MB 限制？**

A: 请使用 `python run_frontend.py` 启动前端，确保读取到项目根目录 `.streamlit/config.toml` 中的 2GB 上传限制。直接运行 `streamlit run frontend/Home.py` 时，若当前目录不是项目根目录，会忽略该配置。

## 开发命令

```bash
# 运行测试
pytest

# 代码检查（可选）
# ruff check .
```
