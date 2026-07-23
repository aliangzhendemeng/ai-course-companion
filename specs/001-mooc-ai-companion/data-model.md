# Data Model: AI 慕课学伴

**Scope**: 定义 AI 慕课学伴持久化层的实体、字段、关系和约束。

**Storage**: SQLite，通过 SQLModel 进行对象关系映射。

**Date**: 2026-07-23

---

## 一、实体关系图

```text
Course 1 ──* Transcript
Course 1 ──* Frame
Course 1 ──1 Summary
Course 1 ──* ChatMessage
Course 1 ──1 Progress
```

说明：
- 一个课程包含多条字幕记录（Transcript）。
- 一个课程包含多个关键帧（Frame）。
- 一个课程对应一份三级总结（Summary）。
- 一个课程对应多条问答历史（ChatMessage）。
- 一个课程对应一条学习进度（Progress）。

---

## 二、Course（课程）

存储用户上传的视频及其处理状态。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | Integer | PK, auto-increment | 课程唯一标识 |
| title | String | 非空 | 课程标题，默认取视频文件名 |
| video_path | String | 非空，唯一 | 上传视频文件的本地路径 |
| duration | Float | 可空 | 视频时长（秒） |
| status | String | 非空，默认 `uploaded` | 处理状态，见状态机定义 |
| status_message | String | 可空 | 当前状态说明或错误信息 |
| frame_interval | Float | 可空 | 实际抽帧间隔（秒） |
| max_frames | Integer | 可空 | 实际最大帧数限制 |
| created_at | DateTime | 非空，默认当前时间 | 创建时间 |
| updated_at | DateTime | 非空，默认当前时间 | 最后更新时间 |

**状态机**:

```
uploaded
  ↓
extracting_audio
  ↓
transcribing
  ↓
extracting_frames
  ↓
ocr_and_vision
  ↓
generating_summary
  ↓
indexing_rag
  ↓
completed
  ↓
failed
```

状态迁移方向为单向。失败状态允许用户触发重新处理。

---

## 三、Transcript（字幕）

存储从视频音频中提取的分段文本。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | Integer | PK, auto-increment | 字幕唯一标识 |
| course_id | Integer | FK → Course.id, 级联删除 | 所属课程 |
| text | String | 非空 | 该时间段内的识别文本 |
| start_time | Float | 非空 | 开始时间（秒） |
| end_time | Float | 非空 | 结束时间（秒） |
| confidence | Float | 可空 | ASR 置信度 |
| created_at | DateTime | 非空，默认当前时间 | 创建时间 |

**约束**:
- `start_time < end_time`
- 同课程下时间段不重叠

---

## 四、Frame（关键帧）

存储从视频中抽取的关键帧及其多模态信息。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | Integer | PK, auto-increment | 关键帧唯一标识 |
| course_id | Integer | FK → Course.id, 级联删除 | 所属课程 |
| timestamp | Float | 非空 | 帧在视频中的时间戳（秒） |
| image_path | String | 非空 | 帧图像的本地路径 |
| thumbnail_path | String | 可空 | 缩略图本地路径 |
| ocr_text | String | 可空 | OCR 提取的文字（整帧拼接） |
| vision_desc | String | 可空 | 视觉模型对画面的描述 |
| created_at | DateTime | 非空，默认当前时间 | 创建时间 |

**约束**:
- 同课程下 `timestamp` 唯一
- `image_path` 指向 `data/frames/` 下的文件

---

## 五、Summary（总结）

存储课程的三级总结内容。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | Integer | PK, auto-increment | 总结唯一标识 |
| course_id | Integer | FK → Course.id, 级联删除，唯一 | 所属课程 |
| outline | String | 可空 | 课程大纲（JSON 或 Markdown） |
| abstract | String | 可空 | 内容摘要 |
| lecture_notes | String | 可空 | 详细讲义 |
| created_at | DateTime | 非空，默认当前时间 | 创建时间 |
| updated_at | DateTime | 非空，默认当前时间 | 更新时间 |

**说明**:
- `outline` 建议存储 JSON 数组，每个元素包含章节标题和时间戳。
- `abstract` 和 `lecture_notes` 存储 Markdown 文本。

---

## 六、ChatMessage（问答消息）

存储用户在问答页面提出的问题及系统回答。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | Integer | PK, auto-increment | 消息唯一标识 |
| course_id | Integer | FK → Course.id, 级联删除 | 所属课程 |
| role | String | 非空 | `user` 或 `assistant` |
| content | String | 非空 | 消息内容 |
| sources | String | 可空 | 引用来源 JSON 数组，包含时间戳和 frame_id |
| created_at | DateTime | 非空，默认当前时间 | 创建时间 |

**sources 示例**:

```json
[
  {
    "type": "transcript",
    "timestamp": 125.5,
    "text": "神经网络由输入层、隐藏层和输出层组成"
  },
  {
    "type": "frame",
    "frame_id": 12,
    "timestamp": 126.0,
    "thumbnail_path": "data/frames/course_1/frame_126.jpg"
  }
]
```

---

## 七、Progress（学习进度）

存储用户每门课程的最后观看到位置。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | Integer | PK, auto-increment | 进度唯一标识 |
| course_id | Integer | FK → Course.id, 级联删除，唯一 | 所属课程 |
| last_position | Float | 非空，默认 0 | 最后观看到的时间（秒） |
| updated_at | DateTime | 非空，默认当前时间 | 更新时间 |

---

## 八、索引设计

| 表 | 索引字段 | 用途 |
|---|---|---|
| Course | status | 按状态查询课程列表 |
| Course | created_at | 课程列表排序 |
| Transcript | (course_id, start_time) | 按课程和时间范围查询 |
| Frame | (course_id, timestamp) | 按课程和时间戳查询 |
| Summary | course_id | 快速获取课程总结 |
| ChatMessage | (course_id, created_at) | 按课程查询问答历史 |
| Progress | course_id | 快速获取学习进度 |

---

## 九、Chroma 向量集合

向量库使用 Chroma 本地持久化，集合名称与课程 ID 关联。

**集合命名**: `course_{course_id}`

**文档元数据**:

| 字段 | 说明 |
|---|---|
| course_id | 所属课程 |
| source_type | 来源类型：`transcript`、`ocr_text`、`vision_desc` |
| timestamp | 对应时间戳（秒） |
| frame_id | 对应帧 ID（仅 ocr_text / vision_desc） |
| transcript_id | 对应字幕 ID（仅 transcript） |

**文档切分策略**:
- 字幕文本：按 300-500 字符滑动窗口切分，保留时间戳。
- OCR 文字：以单帧 OCR 结果为一个文档。
- 视觉描述：以单帧视觉描述为一个文档。

---

## 十、文件存储约定

| 类型 | 路径约定 |
|---|---|
| 上传视频 | `data/uploads/{course_id}/video.{ext}` |
| 关键帧 | `data/frames/{course_id}/frame_{timestamp:.2f}.jpg` |
| 缩略图 | `data/frames/{course_id}/thumb_{timestamp:.2f}.jpg` |
| 音频临时文件 | `data/uploads/{course_id}/audio.wav` |
| Chroma 向量库 | `data/chroma/` |
| SQLite 数据库 | `data/app.db` |

---

## 十一、删除策略

- 删除课程时，级联删除关联的 Transcript、Frame、Summary、ChatMessage、Progress 记录。
- 删除课程时，同步删除 `data/uploads/{course_id}/` 和 `data/frames/{course_id}/` 目录。
- 向量集合 `course_{course_id}` 同步删除。

---

## 十二、二期扩展预留

以下实体本期不实现，但数据模型设计时预留扩展空间：

- **Bookmark（书签/收藏）**: 用户收藏的知识点，关联 Course 和 Frame/Transcript。
- **Quiz（测验）**: 基于课程内容生成的练习题和答案。
- **CourseSource（课程来源）**: URL 下载配置、浏览器录屏元信息等。
