# 004 端到端验证清单

**Feature**: 004 - 多课程学习集与使用门槛优化
**Date**: 2026-07-29

## US1 多课程学习集（核心）

- [x] 创建学习集：POST /api/study-sets 勾选课程 1+2，返回含课程名
- [x] 重命名 + 增删课程：PATCH 后课程列表更新
- [x] 删除学习集：DELETE 后列表移除（课程本身不受影响）
- [x] 学习集问答范围限定：`scope=set&course_ids=[1,2]` 提问，所有来源 course_id ∈ {1,2}，越界数 = 0
- [x] 来源带课程名 + 真实时间戳（非全 0:00）
- [x] 检索过滤生效：`_retrieve(course_filter=[2])` 只命中课程 2（实测）
- [x] 空学习集降级：query_multiple([]) 返回"暂无可用课程"提示
- [x] 前端：ChatPanel 三档范围（当前课程/选择课程/全部课程），set 模式弹 Picker
- [x] 前端：未选课时禁用发送并提示
- [x] 学习集问答历史正确显示"学习集 · 课程1、课程2"（修复锚点误标）

## US2 一键启动脚本

- [x] start_app.sh 同时启动前后端（后端 200 / 前端正常）
- [x] Ctrl+C / SIGINT 后两端口全释放、无残留进程（实测）
- [x] --no-open 跳过自动开浏览器
- [x] 端口占用 / 依赖缺失给出友好提示
- [x] start_app.bat（Windows）双窗口启动 + 自动开浏览器

## US3 设置页完善

- [x] 首次未配置自动进 /welcome 引导（003 已有）
- [x] 保存成功显示绿色提示 + "重启后端使配置生效"按钮
- [x] POST /api/settings/restart 触发 uvicorn reload（实测后端仍 200）

## 修复的回归 / 预存问题

- [x] 历史时间显示：naive UTC → 带时区 UTC，前端正确转北京时间（+8）
- [x] 历史课程归属：set/all 挂错锚点课程 → course_ids 记录实际涉及课程
- [x] 幂等增量列迁移：ALTER TABLE ADD COLUMN（chatmessage.course_ids）
- [x] 003 预存的 3 个 chat_service 测试失败 → 全部修复，17 个测试通过

## 测试

- [x] 后端 17 个单元测试全部通过（chat_service + settings + query_multiple）

## 裁剪项

- [ ] US4 桌面 App 包装（Tauri/Electron）——按计划延后到下版
