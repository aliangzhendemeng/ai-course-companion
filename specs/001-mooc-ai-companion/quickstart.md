# Quickstart: AI 慕课学伴

**目标**: 在 30 分钟内完成环境搭建，并成功跑通第一个慕课视频的处理链路。

**适用平台**: macOS（优先）、Linux（兼容）

---

## 一、环境要求

- Python 3.11 或更高版本
- ffmpeg（系统级依赖）
- 约 10GB 可用磁盘空间（用于模型下载和临时文件）
- DeepSeek API Key

---

## 二、安装步骤

### 1. 进入项目目录

```bash
cd /Users/conglin/Projects/ai-course-companion
```

### 2. 安装 ffmpeg

**macOS**:

```bash
brew install ffmpeg
```

**Ubuntu/Debian**:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### 3. 创建 Python 虚拟环境

```bash
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate
```

### 4. 升级 pip 并安装 torch

```bash
pip install --upgrade pip setuptools wheel
pip install torch torchvision torchaudio
```

> 先安装 torch 可以避免 sentence-transformers 等包的依赖冲突。

### 5. 安装其他 Python 依赖

```bash
pip install -r requirements.txt
```

> 安装 PaddleOCR 和 paddlepaddle 可能需要较长时间，请耐心等待。

### 6. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 DeepSeek API Key：

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

其他配置保持默认即可。

---

## 三、验证环境

运行以下命令检查核心依赖是否安装成功：

```bash
python -c "
import cv2
from paddleocr import PaddleOCR
from faster_whisper import WhisperModel
from openai import OpenAI
import chromadb
print('✅ 环境检查通过')
"
```

如果没有任何报错，说明环境 OK。

---

## 四、启动服务

### 1. 启动后端 API

```bash
source venv/bin/activate
cd backend
uvicorn main:app --reload --port 8000
```

### 2. 启动前端界面

新开一个终端：

```bash
source venv/bin/activate
cd frontend
streamlit run Home.py
```

浏览器会自动打开 `http://localhost:8501`。

---

## 五、端到端验证

### 步骤 1：上传测试视频

1. 在浏览器中打开 Streamlit 界面。
2. 进入「课程库」页面。
3. 点击上传按钮，选择一个 5-10 分钟的中文技术类慕课视频。
4. 等待系统处理，状态会从 `uploaded` 逐步变为 `completed`。

### 步骤 2：查看课程总结

1. 处理完成后，点击课程卡片进入「课程学习」页面。
2. 确认能看到：
   - 课程大纲（带章节和时间戳）
   - 内容摘要
   - 详细讲义

### 步骤 3：进行知识问答

1. 进入「知识问答」页面。
2. 选择刚处理完成的课程。
3. 输入一个与课程内容相关的问题，例如：「请解释视频中提到的神经网络结构。」
4. 确认回答：
   - 内容基于课程
   - 附带相关时间戳
   - 涉及画面时展示关键帧

### 步骤 4：时间戳跳转

1. 在问答结果中点击一个时间戳。
2. 页面跳转到「课程学习」页面，视频自动从该时间点播放。

---

## 六、测试视频建议

为了验证系统效果，建议准备以下类型的测试视频：

| 类型 | 验证点 |
|---|---|
| 机器学习入门 | 架构图、公式 |
| 数学课程 | 公式推导、符号 |
| 编程教程 | 代码演示、语法 |
| 数据分析 | 图表、数据可视化 |

每段视频建议 5-10 分钟，便于快速验证。

---

## 七、常见问题

### Q1: PaddleOCR 安装失败怎么办？

确认 Python 版本是 3.11。PaddlePaddle 目前对 Python 3.12+ 支持有限。尝试单独安装：

```bash
pip install paddlepaddle==3.0.0
pip install paddleocr==2.7.0
```

如果仍失败，可以参考 [PaddleOCR 官方安装文档](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_ch/quickstart.md)。

### Q2: faster-whisper 下载模型很慢怎么办？

首次运行时会自动下载 Whisper 模型。可以通过设置环境变量指定国内镜像或手动下载后放到 `~/.cache/whisper/` 目录。

### Q3: 处理过程中报 API 错误怎么办？

检查 `.env` 中的 `DEEPSEEK_API_KEY` 是否正确，以及网络能否访问 DeepSeek API。查看后端日志中的具体错误信息。

### Q4: 可以切换视觉模型或 LLM 吗？

可以。修改 `.env` 中的 `VISION_MODEL` 和 `LLM_MODEL` 配置项，并填入对应的 API Key。当前支持：

```bash
VISION_MODEL=deepseek   # 可选: deepseek / gemini / claude / local_vlm
LLM_MODEL=deepseek      # 可选: deepseek / gemini / claude
```

### Q5: 视觉模型 API 不可用时怎么办？

系统会自动降级为仅使用 OCR 提取画面文字。如果希望完全离线运行，可以在 `.env` 中配置本地 VLM（预留接口）：

```bash
VISION_MODEL=local_vlm
LOCAL_VLM_MODEL_PATH=/path/to/your/local/vlm
LOCAL_VLM_DEVICE=cuda
```

---

## 八、目录说明

```text
data/
├── uploads/        # 上传的视频和临时音频
├── frames/         # 抽取的关键帧
├── chroma/         # 向量数据库
└── app.db          # SQLite 数据库
```

这些目录会在首次运行时自动创建，不需要手动创建。

---

## 九、下一步

环境跑通后，可以参考 [tasks.md](tasks.md) 按任务清单逐步理解或扩展系统。
