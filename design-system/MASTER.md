# Design System: AI 慕课学伴

> 生成工具：ui-ux-pro-max  
> 策略：以 AI-Native UI 的交互骨架为基础，采用教育场景的青绿色系，兼顾科技感与学习氛围。

---

## 1. 产品定位

**产品名称**：AI 慕课学伴  
**产品类型**：AI 教育学习助手 / 在线课程知识管理平台  
**核心场景**：视频课程上传 → AI 总结/抽帧 → 课程学习 → 知识问答（单课/全局）  
**目标用户**：大学生、职场自学者、MOOC 学习者  
**气质关键词**：智能、专注、清晰、可信赖、学习友好

---

## 2. 页面模式

**主模式**：AI 仪表盘（AI Dashboard）+ 对话式学习助手

| 页面 | 核心功能 |
|------|---------|
| 课程库 | 上传课程、查看处理状态、课程卡片列表 |
| 课程学习 | 视频播放 + 三级总结 + 大纲时间戳跳转 |
| 知识问答 | 聊天式问答 + 引用来源 + 全局/单课搜索切换 |

**布局原则**：
- 侧边导航 + 主内容区（三栏结构）。
- 内容密度中等，留白充足，适合长时间学习。
- 问答页以对话为核心，来源卡片作为上下文补充。

---

## 3. 视觉风格

**风格名称**：AI-Native UI + 教育感  
**关键词**：conversational, agentic, clean, focused, trustworthy, learning-oriented  
**模式支持**：浅色为主，深色后续扩展  
**性能**：优秀（避免重型阴影/模糊）  
**无障碍**：WCAG AA

### 3.1 颜色系统

| 角色 | Hex | CSS 变量 | 用途 |
|------|-----|----------|------|
| Primary | `#0D9488` | `--color-primary` | 主按钮、激活状态、链接、关键操作 |
| On Primary | `#FFFFFF` | `--color-on-primary` | 主按钮文字 |
| Secondary | `#2DD4BF` | `--color-secondary` | 辅助标签、进度条、图标高亮 |
| Accent / CTA | `#D97706` | `--color-accent` | 强调按钮、时间戳、跳转链接 |
| Background | `#F0FDFA` | `--color-background` | 页面背景 |
| Foreground | `#134E4A` | `--color-foreground` | 主要文字 |
| Muted | `#E8F1F4` | `--color-muted` | 次要背景、卡片hover |
| Border | `#5EEAD4` | `--color-border` | 卡片边框、分隔线 |
| Destructive | `#DC2626` | `--color-destructive` | 删除、错误 |
| Ring | `#0D9488` | `--color-ring` | focus ring |

**语义色**：
- 成功：`#059669`
- 警告：`#D97706`
- 错误：`#DC2626`
- 信息：`#0EA5E9`

**文字层次**：
- 主文字：`#134E4A`
- 次文字：`#2C7A7B`（透明度 0.75）
- 占位/禁用：`#94A3B8`

### 3.2 字体系统

**西文字体**：Inter  
**中文回退**：`"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif`  
**等宽字体**（用于代码/时间戳）：JetBrains Mono / SF Mono

```css
font-family: "Inter", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
```

**字号规模**：

| Token | 大小 | 用途 |
|-------|------|------|
| text-xs | 12px | 标签、时间、状态 |
| text-sm | 14px | 次要文字、按钮、来源描述 |
| text-base | 16px | 正文 |
| text-lg | 18px | 小标题 |
| text-xl | 20px | 卡片标题 |
| text-2xl | 24px | 页面标题 |
| text-3xl | 30px | 大标题/Hero |

**字重**：
- 标题：600-700
- 正文：400
- 标签/辅助：500

### 3.3 间距与圆角

**间距规模**（Tailwind 默认即可）：
- 紧凑：4px, 8px
- 常规：12px, 16px, 20px
- 宽松：24px, 32px, 48px

**圆角**：
- 按钮：`rounded-lg`（8px）
- 卡片：`rounded-xl`（12px）
- 输入框：`rounded-md`（6px）
- 标签/徽章：`rounded-full`
- 头像/小图标：`rounded-full`

---

## 4. 动效与交互

### 4.1 关键效果

- **流式文字动画**：AI 回答逐字显示或淡入。
- **打字指示器**：三圆点脉冲，表示 AI 思考中。
- **来源卡片展开**：点击引用来源，平滑展开上下文。
- **卡片悬停**：轻微上浮 + 阴影加深，过渡 200ms。
- **进度条动画**：课程处理进度平滑过渡。
- **时间戳跳转**：点击后视频平滑 seek（由播放器处理）。

### 4.2 时间参数

- 快速反馈：150ms（按钮 hover、状态变化）
- 标准过渡：200ms（卡片、展开收起）
- 慢速揭示：300ms（模态框、toast）
- 流式文字：逐 token 30-50ms

### 4.3 无障碍

- 尊重 `prefers-reduced-motion`，禁用非必要动画。
- 所有可点击元素有可见 focus ring。
- 文字对比度 ≥ 4.5:1。
- 不使用表情符号作为图标（使用 Lucide）。

---

## 5. 组件规范

### 5.1 按钮

| 类型 | 样式 |
|------|------|
| Primary | 背景 `#0D9488`，文字白色，hover `#0F766E`，shadow-sm |
| Secondary | 背景 `#E8F1F4`，文字 `#134E4A`，hover `#D1E3E8` |
| Accent | 背景 `#D97706`，文字白色，hover `#B45309` |
| Ghost | 透明背景，hover `#E8F1F4` |
| Danger | 背景 `#DC2626`，文字白色 |

### 5.2 卡片

- 背景：白色 `#FFFFFF`
- 边框：1px solid `#E2E8F0`（或 `#5EEAD4` 极浅）
- 阴影：`shadow-sm` / `shadow-md` on hover
- 圆角：`rounded-xl`
- 内边距：`p-4` 或 `p-6`

### 5.3 输入框

- 背景：白色
- 边框：默认 `#CBD5E1`，focus `#0D9488`
- 圆角：`rounded-md`
- placeholder：`#94A3B8`

### 5.4 标签/徽章

| 状态 | 颜色 |
|------|------|
| 处理中 | Secondary `#2DD4BF` / `#134E4A` |
| 已完成 | Success `#059669` |
| 失败 | Destructive `#DC2626` |
| 上传中 | Accent `#D97706` |

### 5.5 聊天消息气泡

- 用户：右侧，背景 `#E8F1F4`，文字 `#134E4A`
- AI：左侧，背景白色，边框 `#E2E8F0`
- 最大宽度：80%
- 圆角：用户 `rounded-2xl rounded-tr-sm`，AI `rounded-2xl rounded-tl-sm`

### 5.6 来源卡片

- 紧凑卡片，显示：类型图标、时间戳、课程名、片段文本。
- 点击可跳转到课程对应时间点。
- hover 显示操作按钮。

---

## 6. 页面布局草案

### 6.1 课程库

- 顶部：页面标题 + 上传按钮
- 主体：课程卡片网格（responsive：1/2/3 列）
- 卡片内容：缩略图、标题、时长、状态徽章、操作按钮（学习/重试/删除）
- 上传：模态框或独立区域，拖拽上传

### 6.2 课程学习

- 左侧 60%：视频播放器
- 右侧 40%：三级总结标签页
  - 大纲：时间戳列表，可跳转
  - 摘要：markdown 渲染
  - 讲义：markdown 渲染
- 底部/侧边：AI 问答快捷入口

### 6.3 知识问答

- 顶部：搜索范围切换（当前课程 / 全部课程）+ 课程选择器
- 中部：对话流
- 底部：输入框 + 发送按钮
- AI 回答下方：可折叠来源卡片列表

---

## 7. 反模式（避免）

- 避免过度使用紫色/粉色渐变（这是通用 AI 工具的 cliché）。
- 避免复杂术语和行业黑话，保持学习场景友好。
- 避免厚重 chrome，减少视觉噪音。
- 避免慢响应无反馈，每个操作都应有 loading/skeleton。
- 避免用 emoji 当图标。

---

## 8. 交付前检查清单

- [ ] 所有颜色变量在 Tailwind 主题中定义
- [ ] 字体正确加载，中文显示清晰
- [ ] 所有可点击元素有 hover/focus 状态
- [ ] 文字对比度通过 WCAG AA
- [ ] 响应式：375px / 768px / 1024px / 1440px
- [ ] 尊重 prefers-reduced-motion
- [ ] 无 emoji 图标（使用 Lucide）
- [ ] 课程状态有清晰视觉标识
- [ ] 视频播放器和问答流都有 loading/skeleton 状态
