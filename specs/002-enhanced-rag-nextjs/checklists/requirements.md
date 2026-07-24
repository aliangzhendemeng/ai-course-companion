# 验收检查清单：AI 慕课学伴下一版本增强

**Purpose**: 本清单用于在实现完成后逐项验收本版本功能，确保每个用户故事和关键非功能需求都已满足。
**Created**: 2026-07-24
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [tasks.md](../tasks.md)

---

## 一、US1 - 多模型配置与视频流式播放

- [x] CHK001 `.env.example` 中已包含 `SUMMARY_MODEL`、`CHAT_MODEL`、`VISION_MODEL` 及对应 API Key 配置项
- [x] CHK002 `backend/config.py` 正确读取新配置项，并在新项为空时回退到旧配置
- [x] CHK003 `backend/ai/factory.py` 提供 `create_summary_llm()`、`create_chat_llm()`、`create_vision_analyzer()`
- [x] CHK004 `backend/ai/summarizer.py` 使用 `create_summary_llm()`
- [x] CHK005 `backend/ai/rag_engine.py` 使用 `create_chat_llm()`
- [x] CHK006 `backend/ai/processor.py` 使用 `create_vision_analyzer()`
- [x] CHK007 `backend/schemas.py` 中 `CourseDetail` 返回 `video_url` 而非 `video_path`
- [x] CHK008 `backend/api/courses.py` 新增 `GET /api/courses/{course_id}/video` 接口
- [x] CHK009 视频流接口在无 `Range` 头时返回 200，有 `Range` 头时返回 206 与正确 `Content-Range`
- [x] CHK010 `frontend/pages/02_课程学习.py` 使用 `video_url` 播放视频
- [ ] CHK011 在至少一种模型配置下完成一门课程处理，确认总结和问答正常（需真实 API key）

---

## 二、US2 - 帧处理加速

- [x] CHK012 `backend/core/frame_extractor.py` 支持 `mode=uniform|scene`
- [x] CHK013 场景变化检测模式下，重复画面不生成冗余帧
- [x] CHK014 当场景检测失灵或视频过短时，均匀抽帧 fallback 生效
- [x] CHK015 `backend/ai/frame_complexity.py` 能基于 OCR 结果区分简单帧与复杂帧
- [x] CHK016 简单帧（纯文字 PPT）仅使用 OCR，不调用视觉 API
- [x] CHK017 复杂帧（图表/公式/代码）调用视觉 API 并生成 `vision_desc`
- [x] CHK018 `backend/ai/frame_enricher.py` 使用 `ThreadPoolExecutor` 并发调用 VLM
- [x] CHK019 并发数不超过 `VISION_MAX_WORKERS` 配置
- [x] CHK020 单个视觉 API 调用失败时降级为 OCR，不中断课程处理
- [ ] CHK021 处理一门 45 分钟课程，帧处理阶段耗时比旧版本明显降低（需真实视频）

---

## 三、US3 - 混合检索与全局跨课程搜索

- [x] CHK022 `requirements.txt` 已安装 `bm25s` 和 `jieba`
- [x] CHK023 `backend/ai/text_utils.py` 使用 jieba 对中文文本分词
- [x] CHK024 `backend/ai/rank_utils.py` 实现 RRF 融合公式
- [x] CHK025 `backend/ai/rag_engine.py` 为每个文档生成稳定 `doc_id`
- [x] CHK026 同一文档同时写入课程 collection、全局 collection、课程 BM25、全局 BM25
- [x] CHK027 单课问答使用 RRF 融合向量检索与 BM25 结果
- [x] CHK028 使用精确关键词提问时，混合检索能召回向量检索遗漏的内容
- [x] CHK029 `backend/ai/rag_engine.py` 提供 `query_all(question)` 方法
- [x] CHK030 全局问答结果包含来源课程 ID 与标题
- [x] CHK031 `backend/api/chat.py` 支持 `scope=course` 与 `scope=all`
- [x] CHK032 删除课程后，该课程在全局 collection 和全局 BM25 中不再存在
- [x] CHK033 `frontend/pages/03_知识问答.py` 支持选择搜索范围

---

## 四、US4 - 现代 React 前端

- [x] CHK034 `frontend-next/` 目录存在且可执行 `npm install` 和 `npm run dev`
- [x] CHK035 Next.js 前端样式遵循 `design-system/MASTER.md` 的颜色、字体、间距规范
- [x] CHK036 课程库页面 `/courses` 展示卡片式课程列表与状态标签
- [x] CHK037 课程学习页面 `/courses/[id]` 左侧播放视频，右侧展示三级总结
- [x] CHK038 点击大纲时间戳，视频跳转到对应位置
- [x] CHK039 知识问答页面 `/chat` 支持单课/全局搜索范围切换
- [x] CHK040 AI 回答以聊天流式呈现，下方显示可点击来源卡片
- [x] CHK041 来源卡片点击可跳转到对应课程与时间点
- [x] CHK042 页面在 375px / 768px / 1024px / 1440px 下布局正常
- [x] CHK043 Streamlit 前端仍可完整使用所有后端功能

---

## 五、非功能需求与工程化

- [x] CHK044 所有新增后端功能在 Streamlit 前端中保持可用
- [x] CHK045 后端 CORS 配置放行 `localhost:3000` 和 `localhost:8501`
- [x] CHK046 `.env.example` 已同步所有新增环境变量
- [x] CHK047 `README.md` 已补充 Next.js 启动说明和新配置项说明
- [x] CHK048 新增启动脚本 `start_frontend_next.sh` 可正常启动 Next.js
- [x] CHK049 核心模块单元测试覆盖率不低于 70%
- [x] CHK050 集成测试覆盖上传 → 处理 → 单课问答 → 全局问答 → 删除完整流程
- [x] CHK051 代码无静默吞异常，所有异常都有日志记录
- [ ] CHK052 运行一次真实视频端到端验证，处理成功且问答结果合理（需真实 API key）

---

## Notes

- 检查项按用户故事分组，实现和验收时可逐项勾选。
- 每项验收应至少包含一次手动验证或自动化测试通过。
- 发现阻塞问题时，应在对应检查项后添加注释，并回退到 plan/tasks 调整。
- 本版本完成度：49/52 项自动化或代码层面已验收；CHK011、CHK021、CHK052 需真实 API key / 真实视频手动验证。
