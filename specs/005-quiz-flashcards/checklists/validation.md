# Validation Checklist: 005 第一迭代（测验 + 闪卡）

**Date**: 2026-07-30 ｜ **环境**: 本地后端（uvicorn）+ 真实 LLM（deepseek）

## 后端单元测试（pytest，49 passed）

- [x] quiz_generator：JSON 解析（干净数组 / 前后废话 / markdown 围栏 / 字符串内括号 / 转义引号 / 未闭合 / 顶层非数组）、题目与闪卡规范化（非法项过滤、判断题答案同义词、答案字母越界丢弃）、失败重试一次后成功 / 两次失败抛错
- [x] quiz_service：单课程生成、追加（不覆盖）、未完成课程报错、范围二选一校验、学习集范围（study_set_id + source_course_id）、选择判分（大小写容错）、判断判分（对/正确同义）、题目不存在报错、清空
- [x] flashcard_service：生成默认 unknown、追加、三档熟悉度标记、非法熟悉度报错、统计计数、清空

## 端到端（真实 LLM，课程 1「大数据智能信息处理1绪论」）

- [x] `POST /api/quiz/generate`（course_id=1, count=4）→ `{"generated":4,"total":4}`，约 4.4s；产出 3 选择 + 1 判断，题干/选项/解析均贴合课程内容
- [x] 判分：答错返回 `correct:false` + 正确答案 + 解析；答对返回 `correct:true`；判断题答错同样正确判分
- [x] `POST /api/flashcards/generate`（course_id=1, count=3）→ 3 张卡，默认 `familiarity=unknown`，正面/背面切题
- [x] `PATCH /api/flashcards/{id}` 标记 known/fuzzy → `GET /stats` 返回 `{total:3,known:1,fuzzy:1,unknown:1}` 持久化正确
- [x] 学习集范围：建学习集（课 1+2）→ `generate`（study_set_id）成功，题目记录 `source_course_id`；测验与闪卡均支持学习集
- [x] 范围隔离：清空学习集题不影响单课程题（set2→0，course1→4）
- [x] 清空：`DELETE /api/quiz`、`DELETE /api/flashcards` 返回删除数

## 前端（tsc --noEmit 通过）

- [x] QuizPanel：生成/清空按钮、单选/判断作答、对错高亮 + 正确答案 + 解析、来源时间戳跳回视频
- [x] FlashcardPanel：生成/清空、点击翻卡、上一张/下一张、三档熟悉度标记（标记后自动前进）、统计、只看模糊+不认识筛选、全认识庆祝态
- [x] 课程学习页左列：总结 / 测验 / 闪卡 三个 Tab
- [x] 课程库页顶部：StudySetStudyPanel（选择学习集 → 测验/闪卡 Tab），来源跳转对应课程时间点

## 已知留待后续迭代

- 学习集出题的逐题 `source_course_id` 精确定位（当前记首门课），plan 已预留
- 来源 `source_timestamp` 当前多为 `None`（出题 prompt 未强制逐题标注时间戳），后续迭代强化
- 掌握度 / 错题本 / 学伴角色 / 打卡（第二迭代），实时对话 / 简答 / SM-2（006）
