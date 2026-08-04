# Tasks: 项目展示静态站（showcase-site）

## Phase 1: Astro 骨架与样式

- [ ] T001 `showcase/` Astro 项目初始化：package.json（astro）、astro.config.mjs（GitHub Pages base）、tsconfig
- [ ] T002 Layout + 全局样式：技术文档风排版、配色、代码块、表格、卡片组件
- [ ] T003 通用组件：Hero / Section / FeatureCard / PitfallCard / TechBadge / Timeline / CompareTable

## Phase 2: 内容（基于真实开发全程）

- [ ] T004 Hero 首屏：项目名 + 定位（AI 学伴）+ 亮点 + CTA
- [ ] T005 成果展示：版本演进（001→006）+ 功能矩阵 + 截图/GIF 位
- [ ] T006 技术方案：架构图（SVG/HTML）+ 技术栈 + 关键模块详解 + 数据流
- [ ] T007 AI 开发方法：speckit 流程 + Claude Code 协作 + 经验教训
- [ ] T008 设计决策（为什么）：关键选型对比（faster-whisper vs API、Playwright 子进程、引用后端映射、字幕 custom 渲染、断点续传…）
- [ ] T009 踩坑与解决：课程路由误删、SM-2 迁移 NULL、字幕渲染两次、deepseek 503、yt-dlp SSL、reload 卡死、引用堆砌、Playwright event loop…
- [ ] T010 后续规划：006 future work

## Phase 3: 素材生成

- [ ] T011 Playwright 脚本 `scripts/gen_assets.py`：自动截图 + 录视频
- [ ] T012 录视频转 GIF（ffmpeg）
- [ ] T013 跑脚本生成截图/GIF 到 public/

## Phase 4: 构建与部署

- [ ] T014 `astro build` 通过，dist/ 生成
- [ ] T015 截图嵌入内容，本地预览验证
- [ ] T16 README 加 showcase 启动/部署说明
