# Plan: 项目展示静态站（showcase-site）

## Summary

用 Astro 构建独立静态展示站，部署 GitHub Pages。单页长滚动（首屏 landing + 内页 sections），内容覆盖三目标（成果/技术/AI方法）+ 为什么/坑/规划。Playwright 脚本自动生成功能截图/GIF 素材，无需手动录屏。

## 技术选型

- **Astro**：静态优先、组件化、Markdown 友好、GitHub Pages 部署。比纯 HTML 易维护，比 Next.js 轻（无 JS 运行时开销）
- **Playwright**（Python，项目已装）：自动截图 + 录视频转 GIF
- 单页 `index.astro`（sections）+ 复用 Layout/组件

## 站点结构

```
showcase/
├── package.json            # astro 依赖
├── astro.config.mjs        # GitHub Pages base path
├── public/
│   ├── screenshots/        # Playwright 生成的截图
│   └── gifs/               # 录屏转 GIF
├── scripts/
│   └── gen_assets.py       # Playwright 自动截图/录屏
└── src/
    ├── layouts/Layout.astro
    ├── components/         # Hero / Section / FeatureCard / PitfallCard / TechStack / Timeline ...
    └── pages/index.astro   # 单页，含全部 sections
```

## 内容板块（sections）

1. **Hero 首屏**：项目名 + 一句话定位（AI 学伴）+ 核心亮点 + CTA
2. **成果展示**：版本演进时间线（001→006）+ 功能矩阵 + 关键功能截图/GIF
3. **技术方案**：架构图 + 技术栈 + 关键模块（混合检索 RAG / faster-whisper / PaddleOCR / SM-2 / 会话制 / Playwright 子进程 / 联网搜索）+ 数据流
4. **AI 开发方法**：speckit 流程 + Claude Code 人机协作 + 经验教训
5. **设计决策（为什么）**：关键选型对比（为什么 X 不用 Y）
6. **踩坑与解决**：真实 bug 案例 + 根因 + 修复
7. **后续规划**：006 future work

## Playwright 素材生成

`scripts/gen_assets.py`：
- 假设前后端运行（localhost:3000）
- 自动访问：课程库 / 课程详情（视频+总结）/ 问答（带引用角标）/ 闪卡翻卡 / 错题本 / 学伴动作 / 笔记
- 截图（page.screenshot）+ 关键操作录视频（record_video）→ ffmpeg 转 GIF
- 输出到 public/screenshots + public/gifs

## 部署

- `astro build` → `dist/`
- GitHub Pages（base path 配仓库名）
- 或本地 `astro dev` 预览

## 实现策略

1. 先搭 Astro 骨架 + 样式系统（技术文档风 + 首屏 landing）
2. 写内容（基于真实开发全程，为什么/坑均有据）
3. Playwright 脚本 + 生成素材
4. 构建验证
