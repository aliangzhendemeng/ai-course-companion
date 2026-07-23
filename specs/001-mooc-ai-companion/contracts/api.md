# API / 模块契约

## 后端 API

### 课程 Courses

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/courses` | 列出所有课程 |
| POST | `/api/courses/upload` | 上传视频并创建课程 |
| GET | `/api/courses/{course_id}` | 获取课程详情 |
| DELETE | `/api/courses/{course_id}` | 删除课程 |
| POST | `/api/courses/{course_id}/reprocess` | 重新处理课程 |

### 总结 Summaries

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/summaries/{course_id}` | 获取课程总结 |

### 问答 Chat

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/chat/{course_id}` | 向课程提问 |
| GET | `/api/chat/{course_id}/history` | 获取问答历史 |

### 进度 Progress

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/progress/{course_id}` | 获取学习进度 |
| POST | `/api/progress/{course_id}` | 更新学习进度 |

## 模块接口

### 视觉分析器

所有视觉分析器必须继承 `backend.ai.vision.base.BaseVisionAnalyzer`：

```python
class BaseVisionAnalyzer(ABC):
    @abstractmethod
    def understand_frame(self, image_path: str | Path) -> str:
        pass
```

已实现：
- `DeepSeekVisionAnalyzer`：调用 DeepSeek-VL，失败时降级为 OCR
- `GeminiVisionAnalyzer`：预留
- `LocalVLMVisionAnalyzer`：本地 VLM 预留接口

### LLM

所有 LLM 必须继承 `backend.ai.llm.base.BaseLLM`：

```python
class BaseLLM(ABC):
    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        pass
```

已实现：
- `DeepSeekLLM`：DeepSeek Chat
- `GeminiLLM`：预留
- `ClaudeLLM`：预留

### RAG 引擎

```python
class RAGEngine:
    def index_course(self, course_id: int, transcripts: list[Transcript], frames: list[Frame]) -> None
    def query(self, course_id: int, question: str) -> dict  # {answer, sources}
    def delete_index(self, course_id: int) -> None
```
